"""tai dashboard — one-screen project overview from the docs/ document-driven tree.

Implements SPEC-dashboard-render. Read-only: never writes under docs/ (INV1) and never
raises on a malformed doc — issues degrade to Doc Health warnings (INV2).
"""

from __future__ import annotations

import json as _json
import re
import socket
import threading
import webbrowser
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional
from urllib.parse import parse_qs, unquote, urlparse

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tai.core.context import get_ctx

app = typer.Typer(name="dashboard", help="One-screen project overview from docs/.")
console = Console()
err_console = Console(stderr=True)

def _is_template(name: str) -> bool:
    return name.endswith(".template.md") or name.lower().startswith("_template")
_LINK_FIELDS = ("parent", "children", "related")


# ── docs/ discovery ───────────────────────────────────────────────────────────

def find_docs_dir(start: Optional[Path] = None) -> Optional[Path]:
    """Locate the repo's docs/ dir by walking up from start (cwd). None if absent."""
    here = (start or Path.cwd()).resolve()
    for d in (here, *here.parents):
        candidate = d / "docs"
        if candidate.is_dir():
            return candidate
        if (d / ".git").exists():
            break
    return None


# ── tolerant frontmatter parsing (no YAML dependency; never raises) ─────────────

def parse_frontmatter(text: str) -> dict:
    """Parse leading `---` frontmatter into a dict. Returns {} when absent/malformed.

    Handles `key: scalar`, `key: [a, b]`, and empty `key:`. Tolerant by design (INV2).
    """
    if not text.startswith("---"):
        return {}
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    out: dict = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r"^([A-Za-z0-9_]+):\s*(.*)$", line)
        if not m:
            continue
        key, raw = m.group(1), m.group(2).strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            out[key] = [v.strip() for v in inner.split(",") if v.strip()] if inner else []
        elif raw == "":
            out[key] = None
        else:
            out[key] = raw
    return out


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


# ── data model ──────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Dashboard:
    pipeline: dict
    coverage: dict
    needs_you: list
    recent: list
    doc_health: dict

    def to_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "coverage": self.coverage,
            "needs_you": self.needs_you,
            "recent": self.recent,
            "doc_health": self.doc_health,
        }


# ── collectors (pure, read-only) ──────────────────────────────────────────────

def _md_docs(docs: Path) -> list:
    return [p for p in docs.rglob("*.md") if not _is_template(p.name)]


def collect_pipeline(docs: Path) -> dict:
    """Spec counts grouped by status (R2)."""
    counts = {"draft": 0, "approved": 0, "implemented": 0}
    specs_dir = docs / "specs"
    if specs_dir.is_dir():
        for p in specs_dir.glob("*.md"):
            if _is_template(p.name):
                continue
            status = parse_frontmatter(_read(p)).get("status")
            if status in counts:
                counts[status] += 1
    counts["total"] = sum(counts.values())
    return counts


def collect_coverage(docs: Path) -> dict:
    """COVERED / total from matrix.md Coverage Summary (R4)."""
    text = _read(docs / "matrix.md")
    total = _find_int(text, r"Total Behavior rows:\s*(\d+)") or 0
    covered = _find_int(text, r"COVERED:\s*(\d+)") or 0
    percent = round(100.0 * covered / total, 1) if total else None
    return {"covered": covered, "total": total, "percent": percent}


def _find_int(text: str, pattern: str) -> Optional[int]:
    m = re.search(pattern, text)
    return int(m.group(1)) if m else None


def collect_needs_you(docs: Path) -> list:
    """Open PENDING items from REVIEW.md (R3)."""
    text = _read(docs / "REVIEW.md")
    open_section = text.split("## Resolved", 1)[0]
    items = []
    # blocks start at "### [REVIEW-NNN] title"
    blocks = re.split(r"(?m)^### ", open_section)
    for block in blocks[1:]:
        block_lines = block.splitlines()
        if not block_lines:
            continue
        header = block_lines[0].strip()
        m = re.match(r"\[?(REVIEW-[\w-]+|[\w-]+)\]?\s*(.*)", header)
        rid = m.group(1) if m else "?"
        title = (m.group(2).strip() if m else header) or header
        if re.search(r"(?i)status:\**\s*pending", block):
            items.append({"id": rid, "title": title})
    return items


def collect_recent(docs: Path) -> list:
    """Newest changelog block's entries (R5)."""
    text = _read(docs / "changelog.md")
    out = []
    blocks = re.split(r"(?m)^## ", text)
    for block in blocks[1:]:
        lines = block.splitlines()
        if not lines:
            continue
        version = lines[0].strip()
        entries = [l.strip()[2:].strip() for l in lines[1:] if l.strip().startswith("- ")]
        if entries:
            out.append({"version": version, "entries": entries})
    return out[:2]


