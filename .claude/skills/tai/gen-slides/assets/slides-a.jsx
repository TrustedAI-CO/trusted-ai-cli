/* =========================================================
   Slide layouts — Part A: hero, divider, big-number, quote, card-grid, stat-row
   16 layout types total. Generic placeholder content.
   ========================================================= */

const TOTAL_SLIDES = 16;

/* ---------- 1. HERO ---------- */
function SlideHero({ brand = "TrustedAI", tag, title, subtitle, meta = {}, num, total }) {
  return (
    <>
      <div className="slide-grid-bg" />
      <div className="slide-pad" style={{ justifyContent: "space-between" }}>
        <div className="row between items-start">
          <div className="brand-mark" style={{ fontSize: 30 }}>
            <span className="dot" />
            <span>{brand}</span>
          </div>
          {meta.client && (
            <div className="col items-end" style={{ gap: 8 }}>
              <div className="micro" style={{ fontSize: 24, letterSpacing: "0.12em", textTransform: "uppercase" }}>
                {meta.clientLabel || "Proposal for"}
              </div>
              <div className="jp" style={{ fontSize: 28, fontWeight: 700, color: "var(--navy-900)" }}>{meta.client}</div>
            </div>
          )}
        </div>

        <div className="col" style={{ gap: 48, maxWidth: 1500 }}>
          {tag && (
            <div className="row gap-16 items-center">
              <div className="pill pill-outline jp" style={{ whiteSpace: "nowrap" }}>{tag}</div>
            </div>
          )}
          <h1 className="title jp" style={{ fontSize: 120, fontWeight: 800, lineHeight: 1.02, letterSpacing: "-0.025em" }}>
            {title || <>Your Title Goes <span className="underline">Here</span></>}
          </h1>
          <div className="subtitle" style={{ fontSize: 34, maxWidth: 1300, color: "var(--ink-500)", fontWeight: 400, lineHeight: 1.4 }}>
            {subtitle || "Subtitle text supporting the main title goes here."}
          </div>
        </div>

        <div className="row between items-end">
          <div className="col" style={{ gap: 6 }}>
            <div className="micro" style={{ fontSize: 24, letterSpacing: "0.12em" }}>{meta.leftLabel || "PRESENTED BY"}</div>
            <div style={{ fontSize: 24, fontWeight: 600, color: "var(--navy-900)" }}>{meta.leftValue || `${brand} Team`}</div>
          </div>
          <div className="col items-end" style={{ gap: 6 }}>
            <div className="micro" style={{ fontSize: 24, letterSpacing: "0.12em" }}>{meta.rightLabel || "DATE"}</div>
            <div style={{ fontSize: 24, fontWeight: 600, color: "var(--navy-900)" }}>{meta.rightValue || "April 2026"}</div>
          </div>
        </div>
      </div>
    </>
  );
}

