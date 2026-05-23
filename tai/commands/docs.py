"""tai docs — browse project documentation."""

from __future__ import annotations

import json
import re
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from socketserver import ThreadingMixIn
from pathlib import Path

import typer
from rich.console import Console

from tai.core.errors import TaiError, handle_error

app = typer.Typer(name="docs", help="Project documentation tools.", no_args_is_help=True)
console = Console()

DOCS_DIR_NAME = "docs"
ASSETS_DIR = "_assets"

# Bundled assets shipped with tai
_BUNDLED_ASSETS = Path(__file__).resolve().parent.parent / "data" / "docs" / "assets"


# ── Validation schemas ──────────────────────────────────────────────────────

SCHEMAS: dict[str, dict] = {
    "intent": {
        "required_sections": ["context", "problem", "solution", "success-criteria"],
        "required_meta": ["date"],
    },
    "decision": {
        "required_sections": ["context", "decision", "consequences"],
        "required_meta": ["date", "status"],
    },
    "design": {
        "required_sections": ["overview", "components"],
        "required_meta": ["date"],
    },
    "spec": {
        "required_sections": ["problem", "requirements", "acceptance-criteria"],
        "required_meta": ["date", "status"],
    },
    "guide": {
        "required_sections": ["overview"],
        "required_meta": ["date"],
    },
    "plan": {
        "required_sections": ["phases"],
        "required_meta": ["date"],
    },
    "review": {
        "required_sections": ["findings"],
        "required_meta": ["date"],
    },
    "trace": {
        "required_sections": [],
        "required_meta": ["date"],
    },
    "changelog": {
        "required_sections": [],
        "required_meta": ["date"],
    },
}


def find_docs_root() -> Path:
    """Walk up from cwd to find the docs/ directory."""
    cwd = Path.cwd()
    # Check for docs/ in cwd or any parent up to git root
    for parent in [cwd, *cwd.parents]:
        candidate = parent / DOCS_DIR_NAME
        if candidate.is_dir():
            return candidate
        if (parent / ".git").exists():
            return candidate  # return expected location even if missing
    return cwd / DOCS_DIR_NAME


def discover_docs(docs_root: Path) -> list[dict]:
    """Find all .html docs under docs_root, extract title and metadata."""
    docs = []
    if not docs_root.is_dir():
        return docs

    for html_file in sorted(docs_root.rglob("*.html")):
        rel = html_file.relative_to(docs_root)
        if rel.parts[0] == ASSETS_DIR:
            continue

        text = html_file.read_text(encoding="utf-8", errors="replace")
        title = _extract_title(text) or rel.stem
        doc_type = _extract_meta(text, "doc-type") or ""

        docs.append({
            "path": str(rel),
            "title": title,
            "type": doc_type,
        })
    return docs


def validate_file(path: Path, docs_root: Path) -> list[str]:
    """Validate a single HTML doc. Returns list of issues."""
    text = path.read_text(encoding="utf-8", errors="replace")
    issues: list[str] = []

    title = _extract_title(text)
    doc_type = _extract_meta(text, "doc-type")
    doc_date = _extract_meta(text, "doc-date")

    if not title or title == "Untitled":
        issues.append("Missing <title>")
    if not doc_type:
        issues.append('Missing <meta name="doc-type">')
    if not doc_date:
        issues.append('Missing <meta name="doc-date">')

    schema = SCHEMAS.get(doc_type or "")
    if schema:
        for section in schema["required_sections"]:
            if f'data-section="{section}"' not in text:
                issues.append(f"Missing section: {section}")
        for meta_field in schema["required_meta"]:
            if not _extract_meta(text, f"doc-{meta_field}"):
                issues.append(f"Missing meta: doc-{meta_field}")
    elif doc_type:
        issues.append(f"Unknown doc-type: {doc_type}")

    # Check internal links resolve
    for href in _extract_internal_links(text):
        target = (path.parent / href).resolve()
        if not target.exists():
            issues.append(f"Broken link: {href}")

    return issues