def collect_doc_health(docs: Path) -> dict:
    """Missing frontmatter, orphans, broken links across the graph (R7)."""
    missing, broken = [], []
    ids: dict = {}
    parsed: dict = {}
    for p in _md_docs(docs):
        fm = parse_frontmatter(_read(p))
        rel = str(p.relative_to(docs))
        if not fm or "id" not in fm:
            missing.append(rel)
            continue
        parsed[p] = fm
        ids[fm["id"]] = rel

    referenced: set = set()
    for p, fm in parsed.items():
        rel = str(p.relative_to(docs))
        for fld in _LINK_FIELDS:
            val = fm.get(fld)
            targets = val if isinstance(val, list) else ([val] if val else [])
            for t in targets:
                if t in (None, "null"):
                    continue
                if t not in ids:
                    broken.append(f"{rel}: {fld} → '{t}' (no such doc)")
                else:
                    referenced.add(t)

    # Standalone root docs are flat by design (no parent, nothing links in). Only the
    # graph-participating source docs (spec, decision) are expected to be reachable.
    _flat_types = {"review", "prd", "matrix", "changelog", "contributing", "plan", "design", "architecture"}
    orphans = []
    for p, fm in parsed.items():
        doc_id, typ = fm.get("id"), fm.get("type")
        if typ in _flat_types:
            continue
        if fm.get("parent") in (None, "null") and doc_id not in referenced:
            orphans.append(str(p.relative_to(docs)))
    return {"orphans": orphans, "broken_links": broken, "missing_frontmatter": missing}


def build_dashboard(docs: Path) -> Dashboard:
    return Dashboard(
        pipeline=collect_pipeline(docs),
        coverage=collect_coverage(docs),
        needs_you=collect_needs_you(docs),
        recent=collect_recent(docs),
        doc_health=collect_doc_health(docs),
    )


# ── render ────────────────────────────────────────────────────────────────────

def render(d: Dashboard, out: Console) -> None:
    pipe = d.pipeline
    p = Table.grid(padding=(0, 2))
    p.add_row("Specs", f"{pipe['total']} total")
    p.add_row("  draft", str(pipe["draft"]))
    p.add_row("  approved", str(pipe["approved"]))
    p.add_row("  implemented", str(pipe["implemented"]))
    cov = d.coverage
    cov_str = f"{cov['covered']}/{cov['total']}" + (f" ({cov['percent']}%)" if cov["percent"] is not None else " (n/a)")
    p.add_row("Coverage", cov_str)
    out.print(Panel(p, title="Pipeline", border_style="cyan"))

    if d.needs_you:
        t = Table.grid(padding=(0, 2))
        for item in d.needs_you:
            t.add_row(f"[yellow]{item['id']}[/yellow]", item["title"])
        out.print(Panel(t, title=f"Needs you ({len(d.needs_you)})", border_style="yellow"))
    else:
        out.print(Panel("[green]nothing pending[/green]", title="Needs you (0)", border_style="green"))

    if d.recent:
        t = Table.grid(padding=(0, 2))
        for blk in d.recent:
            t.add_row(f"[bold]{blk['version']}[/bold]")
            for e in blk["entries"][:5]:
                t.add_row(f"  • {e}")
        out.print(Panel(t, title="Recent", border_style="blue"))

    h = d.doc_health
    issues = len(h["orphans"]) + len(h["broken_links"]) + len(h["missing_frontmatter"])
    if issues == 0:
        out.print(Panel("[green]healthy — graph intact[/green]", title="Doc Health", border_style="green"))
    else:
        t = Table.grid(padding=(0, 2))
        for o in h["missing_frontmatter"]:
            t.add_row("[red]no frontmatter[/red]", o)
        for o in h["orphans"]:
            t.add_row("[yellow]orphan[/yellow]", o)
        for b in h["broken_links"]:
            t.add_row("[red]broken link[/red]", b)
        out.print(Panel(t, title=f"Doc Health ({issues} issue{'s' if issues != 1 else ''})", border_style="red"))


# ── web server (SPEC-dashboard-serve; ADR 0002 — stdlib http.server) ──────────

