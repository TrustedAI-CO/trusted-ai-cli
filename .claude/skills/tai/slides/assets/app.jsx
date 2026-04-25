/* =========================================================
   App — mounts each slide into its <section>
   ========================================================= */

const TOTAL = 24;

const DEFAULTS = /*EDITMODE-BEGIN*/{
  "accent": "#E63946",
  "clientName": "株式会社クライアント",
  "clientNameEn": "Client Corporation",
  "brandName": "TrustedAI",
  "presenter": "TrustedAI Solutions Team",
  "date": "2026年4月",
  "density": "balanced"
}/*EDITMODE-END*/;

function App() {
  const [tweaks, setTweaks] = (typeof useTweaks === "function")
    ? (() => {
        const t = useTweaks(DEFAULTS);
        return t;
      })()
    : [DEFAULTS, () => {}];

  // Apply accent color live
  React.useEffect(() => {
    document.documentElement.style.setProperty("--accent", tweaks.accent);
    // derived soft bg
    const hex = tweaks.accent.replace("#", "");
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);
    document.documentElement.style.setProperty("--accent-soft", `rgba(${r},${g},${b},0.10)`);
  }, [tweaks.accent]);

  const shared = { total: TOTAL, brand: tweaks.brandName };

  const slides = [
    [1, "s1", <SlideCover {...shared} num={1} client={tweaks.clientName} clientEn={tweaks.clientNameEn} presenter={tweaks.presenter} date={tweaks.date} brand={tweaks.brandName} />],
    [2, "s2", <SlideAgenda {...shared} num={2} />],
    [3, "s3", <SlideSection {...shared} num={3} numLabel="01" titleJp="現状の課題" titleEn="Current Challenges" lead="貴社が直面している業務上の制約と、今取り組むべき優先課題を整理します。" />],
    [4, "s4", <SlideExecSummary {...shared} num={4} />],
    [5, "s5", <SlideProblem {...shared} num={5} />],
    [6, "s6", <SlideBigStat {...shared} num={6} />],
    [7, "s7", <SlideSection {...shared} num={7} numLabel="02" titleJp="ご提案ソリューション" titleEn="Proposed Solution" lead="TrustedAI がご提供する、信頼できるAI導入アプローチの全体像。" />],
    [8, "s8", <SlideSolution {...shared} num={8} />],
    [9, "s9", <SlideArchitecture {...shared} num={9} />],
    [10, "s10", <SlideWorkflow {...shared} num={10} />],
    [11, "s11", <SlideUseCases {...shared} num={11} />],
    [12, "s12", <SlideComparison {...shared} num={12} />],
    [13, "s13", <SlideBeforeAfter {...shared} num={13} />],
    [14, "s14", <SlideSection {...shared} num={14} numLabel="03" titleJp="導入計画と投資効果" titleEn="Plan & Business Case" lead="スケジュール、目標KPI、投資対効果、価格プランの全体像。" />],
    [15, "s15", <SlideRoadmap {...shared} num={15} />],
    [16, "s16", <SlideKPI {...shared} num={16} />],
    [17, "s17", <SlideROI {...shared} num={17} />],
    [18, "s18", <SlidePricing {...shared} num={18} />],
    [19, "s19", <SlideTeam {...shared} num={19} />],
    [20, "s20", <SlideCaseStudy {...shared} num={20} />],
    [21, "s21", <SlideQuote {...shared} num={21} />],
    [22, "s22", <SlideRisk {...shared} num={22} />],
    [23, "s23", <SlideNextSteps {...shared} num={23} />],
    [24, "s24", <SlideClosing {...shared} num={24} />],
  ];

  return (
    <>
      {slides.map(([n, id, el]) => {
        const host = document.getElementById(id);
        return host ? ReactDOM.createPortal(el, host) : null;
      })}

      {typeof TweaksPanel !== "undefined" && (
        <TweaksPanel title="Tweaks">
          <TweakSection title="Brand">
            <TweakColor label="Accent color" value={tweaks.accent} onChange={v => setTweaks({ accent: v })} />
            <TweakText label="Brand name" value={tweaks.brandName} onChange={v => setTweaks({ brandName: v })} />
          </TweakSection>
          <TweakSection title="Client">
            <TweakText label="Client (日本語)" value={tweaks.clientName} onChange={v => setTweaks({ clientName: v })} />
            <TweakText label="Client (English)" value={tweaks.clientNameEn} onChange={v => setTweaks({ clientNameEn: v })} />
            <TweakText label="Date" value={tweaks.date} onChange={v => setTweaks({ date: v })} />
            <TweakText label="Presenter" value={tweaks.presenter} onChange={v => setTweaks({ presenter: v })} />
          </TweakSection>
          <TweakSection title="Accent presets">
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {[
                { name: "Coral (default)", c: "#E63946" },
                { name: "Hinomaru red", c: "#BC002D" },
                { name: "Indigo accent", c: "#3D5AFE" },
                { name: "Teal", c: "#0EA5A5" },
                { name: "Amber", c: "#D97706" },
              ].map(p => (
                <button key={p.c} onClick={() => setTweaks({ accent: p.c })} style={{
                  padding: "8px 12px", borderRadius: 8, border: "1px solid #ddd",
                  background: tweaks.accent === p.c ? p.c : "#fff",
                  color: tweaks.accent === p.c ? "#fff" : "#333",
                  fontSize: 12, fontWeight: 600, cursor: "pointer",
                  display: "flex", alignItems: "center", gap: 8,
                }}>
                  <span style={{ width: 12, height: 12, borderRadius: "50%", background: p.c, border: "1px solid rgba(0,0,0,0.15)" }} />
                  {p.name}
                </button>
              ))}
            </div>
          </TweakSection>
        </TweaksPanel>
      )}
    </>
  );
}

// Wait for all scripts to finish, then mount
function mount() {
  if (typeof SlideCover === "undefined" || typeof TweaksPanel === "undefined") {
    return setTimeout(mount, 50);
  }
  const root = document.getElementById("tweaks-root");
  ReactDOM.createRoot(root).render(<App />);
}
mount();