def validate_all(docs_root: Path) -> dict[str, list[str]]:
    """Validate every HTML doc under docs_root. Returns {path: [issues]}."""
    results: dict[str, list[str]] = {}
    if not docs_root.is_dir():
        return results

    for html_file in sorted(docs_root.rglob("*.html")):
        rel = html_file.relative_to(docs_root)
        if rel.parts[0] == ASSETS_DIR:
            continue
        file_issues = validate_file(html_file, docs_root)
        if file_issues:
            results[str(rel)] = file_issues
    return results


# ── HTML parsing helpers (no external deps) ─────────────────────────────────

_RE_TITLE = re.compile(r"<title[^>]*>([^<]+)</title>", re.IGNORECASE)
_RE_META = re.compile(r'<meta\s+name="([^"]+)"\s+content="([^"]*)"', re.IGNORECASE)
_RE_HREF = re.compile(r'<a\s[^>]*href="([^"#][^"]*)"', re.IGNORECASE)


def _extract_title(html: str) -> str | None:
    m = _RE_TITLE.search(html)
    return m.group(1).strip() if m else None


def _extract_meta(html: str, name: str) -> str | None:
    for m in _RE_META.finditer(html):
        if m.group(1) == name:
            return m.group(2)
    return None


def _extract_internal_links(html: str) -> list[str]:
    links = []
    for m in _RE_HREF.finditer(html):
        href = m.group(1)
        if href.startswith(("http://", "https://", "mailto:", "/")):
            continue
        links.append(href)
    return links


# ── SSE file watcher ────────────────────────────────────────────────────────

class FileWatcher:
    """Poll-based watcher that tracks mtime of all files under a directory."""

    def __init__(self, root: Path, interval: float = 1.0):
        self._root = root
        self._interval = interval
        self._subscribers: list = []
        self._running = False
        self._snapshot: dict[str, float] = {}

    def subscribe(self, callback):
        self._subscribers.append(callback)

    def _scan(self) -> dict[str, float]:
        snap: dict[str, float] = {}
        if not self._root.is_dir():
            return snap
        for p in self._root.rglob("*"):
            if p.is_file():
                try:
                    snap[str(p)] = p.stat().st_mtime
                except OSError:
                    pass
        return snap

    def _notify(self):
        for cb in self._subscribers:
            try:
                cb()
            except Exception:
                pass

    def run(self):
        self._running = True
        self._snapshot = self._scan()
        while self._running:
            time.sleep(self._interval)
            new = self._scan()
            if new != self._snapshot:
                self._snapshot = new
                self._notify()

    def stop(self):
        self._running = False


# ── HTTP server ─────────────────────────────────────────────────────────────