_PAGE = """<!doctype html><html><head><meta charset=utf-8>
<title>tai dashboard</title>
<style>
 body{font:14px/1.5 ui-monospace,monospace;background:#ffffff;color:#1f2328;margin:0;padding:24px}
 h1{font-size:18px;color:#0969da;margin:0 0 12px}
 nav button{font:inherit;background:#f6f8fa;color:#1f2328;border:1px solid #d0d7de;border-radius:6px;padding:6px 14px;margin-right:6px;cursor:pointer}
 nav button.on{background:#0969da;border-color:#0969da;color:#fff}
 .grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}
 .card{border:1px solid #d0d7de;border-radius:8px;padding:16px;background:#fff}
 .card h2{font-size:13px;text-transform:uppercase;letter-spacing:.05em;margin:0 0 10px}
 .cyan{color:#0550ae}.yellow{color:#9a6700}.green{color:#1a7f37}.blue{color:#0969da}.red{color:#cf222e}.mag{color:#8250df}
 .row{display:flex;justify-content:space-between;gap:12px;border-bottom:1px solid #d8dee4;padding:4px 0}
 .muted{color:#656d76}.foot{margin-top:16px;color:#656d76;font-size:12px}
 a{color:#0969da;cursor:pointer;text-decoration:none}
 input{font:inherit;background:#fff;color:#1f2328;border:1px solid #d0d7de;border-radius:6px;padding:6px 10px;width:280px}
 button.act{font:inherit;background:#1a7f37;color:#fff;border:0;border-radius:5px;padding:3px 10px;cursor:pointer}
 pre{white-space:pre-wrap;background:#f6f8fa;border:1px solid #d0d7de;border-radius:6px;padding:12px;overflow:auto}
 .pill{font-size:11px;padding:1px 7px;border-radius:10px;border:1px solid #d0d7de;white-space:nowrap}
 .dlist{border-collapse:collapse;width:100%}
 .dlist th{text-align:left;font-weight:normal;color:#656d76;font-size:12px;padding:4px 10px;border-bottom:1px solid #d0d7de}
 .dlist td{padding:5px 10px;border-bottom:1px solid #eaeef2;vertical-align:top}
 .dlist td:first-child{white-space:nowrap}.dlist td:nth-child(2){white-space:nowrap}
 .md h1,.md h2,.md h3{border:0;text-transform:none;letter-spacing:0;color:#1f2328;margin:14px 0 6px}
 .md h1{font-size:20px}.md h2{font-size:16px}.md h3{font-size:14px}
 .md table{border-collapse:collapse;margin:8px 0;width:100%}
 .md th,.md td{border:1px solid #d0d7de;padding:5px 9px;text-align:left;vertical-align:top}
 .md th{background:#f6f8fa}
 .md blockquote{border-left:3px solid #d0d7de;margin:8px 0;padding:2px 12px;color:#656d76}
 .md code{background:#f6f8fa;padding:1px 5px;border-radius:4px}
 .md ul,.md ol{margin:6px 0;padding-left:22px}
 .md hr{border:0;border-top:1px solid #d8dee4;margin:14px 0}
</style>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head><body>
<h1>tai dashboard <span class=muted id=ts></span></h1>
<nav><button data-t=overview class=on>Overview</button><button data-t=specs>Specs</button><button data-t=decisions>Decisions</button><button data-t=gates>Gates</button><button data-t=architecture>Architecture</button></nav>
<div id=app style=margin-top:16px></div>
<div class=foot>localhost · reads live · gate actions write + commit</div>
<script>
try{mermaid&&mermaid.initialize({startOnLoad:false,theme:'default',securityLevel:'strict'});}catch(e){}
const app=document.getElementById('app');let tab='overview';
const esc=s=>(s||'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const j=async(u,o)=>(await fetch(u,o)).json();
// compact, escape-first markdown → HTML (no deps; XSS-safe: escape then add known tags).
function mdRender(src){
 const blk=[];
 src=(src||'').replace(/```(\\w*)\\n?([\\s\\S]*?)```/g,(m,lang,code)=>{blk.push([lang,code.replace(/\\n+$/,'')]);return '@@B'+(blk.length-1)+'@@';});
 const inl=t=>esc(t).replace(/`([^`]+)`/g,'<code>$1</code>').replace(/\\*\\*([^*]+)\\*\\*/g,'<b>$1</b>').replace(/\\*([^*]+)\\*/g,'<i>$1</i>').replace(/\\[([^\\]]+)\\]\\(([^)\\s]+)\\)/g,(m,txt,url)=>/^(https?:|mailto:|#|\\/)/i.test(url)?`<a href="${url}">${txt}</a>`:m);
 const L=src.split('\\n');let h='',i=0;
 while(i<L.length){const s=L[i];let m;
  if(m=s.match(/^@@B(\\d+)@@$/)){const b=blk[+m[1]];if(b){const[lang,code]=b;h+=(lang==='mermaid'&&window.mermaid)?`<div class=mermaid>${esc(code)}</div>`:`<pre>${esc(code)}</pre>`;}i++;continue;}
  if(m=s.match(/^(#{1,6})\\s+(.*)/)){const n=m[1].length;h+=`<h${n}>${inl(m[2])}</h${n}>`;i++;continue;}
  if(/^(---|\\*\\*\\*)\\s*$/.test(s)){h+='<hr>';i++;continue;}
  if(/^>\\s?/.test(s)){const q=[];while(i<L.length&&/^>\\s?/.test(L[i])){q.push(inl(L[i].replace(/^>\\s?/,'')));i++;}h+=`<blockquote>${q.join('<br>')}</blockquote>`;continue;}
  if(/^\\s*[-*]\\s/.test(s)){const it=[];while(i<L.length&&/^\\s*[-*]\\s/.test(L[i])){it.push(`<li>${inl(L[i].replace(/^\\s*[-*]\\s/,''))}</li>`);i++;}h+=`<ul>${it.join('')}</ul>`;continue;}
  if(/^\\s*\\d+\\.\\s/.test(s)){const it=[];while(i<L.length&&/^\\s*\\d+\\.\\s/.test(L[i])){it.push(`<li>${inl(L[i].replace(/^\\s*\\d+\\.\\s/,''))}</li>`);i++;}h+=`<ol>${it.join('')}</ol>`;continue;}
  if(/^\\|.*\\|/.test(s)){const rs=[];while(i<L.length&&/^\\|/.test(L[i])){rs.push(L[i]);i++;}
   const cells=r=>r.replace(/^\\||\\|$/g,'').split('|').map(c=>c.trim());let th='',tb='';
   rs.forEach((r,ri)=>{if(/^\\|[\\s:|-]+\\|?$/.test(r))return;const c=cells(r);
    if(ri===0)th=`<tr>${c.map(x=>`<th>${inl(x)}</th>`).join('')}</tr>`;else tb+=`<tr>${c.map(x=>`<td>${inl(x)}</td>`).join('')}</tr>`;});
   h+=`<table>${th}${tb}</table>`;continue;}
  if(s.trim()===''){i++;continue;}
  const p=[];while(i<L.length&&L[i].trim()!==''&&!/^(#|>|\\s*[-*]\\s|\\s*\\d+\\.\\s|\\||@@B)/.test(L[i])){p.push(inl(L[i]));i++;}
  if(!p.length){p.push(inl(s));i++;}  // line fell through all branches → consume as text (guarantee progress)
  h+=`<p>${p.join(' ')}</p>`;
 }
 return h;
}
function setTab(t){tab=t;document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('on',b.dataset.t===t));draw();}
document.querySelectorAll('nav button').forEach(b=>b.onclick=()=>setTab(b.dataset.t));

function card(title,cls,body){return `<div class=card><h2 class="${cls}">${title}</h2>${body}</div>`;}
function rows(p){return p.map(([k,v])=>`<div class=row><span>${k}</span><span>${v}</span></div>`).join('');}

async function drawOverview(){
 const d=await j('/api/dashboard.json');const p=d.pipeline,c=d.coverage;
 const cov=c.total?`${c.covered}/${c.total} (${c.percent}%)`:'n/a';
 const h=d.doc_health,iss=h.orphans.length+h.broken_links.length+h.missing_frontmatter.length;
 app.className='grid';
 app.innerHTML=
  card('Pipeline','cyan',rows([['Specs',p.total],['draft',p.draft],['approved',p.approved],['implemented',p.implemented],['Coverage',cov]]))+
  (d.needs_you.length?card(`Needs you (${d.needs_you.length})`,'yellow',d.needs_you.map(i=>`<div class=row><span class=yellow>${i.id}</span><span>${esc(i.title)}</span></div>`).join('')):card('Needs you (0)','green','<span class=green>nothing pending</span>'))+
  (d.recent.length?card('Recent','blue',d.recent.map(b=>`<div class=row><b>${esc(b.version)}</b></div>`+b.entries.slice(0,5).map(e=>`<div class=row><span class=muted>• ${esc(e)}</span></div>`).join('')).join('')):card('Recent','blue','<span class=muted>none</span>'))+
  (iss===0?card('Doc Health','green','<span class=green>healthy — graph intact</span>'):card(`Doc Health (${iss})`,'red',[].concat(h.missing_frontmatter.map(x=>['no frontmatter',x]),h.orphans.map(x=>['orphan',x]),h.broken_links.map(x=>['broken link',x])).map(([k,v])=>`<div class=row><span class=red>${k}</span><span>${esc(v)}</span></div>`).join('')));
}
async function docList(type,placeholder){
 app.className='';
 app.innerHTML=`<input id=q placeholder="${placeholder}"><div id=list style=margin-top:12px></div><div id=detail style=margin-top:16px></div>`;
 const q=document.getElementById('q'),list=document.getElementById('list');
 async function load(){
  const rows=(q.value?await j('/api/search?q='+encodeURIComponent(q.value)):await j('/api/docs?type='+type)).filter(r=>r.type===type);
  list.innerHTML=rows.length?`<table class=dlist><thead><tr><th>id</th><th>status</th><th>title</th></tr></thead><tbody>`+rows.map(r=>`<tr><td><a class=doclink data-id="${esc(r.id)}">${esc(r.id)}</a></td><td><span class="pill">${esc(r.status)}</span></td><td class=muted>${esc(r.title)}</td></tr>`).join('')+`</tbody></table>`:'<span class=muted>none</span>';
  list.querySelectorAll('.doclink').forEach(a=>a.onclick=()=>showDoc(a.dataset.id));}
 q.oninput=load;await load();
}
const drawSpecs=()=>docList('spec','search specs…');
const drawDecisions=()=>docList('decision','search decisions…');
async function drawArchitecture(){app.className='';app.innerHTML='<div id=detail></div>';await showDoc('architecture');}
async function showDoc(id){
 const d=await j('/api/doc/'+encodeURIComponent(id));const det=document.getElementById('detail');
 if(!d||!d.frontmatter){det.innerHTML=card(esc(id),'red','not found — no such doc');return;}
 const meta=Object.entries(d.frontmatter).filter(([k])=>['id','type','status','approved_at'].includes(k)).map(([k,v])=>`<span class=pill>${k}: ${esc(''+v)}</span>`).join(' ');
 det.innerHTML=card(esc(id),'cyan',`<div>${meta}</div><div class=md style=margin-top:10px>${mdRender(d.body)}</div>`);
 if(window.mermaid){try{await mermaid.run({nodes:det.querySelectorAll('.mermaid')});}catch(e){}}
}
async function drawGates(){
 app.className='';const g=await j('/api/gates');
 const groups=[['gate_a','GATE A — PRD','mag'],['gate_b','GATE B — ADR','blue'],['gate_c','GATE C — spec','yellow'],['review','REVIEW','red']];
 const total=groups.reduce((n,[k])=>n+g[k].length,0);
 if(!total){app.className='grid';app.innerHTML=card('Gates','green','<span class=green>all clear — no gates open</span>');return;}
 app.innerHTML=groups.filter(([k])=>g[k].length).map(([k,label,cls])=>card(`${label} (${g[k].length})`,cls,
   g[k].map(it=>`<div class=row><span class=${cls}>${esc(it.id)}</span><span>${esc(it.title)}</span>`+
     (it.action==='sign'?'<span class=muted>sign (manual)</span>':`<button class=act data-action="${esc(it.action)}" data-id="${esc(it.id)}">${esc(it.action)}</button>`)+`</div>`).join(''))).join('');
 app.querySelectorAll('button.act').forEach(b=>b.onclick=()=>act(b.dataset.action,b.dataset.id));
}
async function act(action,id){
 if(!confirm(`${action} ${id}? This writes to the doc and commits.`))return;
 const r=await j('/api/gate/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id})});
 if(!r.ok)alert('Refused: '+r.message);
 drawGates();
}
function draw(){({overview:drawOverview,specs:drawSpecs,decisions:drawDecisions,gates:drawGates,architecture:drawArchitecture}[tab])();document.getElementById('ts').textContent=new Date().toLocaleTimeString();}
draw();
</script></body></html>"""


