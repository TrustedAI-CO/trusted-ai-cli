/* =========================================================
   Slide layouts — Part C: matrix
   ========================================================= */

/* ---------- 12. MATRIX (2x2 quadrant) ---------- */
function SlideMatrix({ eyebrow, titleJp, xAxis, yAxis, quadrants, num, total }) {
  const q = quadrants || [
    { label: "Quadrant A", desc: "Low × Low", color: "var(--ink-400)", bg: "var(--bg-soft)", textColor: "var(--ink-500)" },
    { label: "Quadrant B", desc: "High × Low", color: "var(--navy-500)", bg: "rgba(10,22,64,0.06)", textColor: "var(--ink-500)" },
    { label: "Quadrant C", desc: "Low × High", color: "var(--accent)", bg: "var(--accent-soft)", textColor: "var(--ink-700)" },
    { label: "Quadrant D", desc: "High × High", color: "#fff", bg: "var(--navy-900)", textColor: "var(--navy-300)" },
  ];

  // Layout: [1=top-left, 3=top-right, 0=bottom-left, 2=bottom-right]
  const grid = [[1, 3], [0, 2]];

  return (
    <>
      <div className="slide-pad">
        <div className="eyebrow jp" style={{ marginBottom: 16 }}>{eyebrow || "PRIORITY MATRIX"}</div>
        <h1 className="title jp" style={{ fontSize: 60, marginBottom: 32 }}>
          {titleJp || <>Two-by-Two <span className="underline">Matrix</span></>}
        </h1>

        <div className="row" style={{ flex: 1, gap: 0 }}>
          {/* Y-axis */}
          <div className="col between items-center" style={{ width: 48, paddingBottom: 48, paddingRight: 16 }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--ink-400)", letterSpacing: "0.08em" }}>HIGH</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--accent)", transform: "rotate(-90deg)", whiteSpace: "nowrap" }}>
              {yAxis || "Dimension Y"}
            </div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--ink-400)", letterSpacing: "0.08em" }}>LOW</div>
          </div>

          <div className="col" style={{ flex: 1 }}>
            {/* Quadrant grid — no gap, shared borders */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gridTemplateRows: "1fr 1fr", flex: 1 }}>
              {grid.flat().map((qi, i) => {
                const seg = q[qi];
                const isTopLeft = i === 0, isTopRight = i === 1, isBottomLeft = i === 2, isBottomRight = i === 3;
                const radius = isTopLeft ? "20px 0 0 0" : isTopRight ? "0 20px 0 0" : isBottomLeft ? "0 0 0 20px" : "0 0 20px 0";
                return (
                  <div key={i} className="col center" style={{
                    background: seg.bg,
                    borderRadius: radius,
                    padding: 40,
                    gap: 16,
                    border: seg.bg === "var(--navy-900)" ? "none" : "1px solid var(--border)",
                    margin: seg.bg === "var(--navy-900)" ? 0 : -0.5,
                  }}>
                    <div className="jp" style={{ fontSize: 40, fontWeight: 800, color: seg.color, lineHeight: 1 }}>{seg.label}</div>
                    <div className="jp" style={{ fontSize: 24, color: seg.textColor, textAlign: "center" }}>{seg.desc}</div>
                  </div>
                );
              })}
            </div>

            {/* X-axis */}
            <div className="row between" style={{ marginTop: 16, paddingLeft: 16, paddingRight: 16 }}>
              <div style={{ fontSize: 24, fontWeight: 700, color: "var(--ink-400)", letterSpacing: "0.08em" }}>LOW</div>
              <div className="jp" style={{ fontSize: 24, fontWeight: 700, color: "var(--accent)" }}>
                {xAxis || "Dimension X"}
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, color: "var(--ink-400)", letterSpacing: "0.08em" }}>HIGH</div>
            </div>
          </div>
        </div>
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