/* ---------- 2. DIVIDER ---------- */
function SlideDivider({ numLabel = "01", titleJp, titleEn, lead, num, total }) {
  return (
    <>
      <div className="slide-grid-bg" />
      <div className="slide-pad">
        <div className="row" style={{ flex: 1 }}>
          <div className="col" style={{ flex: 1, justifyContent: "center", gap: 40 }}>
            <div className="eyebrow">SECTION {numLabel}</div>
            <h1 className="title jp" style={{ fontSize: 104, fontWeight: 800, lineHeight: 1 }}>
              {titleJp || "Section Title"}
            </h1>
            <div style={{ fontSize: 40, color: "var(--ink-500)", fontWeight: 500, letterSpacing: "-0.01em" }}>
              {titleEn || "Section Title"}
            </div>
            {lead && <div className="lead" style={{ maxWidth: 800, marginTop: 20 }}>{lead}</div>}
          </div>
          <div className="col center" style={{ flex: 1 }}>
            <div className="section-num">{numLabel}</div>
          </div>
        </div>
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

/* ---------- 3. BIG NUMBER ---------- */
function SlideBigNumber({ eyebrow, number = "73", unit = "%", titleJp, lead, source, num, total }) {
  return (
    <>
      <div className="slide-grid-bg" />
      <div className="slide-pad" style={{ justifyContent: "center" }}>
        <div className="row" style={{ gap: 80, alignItems: "center" }}>
          <div className="col" style={{ flex: 1, gap: 40 }}>
            <div className="eyebrow">{eyebrow || "BY THE NUMBERS"}</div>
            <div className="big-num" style={{ fontSize: 300 }}>
              {number}<span className="unit">{unit}</span>
            </div>
          </div>
          <div className="col" style={{ flex: 1, gap: 32 }}>
            <h2 className="title jp" style={{ fontSize: 56, lineHeight: 1.2 }}>
              {titleJp || "Context explaining this number."}
            </h2>
            <div className="lead">
              {lead || "Context paragraph explaining what the number means and why it matters to the audience."}
            </div>
            {source && (
              <div className="row gap-16" style={{ marginTop: 16 }}>
                <div className="pill pill-outline pill">{source}</div>
              </div>
            )}
          </div>
        </div>
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

/* ---------- 4. QUOTE ---------- */
function SlideQuote({ quote, authorName, authorTitle, num, total }) {
  const initials = (authorName || "YT").split(/\s+/).map(w => w[0]).join("").slice(0, 2);
  return (
    <>
      <div className="slide-grid-bg" />
      <div className="slide-pad" style={{ justifyContent: "center", alignItems: "center" }}>
        <div className="col center" style={{ maxWidth: 1500, gap: 48, textAlign: "center" }}>
          <div style={{ fontSize: 180, color: "var(--accent)", lineHeight: 0.6, fontFamily: "serif", fontWeight: 700 }}>"</div>
          <div className="jp" style={{ fontSize: 52, fontWeight: 600, color: "var(--navy-900)", lineHeight: 1.3, letterSpacing: "-0.01em", textWrap: "pretty" }}>
            {quote || <>A compelling quote goes here.<br />A memorable statement from a key person.</>}
          </div>
          <div className="row items-center gap-24" style={{ marginTop: 16 }}>
            <div style={{ width: 80, height: 80, borderRadius: "50%", background: "linear-gradient(135deg, var(--navy-900), var(--navy-700))", color: "#fff", display: "grid", placeItems: "center", fontSize: 28, fontWeight: 700 }}>{initials}</div>
            <div className="col items-start" style={{ gap: 4, textAlign: "left" }}>
              <div className="jp" style={{ fontSize: 28, fontWeight: 700, color: "var(--navy-900)" }}>{authorName || "Jane Doe"}</div>
              <div style={{ fontSize: 24, color: "var(--ink-500)" }}>{authorTitle || "Head of Department · Company Name"}</div>
            </div>
          </div>
        </div>
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

/* ---------- 5. CARD GRID ----------
   Configurable: cols (2|3|4), rows (1|2), cardStyle (default|numbered|metric|profile)
   ---------- */
function SlideCardGrid({ eyebrow, titleJp, body, cards, cols = 3, cardStyle = "default", connected = false, num, total }) {
  const defaults = {
    default: [
      { icon: "target", title: "Card Title 1", desc: "Description text for this card. One to two lines recommended." },
      { icon: "clock", title: "Card Title 2", desc: "Description text for this card. One to two lines recommended." },
      { icon: "trend", title: "Card Title 3", desc: "Description text for this card. One to two lines recommended." },
      { icon: "shield", title: "Card Title 4", desc: "Description text for this card. One to two lines recommended." },
    ],
    numbered: [
      { title: "Step 1", desc: "Brief description of step one." },
      { title: "Step 2", desc: "Brief description of step two." },
      { title: "Step 3", desc: "Brief description of step three." },
      { title: "Step 4", desc: "Brief description of step four." },
    ],
    metric: [
      { value: "¥240M", label: "Metric A", labelEn: "Cost reduction", delta: "-38%" },
      { value: "4.2min", label: "Metric B", labelEn: "Processing time", delta: "-82%" },
      { value: "96.4%", label: "Metric C", labelEn: "Accuracy", delta: "+31pt" },
      { value: "+42", label: "Metric D", labelEn: "Employee NPS", delta: "+58pt" },
    ],
    profile: [
      { name: "Person A", nameEn: "Person A", role: "Role Title", bio: "Professional background." },
      { name: "Person B", nameEn: "Person B", role: "Role Title", bio: "Professional background." },
      { name: "Person C", nameEn: "Person C", role: "Role Title", bio: "Professional background." },
      { name: "Person D", nameEn: "Person D", role: "Role Title", bio: "Professional background." },
    ],
  };
  const items = cards || defaults[cardStyle] || defaults.default;
  const rows = Math.ceil(items.length / cols);
  const gridCols = `repeat(${cols}, 1fr)`;

  return (
    <>
      <div className="slide-pad">
        <div className="eyebrow jp" style={{ marginBottom: 20 }}>{eyebrow || "CARD GRID"}</div>
        <h1 className="title jp" style={{ fontSize: 60, marginBottom: 12 }}>
          {titleJp || <>Card Grid <span className="underline">Layout</span></>}
        </h1>
        {body && <div className="body" style={{ marginBottom: 40 }}>{body}</div>}

        {connected ? (
          /* ── Connected mode: horizontal flow with arrows ── */
          <div className="row items-stretch" style={{ gap: 0, flex: 1, marginTop: body ? 0 : 40 }}>
            {items.map((item, i) => (
              <React.Fragment key={i}>
                <div className="col" style={{ flex: 1, padding: 24, background: "#fff", border: "1px solid var(--border)", borderRadius: 14, gap: 18, boxShadow: "var(--shadow-card)" }}>
                  <div className="row between items-center">
                    <div className="icon-chip-sm"><Icon name={item.icon || "target"} /></div>
                    <div style={{ fontSize: 24, fontWeight: 700, color: "var(--accent)", letterSpacing: "0.12em", fontFamily: "var(--font-mono)" }}>STEP {String(i + 1).padStart(2, "0")}</div>
                  </div>
                  <div className="jp" style={{ fontSize: 24, fontWeight: 700, color: "var(--navy-900)" }}>{item.title}</div>
                  <div className="jp" style={{ fontSize: 24, color: "var(--ink-500)", lineHeight: 1.5 }}>{item.desc}</div>
                </div>
                {i < items.length - 1 && (
                  <div className="col center" style={{ width: 36, color: "var(--accent)" }}>
                    <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
                    </svg>
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        ) : (
          /* ── Grid mode: standard card grid ── */
          <div style={{ display: "grid", gridTemplateColumns: gridCols, gap: 24, flex: 1, marginTop: body ? 0 : 40 }}>
            {items.map((item, i) => {
              if (cardStyle === "metric") return (
                <div key={i} className="col" style={{ padding: 32, background: "#fff", borderRadius: 16, border: "1px solid var(--border)", boxShadow: "var(--shadow-card)", gap: 16 }}>
                  <div className="row between items-start">
                    <div className="col" style={{ gap: 4 }}>
                      <div className="jp" style={{ fontSize: 24, fontWeight: 600, color: "var(--ink-500)" }}>{item.label}</div>
                      {item.labelEn && <div style={{ fontSize: 24, color: "var(--ink-400)", letterSpacing: "0.08em", textTransform: "uppercase", fontWeight: 600 }}>{item.labelEn}</div>}
                    </div>
                    {item.delta && <div style={{ padding: "6px 12px", background: "var(--accent-soft)", color: "var(--accent)", borderRadius: 999, fontSize: 24, fontWeight: 700, fontFamily: "var(--font-mono)" }}>{item.delta}</div>}
                  </div>
                  <div style={{ fontSize: 48, fontWeight: 800, color: "var(--navy-900)", letterSpacing: "-0.03em", fontFamily: "var(--font-mono)", marginTop: 8 }}>{item.value}</div>
                </div>
              );
              if (cardStyle === "profile") {
                const initials = (item.nameEn || item.name || "XX").split(/\s+/).map(w => w[0]).join("").slice(0, 2);
                return (
                  <div key={i} className="col" style={{ padding: 32, background: "#fff", borderRadius: 16, border: "1px solid var(--border)", boxShadow: "var(--shadow-card)", gap: 20, alignItems: "center", textAlign: "center" }}>
                    <div style={{ width: 120, height: 120, borderRadius: "50%", background: "linear-gradient(135deg, var(--navy-900), var(--navy-700))", color: "#fff", display: "grid", placeItems: "center", fontSize: 40, fontWeight: 700 }}>{initials}</div>
                    <div className="col" style={{ gap: 4 }}>
                      <div className="jp" style={{ fontSize: 24, fontWeight: 700, color: "var(--navy-900)" }}>{item.name}</div>
                      <div className="jp" style={{ fontSize: 24, fontWeight: 600, color: "var(--accent)" }}>{item.role}</div>
                    </div>
                    <div className="jp" style={{ fontSize: 24, color: "var(--ink-500)", lineHeight: 1.5 }}>{item.bio}</div>
                  </div>
                );
              }
              if (cardStyle === "numbered") return (
                <div key={i} className="col" style={{ padding: 32, background: "#fff", borderRadius: 16, border: "1px solid var(--border)", boxShadow: "var(--shadow-card)", gap: 20 }}>
                  <div className="row between items-center">
                    <div style={{ fontSize: 56, fontWeight: 800, color: "var(--surface-2)", fontFamily: "var(--font-mono)" }}>{String(i + 1).padStart(2, "0")}</div>
                  </div>
                  <div className="jp" style={{ fontSize: 26, fontWeight: 700, color: "var(--navy-900)" }}>{item.title}</div>
                  <div className="jp" style={{ fontSize: 24, color: "var(--ink-500)", lineHeight: 1.5 }}>{item.desc}</div>
                </div>
              );
              // default: icon card
              return (
                <div key={i} className="row items-start gap-24" style={{ padding: 36, background: "#fff", borderRadius: 16, border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
                  <div className="icon-chip"><Icon name={item.icon || "target"} /></div>
                  <div className="col" style={{ gap: 10 }}>
                    <div className="jp" style={{ fontSize: 26, fontWeight: 700, color: "var(--navy-900)", lineHeight: 1.3 }}>{item.title}</div>
                    <div className="jp" style={{ fontSize: 24, color: "var(--ink-500)", lineHeight: 1.5 }}>{item.desc}</div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

/* ---------- 6. STAT ROW ---------- */
function SlideStatRow({ eyebrow, titleJp, stats, num, total }) {
  const items = stats || [
    { value: "15,000", label: "Metric A", source: "" },
    { value: "74.1%", label: "Metric B", source: "" },
    { value: "1.84兆円", label: "Metric C", source: "" },
  ];
  return (
    <>
      <div className="slide-pad">
        <div className="eyebrow jp" style={{ marginBottom: 20 }}>{eyebrow || "KEY METRICS"}</div>
        <h1 className="title jp" style={{ fontSize: 60, marginBottom: 60 }}>
          {titleJp || <>Overview of <span className="underline">Key Metrics</span></>}
        </h1>
        <div style={{ display: "grid", gridTemplateColumns: `repeat(${items.length}, 1fr)`, gap: 48, flex: 1, alignItems: "center" }}>
          {items.map((s, i) => (
            <div key={i} className="col" style={{ gap: 12, textAlign: "center", padding: "40px 20px", borderRight: i < items.length - 1 ? "1px solid var(--border)" : "none" }}>
              <div style={{ fontSize: 72, fontWeight: 900, color: "var(--navy-900)", fontFamily: "var(--font-mono)", letterSpacing: "-0.04em", lineHeight: 1 }}>{s.value}</div>
              <div className="jp" style={{ fontSize: 24, fontWeight: 600, color: "var(--ink-700)", marginTop: 8 }}>{s.label}</div>
              {s.source && <div style={{ fontSize: 24, color: "var(--ink-400)" }}>{s.source}</div>}
            </div>
          ))}
        </div>
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

Object.assign(window, {
  SlideHero, SlideDivider, SlideBigNumber, SlideQuote,
  SlideCardGrid, SlideStatRow, TOTAL_SLIDES,
});