def doc_detail(docs: Path, doc_id: str) -> Optional[dict]:
    """One doc: {id, frontmatter, body, mermaid:[blocks]}. None if absent."""
    path = find_doc_by_id(docs, doc_id)
    if path is None:
        return None
    text = _read(path)
    body = _doc_body(text)
    mermaid = re.findall(r"```mermaid\s*\n(.*?)```", body, re.S)
    return {"id": doc_id, "frontmatter": parse_frontmatter(text), "body": body, "mermaid": mermaid}


_GATE_LOCK = threading.Lock()  # serialize web gate writes (one git index at a time)


def _make_handler(docs: Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):  # silence default stderr logging
            pass

        def _host_ok(self) -> bool:
            # DNS-rebinding / cross-origin guard: only serve requests whose Host is loopback.
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
            return host in ("127.0.0.1", "localhost", "::1", "")

        def do_GET(self):  # noqa: N802
            if not self._host_ok():
                self._send(403, "text/plain", b"forbidden host")
                return
            u = urlparse(self.path)
            path, qs = u.path, parse_qs(u.query)
            if path == "/api/dashboard.json":
                self._json(build_dashboard(docs).to_dict())
            elif path == "/api/docs":
                rows = collect_list(docs, (qs.get("type", ["all"])[0]), (qs.get("status", [None])[0]))
                self._json([r.to_dict() for r in rows])
            elif path == "/api/search":
                rows = collect_search(docs, qs.get("q", [""])[0])
                self._json([r.to_dict() for r in rows])
            elif path == "/api/gates":
                self._json(collect_gates(docs))
            elif path.startswith("/api/doc/"):
                detail = doc_detail(docs, unquote(path[len("/api/doc/"):]))
                self._json(detail) if detail else self._send(404, "application/json", b'{"error":"not found"}')
            elif path in ("/", "/index.html"):
                self._send(200, "text/html; charset=utf-8", _PAGE.encode())
            else:
                self._send(404, "text/plain", b"not found")

        def do_POST(self):  # noqa: N802
            if not self._host_ok():
                self._send(403, "text/plain", b"forbidden host")
                return
            # Writes are loopback-only by design: if the server was bound to a non-loopback
            # host (--host 0.0.0.0), refuse all gate writes regardless of Host/Origin.
            if self.server.server_address[0] not in ("127.0.0.1", "::1", "localhost"):
                self._send(403, "text/plain", b"gate writes are localhost-only")
                return
            path = urlparse(self.path).path
            actions = {"/api/gate/approve": "approve", "/api/gate/accept": "accept",
                       "/api/gate/resolve": "resolve"}
            if path not in actions:
                self._send(404, "text/plain", b"not found")
                return
            # CSRF guard: require JSON content-type (forces a CORS preflight for cross-origin,
            # which we don't answer → blocked); reject a present non-loopback Origin outright.
            if "application/json" not in (self.headers.get("Content-Type") or ""):
                self._send(415, "text/plain", b"application/json required")
                return
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).hostname not in ("127.0.0.1", "localhost", "::1"):
                self._send(403, "text/plain", b"forbidden origin")
                return
            try:
                length = int(self.headers.get("Content-Length", 0) or 0)
                body = _json.loads(self.rfile.read(length) or b"{}")
                doc_id = body["id"]
            except Exception:
                self._json({"ok": False, "message": "missing id"})  # 200 + ok:false (client reads `ok`)
                return
            from tai.commands import gate  # lazy import — avoids dashboard↔gate cycle
            fn = {"approve": gate.gate_approve, "accept": gate.gate_accept, "resolve": gate.gate_resolve}[actions[path]]
            with _GATE_LOCK:  # serialize concurrent writes/commits
                ok, message = fn(docs, doc_id)
            self._json({"ok": ok, "message": message})

        def _json(self, obj, code: int = 200):
            self._send(code, "application/json", _json.dumps(obj).encode())

        def _send(self, code: int, ctype: str, body: bytes):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def build_server(docs: Path, host: str, port: int) -> ThreadingHTTPServer:
    """Bind a localhost web server serving the dashboard. Raises OSError if port in use."""
    return ThreadingHTTPServer((host, port), _make_handler(docs))


