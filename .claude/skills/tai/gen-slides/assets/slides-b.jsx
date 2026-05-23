/* =========================================================
   Slide layouts — Part B: split, table, timeline, chart, list
   ========================================================= */

/* ---------- 7. SPLIT ---------- */
function SlideSplit({ eyebrow, titleJp, leftLabel, rightLabel, leftItems, rightItems, leftDark = false, rightDark = true, num, total }) {
  const lItems = leftItems || [
    "Point describing current state 1",
    "Point describing current state 2",
    "Point describing current state 3",
    "Point describing current state 4",
  ];
  const rItems = rightItems || [
    "Point describing improved state 1",
    "Point describing improved state 2",
    "Point describing improved state 3",
    "Point describing improved state 4",
  ];

  function renderColumn(items, label, labelTag, isDark) {
    const bg = isDark ? "card-dark" : "";
    return (
      <div className={`col ${bg}`} style={{
        padding: 44, gap: 24,
        ...(isDark ? {} : { background: "#fff", borderRadius: 16, border: "1px solid var(--border)" }),
      }}>
        <div className="row items-center gap-16">
          <div style={{
            width: 48, height: 48, borderRadius: 12,
            background: isDark ? "var(--accent)" : "rgba(107,114,128,0.12)",
            color: isDark ? "#fff" : "var(--ink-500)",
            display: "grid", placeItems: "center", fontSize: 24, fontWeight: 800,
          }}>{labelTag}</div>
          <div className="col" style={{ gap: 2 }}>
            <div style={{ fontSize: 24, letterSpacing: "0.12em", textTransform: "uppercase", fontWeight: 700, color: isDark ? "var(--accent)" : "var(--ink-400)" }}>{isDark ? "After" : "Before"}</div>
            <div className="jp" style={{ fontSize: 28, fontWeight: 700, color: isDark ? "#fff" : "var(--ink-700)" }}>{label}</div>
          </div>
        </div>
        <div className="col gap-16" style={{ marginTop: 8 }}>
          {items.map((item, i) => (
            <div key={i} className="row items-start gap-16">
              <span style={{ color: isDark ? "var(--accent)" : "var(--ink-400)", marginTop: 4, flexShrink: 0 }}>
                {isDark ? (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                )}
              </span>
              <div className="jp" style={{ fontSize: 24, color: isDark ? "#fff" : "var(--ink-700)", lineHeight: 1.45, fontWeight: isDark ? 500 : 400 }}>{item}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="slide-pad">
        <div className="eyebrow jp" style={{ marginBottom: 16 }}>{eyebrow || "SPLIT VIEW"}</div>
        <h1 className="title jp" style={{ fontSize: 60, marginBottom: 48 }}>
          {titleJp || <>Side by Side <span className="underline">Comparison</span></>}
        </h1>
        <div style={{ display: "grid", gridTemplateColumns: "1fr auto 1fr", gap: 40, flex: 1, alignItems: "stretch" }}>
          {renderColumn(lItems, leftLabel || "Before State", "B", leftDark)}
          <div className="col center" style={{ width: 80 }}>
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
            </svg>
          </div>
          {renderColumn(rItems, rightLabel || "After State", "A", rightDark)}
        </div>
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

/* ---------- 8. TABLE ---------- */
function SlideTable({ eyebrow, titleJp, headers, rows, num, total }) {
  const defaultHeaders = ["Aspect", "Option A", "Option B"];
  const defaultRows = [
    ["Approach", "Traditional method described here", "Proposed method described here"],
    ["Timeline", "12-18 months", "8 weeks PoC, 6 months production"],
    ["Operations", "Self-managed operations", "Managed operations support"],
    ["Explainability", "Black-box output", "Explainable with citations"],
    ["Security", "Data sent to external API", "Self-contained environment"],
    ["Pricing", "Usage-based pricing", "Flat-rate pricing"],
  ];
  const h = headers || defaultHeaders;
  const r = rows || defaultRows;

  return (
    <>
      <div className="slide-pad">
        <div className="eyebrow jp" style={{ marginBottom: 16 }}>{eyebrow || "COMPARISON"}</div>
        <h1 className="title jp" style={{ fontSize: 60, marginBottom: 40, textAlign: "center" }}>
          {titleJp || <>Comparison <span className="underline">Table</span></>}
        </h1>
        <table className="cmp-table">
          <thead>
            <tr>
              {h.map((col, i) => (
                <th key={i} style={i === 0 ? { width: "22%" } : i === h.length - 1 ? { width: "40%" } : {}}>
                  {i === h.length - 1 ? (
                    <div style={{ color: "#fff" }}>{col}</div>
                  ) : i === 0 ? (
                    col
                  ) : (
                    <div style={{ color: "var(--navy-300)" }}>{col}</div>
                  )}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {r.map((row, i) => (
              <tr key={i}>
                {row.map((cell, j) => (
                  <td key={j} className={j === 0 ? "label jp" : j === row.length - 1 ? "highlight jp" : "muted jp"}>
                    {j === row.length - 1 ? (
                      <div className="row items-center gap-16">
                        <span style={{ color: "var(--accent)", flexShrink: 0 }}>
                          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                        </span>
                        <span>{cell}</span>
                      </div>
                    ) : cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

/* SlideFlow merged into SlideCardGrid with connected=true prop */

/* ---------- 9. TIMELINE (gantt) ---------- */
function SlideTimeline({ eyebrow, titleJp, phases, months = 12, num, total }) {
  const items = phases || [
    { name: "Phase 1", jp: "Phase A Title", start: 0, span: 2, color: "soft", milestones: ["Task 1", "Task 2"] },
    { name: "Phase 2", jp: "Phase B Title", start: 2, span: 2, color: "accent", milestones: ["Task 3", "Task 4"] },
    { name: "Phase 3", jp: "Phase C Title", start: 4, span: 3, color: "navy", milestones: ["Task 5", "Task 6"] },
    { name: "Phase 4", jp: "Phase D Title", start: 7, span: 5, color: "navy", milestones: ["Task 7", "Task 8"] },
  ];
  const monthLabels = Array.from({ length: months }, (_, i) => `M${i + 1}`);
  const barBg = (c) => c === "accent" ? "var(--accent)" : c === "navy" ? "var(--navy-900)" : "var(--surface-2)";
  const barFg = (c) => c === "soft" ? "var(--navy-900)" : "#fff";
  const barBd = (c) => c === "soft" ? "1px solid var(--border)" : "none";
  const gridCols = `180px repeat(${months}, 1fr)`;

  return (
    <>
      <div className="slide-pad">
        <div className="eyebrow jp" style={{ marginBottom: 16 }}>{eyebrow || "ROADMAP"}</div>
        <h1 className="title jp" style={{ fontSize: 60, marginBottom: 40 }}>
          {titleJp || <>{months}-Month <span className="underline">Roadmap</span></>}
        </h1>
        <div className="card" style={{ padding: 40, flex: 1, display: "flex", flexDirection: "column" }}>
          <div style={{ display: "grid", gridTemplateColumns: gridCols, gap: 8, marginBottom: 24 }}>
            <div />
            {monthLabels.map((m, i) => (
              <div key={i} style={{ fontSize: 24, fontWeight: 600, color: "var(--ink-400)", textAlign: "center", fontFamily: "var(--font-mono)" }}>{m}</div>
            ))}
          </div>
          <div className="col gap-16" style={{ flex: 1 }}>
            {items.map((p, i) => (
              <div key={i} style={{ display: "grid", gridTemplateColumns: gridCols, gap: 8, alignItems: "start" }}>
                <div className="col" style={{ gap: 2, paddingTop: 8 }}>
                  <div className="jp" style={{ fontSize: 24, fontWeight: 700, color: "var(--navy-900)" }}>{p.jp}</div>
                  <div style={{ fontSize: 24, color: "var(--ink-400)", fontWeight: 600 }}>{p.span} months</div>
                </div>
                {Array.from({ length: p.start }).map((_, j) => <div key={"s" + j} />)}
                <div style={{ gridColumn: `${p.start + 2} / -1` }} className="col" >
                  <div style={{
                    height: 48,
                    width: `${(p.span / (months - p.start)) * 100}%`,
                    background: barBg(p.color),
                    color: barFg(p.color),
                    border: barBd(p.color),
                    borderRadius: 10,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 24,
                    fontWeight: 700,
                  }}>
                    <span className="jp">{p.name}</span>
                  </div>
                  {p.milestones && p.milestones.length > 0 && (
                    <div style={{ display: "flex", gap: 24, paddingLeft: 8, flexWrap: "wrap", marginTop: 4 }}>
                      {p.milestones.map((m, j) => (
                        <span key={j} className="row items-center gap-8" style={{ fontSize: 24, color: "var(--ink-500)" }}>
                          <span style={{ width: 8, height: 8, borderRadius: "50%", background: barBg(p.color), flexShrink: 0 }} />
                          <span className="jp">{m}</span>
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

/* ── Chart SVG helpers ── */
function _chartHelpers(W, H, padL, padB, padT, padR) {
  const plotW = W - padL - padR;
  const plotH = H - padT - padB;
  return {
    xFor: (i, len) => padL + (i / (len - 1)) * plotW,
    yFor: (v, maxY) => padT + (1 - v / maxY) * plotH,
    linePath: (data, maxY) => data.map((v, i) =>
      `${i === 0 ? "M" : "L"} ${padL + (i / (data.length - 1)) * plotW} ${padT + (1 - v / maxY) * plotH}`
    ).join(" "),
    areaPath: (data, maxY) => {
      const line = data.map((v, i) =>
        `${i === 0 ? "M" : "L"} ${padL + (i / (data.length - 1)) * plotW} ${padT + (1 - v / maxY) * plotH}`
      ).join(" ");
      return `${line} L ${padL + plotW} ${padT + plotH} L ${padL} ${padT + plotH} Z`;
    },
    gridLines: (maxY, steps) => Array.from({ length: steps + 1 }, (_, i) => Math.round(maxY / steps * i)),
    W, H, padL, padB, padT, padR, plotW, plotH,
  };
}

/* ---------- 10. CHART — configurable: line, bar, donut ---------- */
function SlideChart({ eyebrow, titleJp, chartType = "line", data, labels, series, summary, num, total }) {
  const W = 900, H = 420, padL = 70, padB = 50, padT = 20, padR = 20;
  const ch = _chartHelpers(W, H, padL, padB, padT, padR);

  const items = summary || [
    { label: "Metric A", val: "85M" },
    { label: "Metric B", val: "36M" },
    { label: "Metric C", val: "380M" },
    { label: "Total", val: "412%", accent: true },
  ];

  const colors = ["var(--navy-900)", "var(--accent)", "var(--navy-500)"];

  function renderLineChart() {
    const s = series || [
      { name: "Series A", data: [5, 12, 24, 42, 68, 98, 132, 172, 218, 268, 322, 380] },
      { name: "Series B", data: [40, 45, 50, 55, 50, 48, 45, 42, 40, 38, 36, 34] },
    ];
    const lbls = labels || Array.from({ length: 12 }, (_, i) => `M${i + 1}`);
    const maxY = Math.max(...s.flatMap(x => x.data)) * 1.1;
    const gridVals = ch.gridLines(maxY, 4);

    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "100%", flex: 1 }}>
        {gridVals.map((v, i) => (
          <g key={i}>
            <line x1={padL} x2={W - padR} y1={ch.yFor(v, maxY)} y2={ch.yFor(v, maxY)} stroke="var(--border)" strokeDasharray="4 6" />
            <text x={padL - 12} y={ch.yFor(v, maxY) + 5} fill="var(--ink-400)" fontSize="14" textAnchor="end" fontFamily="var(--font-mono)">{Math.round(v)}</text>
          </g>
        ))}
        {lbls.map((l, i) => <text key={i} x={ch.xFor(i, lbls.length)} y={H - 20} fill="var(--ink-400)" fontSize="14" textAnchor="middle" fontFamily="var(--font-mono)">{l}</text>)}
        {s.map((sr, si) => (
          <g key={si}>
            {si === 0 && <path d={ch.areaPath(sr.data, maxY)} fill={colors[si]} opacity="0.08" />}
            <path d={ch.linePath(sr.data, maxY)} fill="none" stroke={colors[si]} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
            <circle cx={ch.xFor(sr.data.length - 1, sr.data.length)} cy={ch.yFor(sr.data[sr.data.length - 1], maxY)} r="5" fill={colors[si]} />
          </g>
        ))}
      </svg>
    );
  }

  function renderBarChart() {
    const d = data || [120, 85, 200, 160, 240, 180];
    const lbls = labels || ["Q1", "Q2", "Q3", "Q4", "Q5", "Q6"];
    const maxY = Math.max(...d) * 1.2;
    const barW = ch.plotW / d.length * 0.6;
    const gap = ch.plotW / d.length;
    const gridVals = ch.gridLines(maxY, 4);

    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "100%", flex: 1 }}>
        {gridVals.map((v, i) => (
          <g key={i}>
            <line x1={padL} x2={W - padR} y1={ch.yFor(v, maxY)} y2={ch.yFor(v, maxY)} stroke="var(--border)" strokeDasharray="4 6" />
            <text x={padL - 12} y={ch.yFor(v, maxY) + 5} fill="var(--ink-400)" fontSize="14" textAnchor="end" fontFamily="var(--font-mono)">{Math.round(v)}</text>
          </g>
        ))}
        {d.map((v, i) => {
          const x = padL + gap * i + (gap - barW) / 2;
          const y = ch.yFor(v, maxY);
          const h = padT + ch.plotH - y;
          return (
            <g key={i}>
              <rect x={x} y={y} width={barW} height={h} rx={6} fill={i === d.length - 1 ? "var(--accent)" : "var(--navy-900)"} opacity={i === d.length - 1 ? 1 : 0.85} />
              <text x={x + barW / 2} y={H - 20} fill="var(--ink-400)" fontSize="14" textAnchor="middle" fontFamily="var(--font-mono)">{lbls[i]}</text>
              <text x={x + barW / 2} y={y - 10} fill="var(--navy-900)" fontSize="14" textAnchor="middle" fontWeight="700" fontFamily="var(--font-mono)">{v}</text>
            </g>
          );
        })}
      </svg>
    );
  }

  function renderDonutChart() {
    const d = data || [
      { label: "Category A", value: 40, color: "var(--navy-900)" },
      { label: "Category B", value: 25, color: "var(--accent)" },
      { label: "Category C", value: 20, color: "var(--navy-500)" },
      { label: "Category D", value: 15, color: "var(--navy-300)" },
    ];
    const total = d.reduce((s, x) => s + x.value, 0);
    const cx = W / 2, cy = H / 2, r = 160, inner = 100;
    let angle = -90;

    return (
      <svg viewBox={`0 0 ${W} ${H}`} style={{ width: "100%", height: "100%", flex: 1 }}>
        {d.map((seg, i) => {
          const sweep = (seg.value / total) * 360;
          const startRad = (angle * Math.PI) / 180;
          const endRad = ((angle + sweep) * Math.PI) / 180;
          const largeArc = sweep > 180 ? 1 : 0;
          const x1 = cx + r * Math.cos(startRad), y1 = cy + r * Math.sin(startRad);
          const x2 = cx + r * Math.cos(endRad), y2 = cy + r * Math.sin(endRad);
          const ix1 = cx + inner * Math.cos(endRad), iy1 = cy + inner * Math.sin(endRad);
          const ix2 = cx + inner * Math.cos(startRad), iy2 = cy + inner * Math.sin(startRad);
          const path = `M ${x1} ${y1} A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2} L ${ix1} ${iy1} A ${inner} ${inner} 0 ${largeArc} 0 ${ix2} ${iy2} Z`;
          const midRad = ((angle + sweep / 2) * Math.PI) / 180;
          const lx = cx + (r + 70) * Math.cos(midRad);
          const ly = cy + (r + 70) * Math.sin(midRad);
          angle += sweep;
          return (
            <g key={i}>
              <path d={path} fill={seg.color} />
              <text x={lx} y={ly - 14} fill="var(--ink-700)" fontSize="24" textAnchor="middle" dominantBaseline="middle" fontWeight="600" className="jp">{seg.label}</text>
              <text x={lx} y={ly + 14} fill="var(--ink-400)" fontSize="24" textAnchor="middle" fontFamily="var(--font-mono)">{Math.round(seg.value / total * 100)}%</text>
            </g>
          );
        })}
        <text x={cx} y={cy - 10} fill="var(--navy-900)" fontSize="48" textAnchor="middle" fontWeight="800" fontFamily="var(--font-mono)">{total}</text>
        <text x={cx} y={cy + 28} fill="var(--ink-400)" fontSize="24" textAnchor="middle">Total</text>
      </svg>
    );
  }

  const chartRenderer = chartType === "bar" ? renderBarChart : chartType === "donut" ? renderDonutChart : renderLineChart;

  return (
    <>
      <div className="slide-pad">
        <div className="eyebrow jp" style={{ marginBottom: 16 }}>{eyebrow || "CHART"}</div>
        <h1 className="title jp" style={{ fontSize: 60, marginBottom: 40 }}>
          {titleJp || <>Data <span className="underline">Chart</span></>}
        </h1>
        <div className="row gap-48" style={{ flex: 1 }}>
          <div className="card" style={{ flex: 1.6, padding: 40, display: "flex", flexDirection: "column" }}>
            {chartType === "line" && (
              <div className="row between items-center" style={{ marginBottom: 12 }}>
                <div className="jp" style={{ fontSize: 24, fontWeight: 700, color: "var(--navy-900)" }}>Trend Chart</div>
                <div className="row gap-24" style={{ fontSize: 24 }}>
                  {(series || [{ name: "Series A" }, { name: "Series B" }]).map((s, i) => (
                    <span key={i} className="row items-center gap-8"><span style={{ width: 16, height: 3, background: colors[i] }} /> {s.name}</span>
                  ))}
                </div>
              </div>
            )}
            {chartRenderer()}
          </div>
          <div className="col gap-24" style={{ flex: 1, justifyContent: "center" }}>
            {items.map((k, i) => (
              <div key={i} className="row between items-center" style={{ padding: "24px 28px", background: "#fff", borderRadius: 12, border: "1px solid var(--border)" }}>
                <div className="jp" style={{ fontSize: 24, fontWeight: 700, color: "var(--navy-900)" }}>{k.label}</div>
                <div style={{ fontSize: 36, fontWeight: 800, color: k.accent ? "var(--accent)" : "var(--navy-900)", fontFamily: "var(--font-mono)" }}>{k.val}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

/* ---------- 11. LIST ---------- */
function SlideList({ eyebrow, titleJp, items, num, total }) {
  const list = items || [
    { jp: "Item Title 1", en: "Item Title 1" },
    { jp: "Item Title 2", en: "Item Title 2" },
    { jp: "Item Title 3", en: "Item Title 3" },
    { jp: "Item Title 4", en: "Item Title 4" },
    { jp: "Item Title 5", en: "Item Title 5" },
    { jp: "Item Title 6", en: "Item Title 6" },
    { jp: "Item Title 7", en: "Item Title 7" },
    { jp: "Item Title 8", en: "Item Title 8" },
  ];
  return (
    <>
      <div className="slide-grid-bg" />
      <div className="slide-pad">
        <div className="eyebrow jp" style={{ marginBottom: 24 }}>{eyebrow || "AGENDA"}</div>
        <h1 className="title jp" style={{ fontSize: 72, marginBottom: 64 }}>
          {titleJp || <>Table of <span className="underline">Contents</span></>}
        </h1>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", columnGap: 64, rowGap: 28, flex: 1 }}>
          {list.map((item, i) => (
            <div key={i} className="row items-center gap-24" style={{ padding: "24px 32px", background: "#fff", borderRadius: 14, border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
              <div style={{ fontSize: 28, fontWeight: 800, color: "var(--accent)", minWidth: 48, fontFamily: "var(--font-mono)" }}>{String(i + 1).padStart(2, "0")}</div>
              <div className="col" style={{ gap: 4 }}>
                <div className="jp" style={{ fontSize: 28, fontWeight: 700, color: "var(--navy-900)" }}>{item.jp}</div>
                {item.en && <div style={{ fontSize: 24, color: "var(--ink-500)" }}>{item.en}</div>}
              </div>
            </div>
          ))}
        </div>
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

Object.assign(window, {
  SlideSplit, SlideTable,
  SlideTimeline, SlideChart, SlideList,
});