/* ---------- 13. CLOSING ---------- */
function SlideClosing({ brand = "TrustedAI", title, subtitle, contact, num, total }) {
  const c = contact || { name: "Team Name", email: "hello@example.com", phone: "+1 000-000-0000", web: "example.com" };
  return (
    <>
      <div className="slide-grid-bg" />
      <div className="slide-pad" style={{ justifyContent: "space-between" }}>
        <div className="row between items-start">
          <div className="brand-mark" style={{ fontSize: 24 }}>
            <span className="dot" />
            <span>{brand}</span>
          </div>
          <div className="micro" style={{ fontSize: 24 }}>END OF PRESENTATION</div>
        </div>

        <div className="col center" style={{ textAlign: "center", gap: 32, margin: "auto", maxWidth: 1500 }}>
          <div className="eyebrow" style={{ fontSize: 24 }}>THANK YOU</div>
          <h1 className="title jp" style={{ fontSize: 140, fontWeight: 800, lineHeight: 1 }}>
            {title || <>Thank You</>}
          </h1>
          {subtitle && (
            <div className="subtitle" style={{ fontSize: 32 }}>{subtitle}</div>
          )}
        </div>

        <div className="row between" style={{ gap: 48 }}>
          <div className="col gap-6">
            <div className="micro" style={{ fontSize: 24, letterSpacing: "0.12em" }}>CONTACT</div>
            <div style={{ fontSize: 24, fontWeight: 700, color: "var(--navy-900)" }}>{c.name}</div>
          </div>
          <div className="col gap-6">
            <div className="micro" style={{ fontSize: 24, letterSpacing: "0.12em" }}>EMAIL</div>
            <div style={{ fontSize: 24, fontWeight: 600, color: "var(--navy-900)" }}>{c.email}</div>
          </div>
          <div className="col gap-6">
            <div className="micro" style={{ fontSize: 24, letterSpacing: "0.12em" }}>PHONE</div>
            <div style={{ fontSize: 24, fontWeight: 600, color: "var(--navy-900)" }}>{c.phone}</div>
          </div>
          <div className="col gap-6">
            <div className="micro" style={{ fontSize: 24, letterSpacing: "0.12em" }}>WEB</div>
            <div style={{ fontSize: 24, fontWeight: 600, color: "var(--navy-900)" }}>{c.web}</div>
          </div>
        </div>
      </div>
    </>
  );
}

/* ---------- 14. TITLE + CONTENT (flexible single area) ---------- */
function SlideTitleContent({ eyebrow, titleJp, children, num, total }) {
  return (
    <>
      <div className="slide-pad">
        <div className="eyebrow jp" style={{ marginBottom: 16 }}>{eyebrow || "SECTION"}</div>
        <h1 className="title jp" style={{ fontSize: 60, marginBottom: 32 }}>
          {titleJp || <>Title and <span className="underline">Content</span></>}
        </h1>
        <div style={{ flex: 1 }}>
          {children || (
            <div className="card" style={{ height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <div style={{ fontSize: 28, color: "var(--ink-400)", textAlign: "center" }}>
                Content area — place any elements here.<br />
                Text, images, cards, lists, or custom layouts.
              </div>
            </div>
          )}
        </div>
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

/* ---------- 15. TWO COLUMN (flexible left/right) ---------- */
function SlideTwoColumn({ eyebrow, titleJp, left, right, ratio = "1fr 1fr", num, total }) {
  return (
    <>
      <div className="slide-pad">
        <div className="eyebrow jp" style={{ marginBottom: 16 }}>{eyebrow || "SECTION"}</div>
        <h1 className="title jp" style={{ fontSize: 60, marginBottom: 32 }}>
          {titleJp || <>Two Column <span className="underline">Layout</span></>}
        </h1>
        <div style={{ display: "grid", gridTemplateColumns: ratio, gap: 40, flex: 1 }}>
          <div className="card" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
            {left || (
              <div style={{ fontSize: 28, color: "var(--ink-400)", textAlign: "center" }}>
                Left column content
              </div>
            )}
          </div>
          <div className="card" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
            {right || (
              <div style={{ fontSize: 28, color: "var(--ink-400)", textAlign: "center" }}>
                Right column content
              </div>
            )}
          </div>
        </div>
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

/* ---------- 16. BLANK (just chrome, empty canvas) ---------- */
function SlideBlank({ children, num, total }) {
  return (
    <>
      <div className="slide-pad" style={{ justifyContent: "center", alignItems: "center" }}>
        {children || (
          <div style={{ fontSize: 28, color: "var(--ink-400)", textAlign: "center" }}>
            Blank slide — full creative freedom.<br />
            Place any custom content here.
          </div>
        )}
      </div>
      <SlideChrome num={num} total={total} />
    </>
  );
}

Object.assign(window, { SlideMatrix, SlideClosing, SlideTitleContent, SlideTwoColumn, SlideBlank });