def serve(docs: Path, host: str, port: Optional[int], open_browser: bool, out: Console) -> None:
    bind_port = port if port is not None else find_free_port()
    try:
        httpd = build_server(docs, host, bind_port)
    except OSError as exc:
        err_console.print(f"[bold red]Cannot bind {host}:{bind_port}[/bold red] — {exc}")
        err_console.print("[dim]Hint: the port may be in use; pass a free --port.[/dim]")
        raise typer.Exit(1)
    url = f"http://{host}:{bind_port}/"
    out.print(f"[green]tai dashboard serving at[/green] [bold]{url}[/bold]  [dim](Ctrl-C to stop)[/dim]")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        out.print("\n[dim]shutting down…[/dim]")
    finally:
        httpd.shutdown()
        httpd.server_close()


# ── doc query (SPEC-docs-query) + gates (SPEC-gates-view) ─────────────────────

@dataclass(frozen=True)
class DocRow:
    id: str
    type: str
    status: str
    title: str
    path: str

    def to_dict(self) -> dict:
        return {"id": self.id, "type": self.type, "status": self.status,
                "title": self.title, "path": self.path}


def _first_heading(text: str) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def _doc_body(text: str) -> str:
    """Strip leading frontmatter, return the markdown body (banner line, if any, kept)."""
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]
    return text.lstrip("\n")