class DocsHandler(SimpleHTTPRequestHandler):
    """Serves docs/ with API endpoints for navigation and SSE."""

    docs_root: Path
    watcher: FileWatcher
    _sse_clients: list  # class-level, shared across instances

    def do_GET(self):
        if self.path == "/_api/docs":
            return self._api_docs()
        if self.path.startswith("/_api/schema/"):
            return self._api_schema()
        if self.path == "/_events":
            return self._sse()
        if self.path == "/":
            # If index.html exists, serve it; otherwise generate index
            index = self.docs_root / "index.html"
            if index.is_file():
                return super().do_GET()
            return self._auto_index()

        return super().do_GET()

    def _api_docs(self):
        docs = discover_docs(self.docs_root)
        body = json.dumps(docs).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _api_schema(self):
        doc_type = self.path.split("/")[-1]
        schema = SCHEMAS.get(doc_type, {})
        body = json.dumps(schema).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _sse(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()

        event = threading.Event()
        self.watcher.subscribe(event.set)

        try:
            while True:
                event.wait(timeout=30)
                if event.is_set():
                    self.wfile.write(b'data: {"type":"reload"}\n\n')
                    self.wfile.flush()
                    event.clear()
                else:
                    # keepalive
                    self.wfile.write(b': keepalive\n\n')
                    self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _auto_index(self):
        docs = discover_docs(self.docs_root)
        groups: dict[str, list] = {}
        for doc in docs:
            parts = doc["path"].split("/")
            group = "/".join(parts[:-1]) if len(parts) > 1 else "root"
            groups.setdefault(group, []).append(doc)

        items_html = []
        for group in sorted(groups):
            if group != "root":
                items_html.append(f'<h3>{group}</h3>')
            items_html.append('<ul>')
            for doc in sorted(groups[group], key=lambda d: d["title"]):
                doc_type = ""
                if doc["type"]:
                    doc_type = f' <code>{doc["type"]}</code>'
                items_html.append(
                    f'<li><a href="/{doc["path"]}">{doc["title"]}</a>{doc_type}</li>'
                )
            items_html.append('</ul>')

        body = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="doc-type" content="trace">
  <meta name="doc-date" content="{time.strftime('%Y-%m-%d')}">
  <title>Documentation Index</title>
  <link rel="stylesheet" href="/_assets/style.css">
</head>
<body>
  <article>
    <h1>Documentation</h1>
    {''.join(items_html) if items_html else '<p>No documents found. Create <code>.html</code> files in <code>docs/</code>.</p>'}
  </article>
  <script src="/_assets/docs.js"></script>
</body>
</html>"""
        encoded = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def translate_path(self, path: str) -> str:
        """Route /_assets/ to bundled assets, everything else to docs_root."""
        if path.startswith("/_assets/"):
            rel = path[len("/_assets/"):]
            # Prefer project's docs/_assets/ first, fall back to bundled
            project_asset = self.docs_root / ASSETS_DIR / rel
            if project_asset.is_file():
                return str(project_asset)
            bundled = _BUNDLED_ASSETS / rel
            return str(bundled)

        # Strip leading slash, resolve relative to docs_root
        clean = path.lstrip("/")
        if not clean:
            clean = "index.html"
        return str(self.docs_root / clean)

    def log_message(self, format, *args):
        """Suppress default logs — we log through rich."""
        pass


# ── CLI commands ────────────────────────────────────────────────────────────

@app.command()
def serve(
    port: int = typer.Option(3333, help="Port to serve on."),
    docs_dir: str = typer.Option("", help="Path to docs directory (auto-detected if empty)."),
) -> None:
    """Start a local server to browse project docs with hot reload."""
    docs_root = Path(docs_dir) if docs_dir else find_docs_root()

    if not docs_root.is_dir():
        console.print(f"[yellow]docs/ not found at {docs_root}[/yellow]")
        console.print("Create docs/ or run the [bold]docs-init[/bold] skill.")
        raise typer.Exit(1)

    # Ensure _assets/ exists in the project docs
    project_assets = docs_root / ASSETS_DIR
    if not project_assets.is_dir():
        console.print(f"[dim]Copying shared assets to {project_assets}[/dim]")
        _copy_assets(project_assets)

    watcher = FileWatcher(docs_root)
    watcher_thread = threading.Thread(target=watcher.run, daemon=True)
    watcher_thread.start()

    handler_class = type(
        "Handler",
        (DocsHandler,),
        {"docs_root": docs_root, "watcher": watcher},
    )

    class ThreadedServer(ThreadingMixIn, HTTPServer):
        daemon_threads = True

    server = ThreadedServer(("127.0.0.1", port), handler_class)
    console.print(f"[bold green]Serving docs[/bold green] at http://localhost:{port}")
    console.print(f"[dim]Root: {docs_root}[/dim]")
    console.print("[dim]Hot reload active. Ctrl+C to stop.[/dim]")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        watcher.stop()
        server.shutdown()
        console.print("\n[dim]Stopped.[/dim]")



def _copy_assets(target: Path) -> None:
    """Copy bundled CSS/JS assets to the project's docs/_assets/."""
    import shutil
    if target.is_dir():
        shutil.rmtree(target)
    shutil.copytree(_BUNDLED_ASSETS, target)