def _doc_row(path: Path, docs: Path) -> Optional[DocRow]:
    fm = parse_frontmatter(_read(path))
    if not fm or "id" not in fm:
        return None
    body = _doc_body(_read(path))
    return DocRow(
        id=fm["id"], type=fm.get("type") or "?", status=fm.get("status") or "—",
        title=_first_heading(body) or fm["id"], path=str(path.relative_to(docs)),
    )


def _doc_rows(docs: Path) -> list:
    rows = []
    for p in _md_docs(docs):
        row = _doc_row(p, docs)
        if row:
            rows.append(row)
    return rows


def collect_list(docs: Path, type_filter: str = "all", status_filter: Optional[str] = None) -> list:
    # "all" = all specs + ADRs (the browsable contract docs), per SPEC-docs-query R1 —
    # not every doc in the tree (prd/architecture/matrix are not listed here).
    rows = [r for r in _doc_rows(docs) if r.type in ("spec", "decision")]
    if type_filter and type_filter != "all":
        rows = [r for r in rows if r.type == type_filter]
    if status_filter:
        rows = [r for r in rows if r.status == status_filter]
    return sorted(rows, key=lambda r: (r.type, r.id))


def collect_search(docs: Path, query: str) -> list:
    q = query.lower()
    hits = []
    for p in _md_docs(docs):
        row = _doc_row(p, docs)
        if not row or row.type not in ("spec", "decision"):  # specs + ADRs only, matches `list`
            continue
        in_id, in_title = q in row.id.lower(), q in row.title.lower()
        in_body = q in _doc_body(_read(p)).lower()  # body only — not frontmatter
        if in_id or in_title or in_body:
            rank = 0 if in_id else (1 if in_title else 2)
            hits.append((rank, row))
    return [r for _, r in sorted(hits, key=lambda t: (t[0], t[1].id))]


def find_doc_by_id(docs: Path, doc_id: str) -> Optional[Path]:
    for p in _md_docs(docs):
        if parse_frontmatter(_read(p)).get("id") == doc_id:
            return p
    return None


def collect_gates(docs: Path) -> dict:
    gate_a, gate_b, gate_c = [], [], []
    prd = docs / "prd.md"
    if prd.exists():
        st = parse_frontmatter(_read(prd)).get("status")
        if st not in ("approved", "shipped"):
            gate_a.append({"id": "prd", "title": _first_heading(_doc_body(_read(prd))) or "prd",
                           "action": "sign"})
    dec = docs / "decisions"
    if dec.is_dir():
        for p in sorted(dec.glob("*.md")):
            if _is_template(p.name):
                continue
            r = _doc_row(p, docs)
            if r and r.status == "proposed":
                gate_b.append({"id": r.id, "title": r.title, "action": "accept"})
    specs = docs / "specs"
    if specs.is_dir():
        for p in sorted(specs.glob("*.md")):
            if _is_template(p.name):
                continue
            r = _doc_row(p, docs)
            if r and r.status == "draft":
                gate_c.append({"id": r.id, "title": r.title, "action": "approve"})
    review = [{**it, "action": "resolve"} for it in collect_needs_you(docs)]
    return {"gate_a": gate_a, "gate_b": gate_b, "gate_c": gate_c, "review": review}


def _require_docs() -> Path:
    docs = find_docs_dir()
    if docs is None:
        err_console.print("[bold red]No docs/ found.[/bold red]")
        err_console.print("[dim]Hint: run /docs-init (or tai setup) to bootstrap the docs tree.[/dim]")
        raise typer.Exit(1)
    return docs


def _print_rows(rows: list, out: Console, title: str) -> None:
    if not rows:
        out.print(f"[dim]{title}: none[/dim]")
        return
    t = Table(title=title, title_style="bold", header_style="dim")
    t.add_column("id"); t.add_column("type"); t.add_column("status"); t.add_column("title")
    for r in rows:
        sc = {"approved": "green", "implemented": "cyan", "draft": "yellow",
              "proposed": "yellow", "accepted": "green"}.get(r.status, "white")
        t.add_row(r.id, r.type, f"[{sc}]{r.status}[/{sc}]", r.title)
    out.print(t)


# ── command ───────────────────────────────────────────────────────────────────

@app.callback(invoke_without_command=True)
def dashboard(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Emit JSON instead of the rendered view."),
    serve_web: bool = typer.Option(False, "--serve", help="Serve a live web view (localhost)."),
    port: Optional[int] = typer.Option(None, "--port", help="Port for --serve (default: auto-pick free)."),
    host: str = typer.Option("127.0.0.1", "--host", help="Bind host for --serve (default loopback)."),
    no_open: bool = typer.Option(False, "--no-open", help="Don't auto-open the browser with --serve."),
) -> None:
    """Render a one-screen overview of project state from docs/ (terminal or --serve web)."""
    if ctx.invoked_subcommand is not None:
        return  # a subcommand (list/search/show/gates) handles it

    docs = find_docs_dir()
    if docs is None:
        err_console.print("[bold red]No docs/ found.[/bold red]")
        err_console.print("[dim]Hint: run /docs-init (or tai setup) to bootstrap the docs tree.[/dim]")
        raise typer.Exit(1)

    if serve_web:
        if host != "127.0.0.1" and not host.startswith("127."):
            err_console.print(f"[yellow]Warning:[/yellow] binding non-loopback host {host} — the dashboard has no auth.")
        serve(docs, host, port, open_browser=not no_open, out=console)
        return

    as_json = json_output
    try:
        app_ctx = get_ctx(ctx)
        as_json = as_json or app_ctx.json_output
    except Exception:
        pass

    data = build_dashboard(docs)
    if as_json:
        console.print_json(_json.dumps(data.to_dict()))
    else:
        render(data, console)


@app.command("list")
def list_docs(
    type_filter: str = typer.Option("all", "--type", help="spec | decision | all"),
    status_filter: Optional[str] = typer.Option(None, "--status", help="draft|approved|implemented|proposed|accepted"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """List specs + ADRs (filter by --type / --status)."""
    docs = _require_docs()
    rows = collect_list(docs, type_filter, status_filter)
    if json_output:
        console.print_json(_json.dumps([r.to_dict() for r in rows]))
    else:
        _print_rows(rows, console, f"Docs ({len(rows)})")


@app.command("search")
def search_docs(
    query: str = typer.Argument(..., help="substring to match in id / title / body"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Search specs + ADRs by id / title / body (case-insensitive)."""
    docs = _require_docs()
    rows = collect_search(docs, query)
    if json_output:
        console.print_json(_json.dumps([r.to_dict() for r in rows]))
    else:
        _print_rows(rows, console, f"Search '{query}' ({len(rows)})")


@app.command("show")
def show_doc(
    doc_id: str = typer.Argument(..., help="doc id, e.g. SPEC-dashboard-render"),
    json_output: bool = typer.Option(False, "--json"),
) -> None:
    """Show one doc: frontmatter summary + body (mermaid shown raw)."""
    docs = _require_docs()
    path = find_doc_by_id(docs, doc_id)
    if path is None:
        err_console.print(f"[bold red]No doc with id '{doc_id}'.[/bold red]")
        ids = [r.id for r in _doc_rows(docs)]
        near = [i for i in ids if doc_id.lower() in i.lower()][:3]
        if near:
            err_console.print(f"[dim]Did you mean: {', '.join(near)}?[/dim]")
        raise typer.Exit(1)
    text = _read(path)
    fm, body = parse_frontmatter(text), _doc_body(text)
    if json_output:
        console.print_json(_json.dumps({"frontmatter": fm, "body": body}))
    else:
        meta = "  ".join(f"[dim]{k}:[/dim] {v}" for k, v in fm.items() if k in ("id", "type", "status", "approved_at"))
        console.print(Panel(meta, title=str(path.relative_to(docs)), border_style="cyan"))
        console.print(body)


@app.command("gates")
def gates(json_output: bool = typer.Option(False, "--json")) -> None:
    """Show the pending-gates board: what needs a human, grouped by gate."""
    docs = _require_docs()
    g = collect_gates(docs)
    if json_output:
        console.print_json(_json.dumps(g))
        return
    total = sum(len(g[k]) for k in g)
    if total == 0:
        console.print(Panel("[green]all clear — no gates open[/green]", title="Gates", border_style="green"))
        return
    labels = [("gate_a", "GATE A — PRD sign", "magenta"), ("gate_b", "GATE B — ADR accept", "blue"),
              ("gate_c", "GATE C — spec approve", "yellow"), ("review", "REVIEW — resolve", "red")]
    for key, label, color in labels:
        items = g[key]
        if not items:
            continue
        t = Table.grid(padding=(0, 2))
        for it in items:
            t.add_row(f"[{color}]{it['id']}[/{color}]", it["title"], f"[dim]→ {it['action']}[/dim]")
        console.print(Panel(t, title=f"{label} ({len(items)})", border_style=color))
