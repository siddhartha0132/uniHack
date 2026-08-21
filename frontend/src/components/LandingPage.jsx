import { useEffect, useRef, useState } from "react";

/* ─── Tiny helpers ────────────────────────────────────────────────────── */
function useAnimationFrame(cb) {
  const ref = useRef();
  useEffect(() => {
    let id;
    const loop = (t) => { cb(t); id = requestAnimationFrame(loop); };
    id = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(id);
  }, [cb]);
}

/* ─── Particle field (canvas, pure JS – no libraries) ────────────────── */
function ParticleField() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    let W, H, particles = [];

    const COLORS = ["#3FC1A9", "#52D9BE", "#E8A33D", "#E05C3A", "#7A95A8"];

    const resize = () => {
      W = canvas.width  = canvas.offsetWidth;
      H = canvas.height = canvas.offsetHeight;
    };
    resize();
    window.addEventListener("resize", resize);

    for (let i = 0; i < 90; i++) {
      particles.push({
        x: Math.random() * W,
        y: Math.random() * H,
        r: Math.random() * 1.6 + 0.4,
        dx: (Math.random() - 0.5) * 0.3,
        dy: (Math.random() - 0.5) * 0.3,
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        alpha: Math.random() * 0.5 + 0.15,
      });
    }

    let mouse = { x: -9999, y: -9999 };
    const handleMouseMove = (e) => {
      const r = canvas.getBoundingClientRect();
      mouse = { x: e.clientX - r.left, y: e.clientY - r.top };
    };
    canvas.parentElement.addEventListener("mousemove", handleMouseMove);

    let raf;
    const draw = () => {
      ctx.clearRect(0, 0, W, H);
      particles.forEach((p) => {
        p.x += p.dx; p.y += p.dy;
        if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
        if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;

        const mdx = p.x - mouse.x, mdy = p.y - mouse.y;
        const md  = Math.sqrt(mdx * mdx + mdy * mdy);
        if (md < 100) { p.x += mdx / md * 1.2; p.y += mdy / md * 1.2; }

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = p.alpha;
        ctx.fill();
      });

      ctx.globalAlpha = 1;
      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const d  = Math.sqrt(dx * dx + dy * dy);
          if (d < 100) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            ctx.strokeStyle = `rgba(63,193,169,${0.12 * (1 - d / 100)})`;
            ctx.lineWidth = 0.6;
            ctx.stroke();
          }
        }
      }
      raf = requestAnimationFrame(draw);
    };
    draw();
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", resize);
      if (canvas.parentElement) canvas.parentElement.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  return <canvas ref={canvasRef} style={{ position: "absolute", inset: 0, width: "100%", height: "100%", zIndex: 0 }} />;
}

/* ─── 3-D floating card ───────────────────────────────────────────────── */
function Card3D({ icon, title, label, accentColor, delay = 0, children }) {
  const ref = useRef(null);

  const handleMouseMove = (e) => {
    const el = ref.current;
    const rect = el.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width  - 0.5) * 2;
    const y = ((e.clientY - rect.top)  / rect.height - 0.5) * 2;
    el.style.transform = `perspective(700px) rotateY(${x * 14}deg) rotateX(${-y * 14}deg) scale(1.04)`;
    el.style.boxShadow = `0 24px 64px rgba(0,0,0,0.6), 0 0 40px ${accentColor}22, inset 0 1px 0 rgba(255,255,255,0.06)`;
  };
  const handleMouseLeave = () => {
    if (ref.current) {
      ref.current.style.transform = "perspective(700px) rotateY(0) rotateX(0) scale(1)";
      ref.current.style.boxShadow = "";
    }
  };

  return (
    <div
      ref={ref}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{
        position: "relative", overflow: "hidden",
        width: 210, padding: "24px 20px",
        background: "linear-gradient(145deg, #141B23, #0D1520)",
        border: "1px solid #1D2A38",
        borderRadius: 16,
        transition: "transform 0.2s cubic-bezier(0.16,1,0.3,1), box-shadow 0.25s",
        cursor: "default",
        animation: `floatIn 0.8s cubic-bezier(0.16,1,0.3,1) ${delay}ms both`,
        "--accent": accentColor,
      }}
    >
      <div style={{
        fontFamily: "'IBM Plex Mono', monospace", fontSize: 9, letterSpacing: "0.12em",
        textTransform: "uppercase", color: accentColor,
        background: `${accentColor}15`, border: `1px solid ${accentColor}40`,
        padding: "3px 10px", borderRadius: 99, width: "fit-content", marginBottom: 16,
      }}>{label}</div>
      <div style={{
        width: 52, height: 52, borderRadius: 12,
        background: "rgba(255,255,255,0.04)",
        display: "flex", alignItems: "center", justifyContent: "center",
        fontSize: 26, marginBottom: 14,
        boxShadow: `0 8px 24px ${accentColor}30`,
      }}>{icon}</div>
      <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 8 }}>{title}</div>
      <div style={{ fontSize: 12, color: "#7A95A8", lineHeight: 1.6, fontFamily: "'IBM Plex Mono', monospace" }}>{children}</div>
    </div>
  );
}

/* ─── Animated terminal ──────────────────────────────────────────────── */
const TERMINAL_LINES = [
  { delay: 0,    text: "$ veritas ingest --sources datasheet.pdf,erp.csv,web",  color: "#7A95A8" },
  { delay: 800,  text: "✓ Extracting attributes from 3 sources...",              color: "#3FC1A9" },
  { delay: 1500, text: "⚡ CONFLICT: supply_voltage",                             color: "#E8A33D" },
  { delay: 2300, text: "  datasheet: 24 VDC  |  erp: 24-28V  |  web: 24VDC",   color: "#4A606E" },
  { delay: 3100, text: "→ Resolved → datasheet (reliability: 0.95) ✓",          color: "#3FC1A9" },
  { delay: 3900, text: "✓ ETIM EC002542 · ECLASS 27-37-16-01 · UNSPSC 43211900", color: "#3FC1A9" },
  { delay: 4700, text: "✓ Quality score: 87/100  ·  1 attribute needs review",   color: "#52D9BE" },
  { delay: 5500, text: "✓ Record saved — ready for export (JSON / Akeneo CSV)", color: "#3FC1A9" },
];

function Terminal() {
  const [visible, setVisible] = useState([]);
  const [key, setKey] = useState(0);

  useEffect(() => {
    setVisible([]);
    const timers = TERMINAL_LINES.map((l, i) =>
      setTimeout(() => setVisible((v) => [...v, i]), l.delay + 300)
    );
    // loop
    const loop = setTimeout(() => setKey(k => k + 1), 8000);
    return () => { timers.forEach(clearTimeout); clearTimeout(loop); };
  }, [key]);

  return (
    <div style={{
      background: "#070D12", border: "1px solid #1D2A38",
      borderRadius: 12, overflow: "hidden",
      boxShadow: "0 32px 80px rgba(0,0,0,0.6), 0 0 40px rgba(63,193,169,0.06)",
    }}>
      <div style={{
        display: "flex", alignItems: "center", gap: 8,
        padding: "10px 14px", borderBottom: "1px solid #1D2A38",
        background: "rgba(20,27,35,0.5)",
      }}>
        {["#E05C3A","#E8A33D","#3FC1A9"].map((c,i) => (
          <span key={i} style={{ width: 10, height: 10, borderRadius: "50%", background: c, display: "block" }} />
        ))}
        <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, color: "#4A606E", marginLeft: 6 }}>
          veritas — arbitration engine
        </span>
        <span style={{
          marginLeft: "auto", fontFamily: "'IBM Plex Mono', monospace", fontSize: 9,
          color: "#3FC1A9", letterSpacing: "0.15em", display: "flex", alignItems: "center", gap: 5,
        }}>
          <span style={{
            width: 6, height: 6, borderRadius: "50%", background: "#3FC1A9",
            boxShadow: "0 0 8px #3FC1A9", display: "block", animation: "lp-pulse 1.5s infinite",
          }} />
          LIVE
        </span>
      </div>
      <div style={{ padding: "16px 20px", fontFamily: "'IBM Plex Mono', monospace", fontSize: 12.5, lineHeight: 1.8, minHeight: 230 }}>
        {TERMINAL_LINES.map((l, i) =>
          visible.includes(i) ? (
            <div key={i} style={{ color: l.color, animation: "lp-fadeUp 0.3s ease both" }}>
              {l.text}
            </div>
          ) : null
        )}
        <span style={{
          display: "inline-block", width: 8, height: 14,
          background: "#3FC1A9", verticalAlign: "middle", marginLeft: 2,
          animation: "lp-blink 1s step-end infinite",
        }} />
      </div>
    </div>
  );
}

/* ─── Pipeline step ───────────────────────────────────────────────────── */
function Step({ n, title, desc, color }) {
  return (
    <div style={{
      display: "flex", gap: 16, alignItems: "flex-start",
      padding: 18, borderRadius: 12,
      background: "rgba(20,27,35,0.5)", border: "1px solid #17222E",
      transition: "border-color 0.2s",
    }}
      onMouseEnter={e => e.currentTarget.style.borderColor = "#3FC1A9"}
      onMouseLeave={e => e.currentTarget.style.borderColor = "#17222E"}
    >
      <div style={{
        width: 32, height: 32, borderRadius: 8, flexShrink: 0,
        display: "flex", alignItems: "center", justifyContent: "center",
        fontFamily: "'IBM Plex Mono', monospace", fontSize: 12, fontWeight: 700,
        background: `${color}18`, border: `1px solid ${color}44`, color,
      }}>{n}</div>
      <div>
        <div style={{ fontSize: 13, fontWeight: 700, marginBottom: 4 }}>{title}</div>
        <div style={{ fontSize: 12, color: "#7A95A8", fontFamily: "'IBM Plex Mono', monospace", lineHeight: 1.5 }}>{desc}</div>
      </div>
    </div>
  );
}

/* ─── StatPill ───────────────────────────────────────────────────── */
function StatPill({ value, label, color }) {
  return (
    <div style={{
      display: "flex", flexDirection: "column", alignItems: "center",
      padding: "18px 28px", borderRight: "1px solid #17222E", gap: 4,
    }}>
      <span style={{ fontSize: 26, fontWeight: 800, lineHeight: 1, color }}>{value}</span>
      <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 10, letterSpacing: "0.1em", color: "#4A606E", textTransform: "uppercase" }}>{label}</span>
    </div>
  );
}

/* ─── MAIN LANDING ──────────────────────────────────────────────────── */
export default function LandingPage({ onEnterApp }) {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 40);
    window.addEventListener("scroll", onScroll);
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const scrollTo = (id) => document.getElementById(id)?.scrollIntoView({ behavior: "smooth" });

  const navStyle = {
    position: "fixed", top: 0, left: 0, right: 0, zIndex: 100,
    display: "flex", alignItems: "center", justifyContent: "space-between",
    padding: "14px 40px",
    transition: "background 0.4s, backdrop-filter 0.4s",
    ...(scrolled ? {
      background: "rgba(8,13,18,0.88)",
      backdropFilter: "blur(14px)",
      WebkitBackdropFilter: "blur(14px)",
      borderBottom: "1px solid #17222E",
    } : {}),
  };

  return (
    <div style={{
      background: "#080D12", color: "#E4ECF2",
      fontFamily: "'Space Grotesk', sans-serif",
      minHeight: "100vh", overflowX: "hidden",
    }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=IBM+Plex+Mono:wght@400;500&display=swap');
        @keyframes lp-fadeUp { from { opacity:0; transform:translateY(20px) } to { opacity:1; transform:none } }
        @keyframes lp-floatIn { from { opacity:0; transform:translateY(40px) scale(0.9) } to { opacity:1; transform:none } }
        @keyframes lp-pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        @keyframes lp-blink { 0%,100%{opacity:1} 50%{opacity:0} }
        .lp-cta-big:hover .lp-arrow { transform: translateX(5px); }
        .lp-prob-card:hover { border-color: rgba(63,193,169,0.25) !important; }
      `}</style>

      {/* NAV */}
      <nav style={navStyle}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, fontWeight: 800, fontSize: 18, letterSpacing: "0.08em" }}>
          <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#3FC1A9", boxShadow: "0 0 10px #3FC1A9", display: "block" }} />
          VERITAS
        </div>
        <div style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 10, letterSpacing: "0.1em", padding: "4px 14px", borderRadius: 99, border: "1px solid #1D2A38", color: "#7A95A8", background: "rgba(20,27,35,0.6)" }}>
          uniHack 2026 · Industrial PIM Intelligence
        </div>
        <button onClick={onEnterApp} style={{
          display: "inline-flex", alignItems: "center", gap: 8,
          padding: "9px 22px", borderRadius: 8, fontWeight: 700, fontSize: 13,
          background: "#3FC1A9", color: "#051210", border: "none", cursor: "pointer",
          transition: "background 0.2s, transform 0.15s", fontFamily: "'Space Grotesk', sans-serif",
        }}
          onMouseEnter={e => { e.currentTarget.style.background = "#52D9BE"; e.currentTarget.style.transform = "translateY(-1px)"; }}
          onMouseLeave={e => { e.currentTarget.style.background = "#3FC1A9"; e.currentTarget.style.transform = "none"; }}
        >
          Open App →
        </button>
      </nav>

      {/* HERO */}
      <section id="top" style={{
        position: "relative", minHeight: "100vh",
        display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
        textAlign: "center", padding: "100px 24px 60px", overflow: "hidden",
      }}>
        <ParticleField />
        {/* glow */}
        <div style={{ position: "absolute", top: "10%", left: "50%", transform: "translateX(-50%)", width: 800, height: 400, background: "radial-gradient(ellipse at center, rgba(63,193,169,0.1) 0%, transparent 70%)", pointerEvents: "none", zIndex: 0 }} />

        {/* eyebrow */}
        <div style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, letterSpacing: "0.15em", color: "#3FC1A9", textTransform: "uppercase", display: "flex", alignItems: "center", gap: 12, marginBottom: 24, position: "relative", zIndex: 1, animation: "lp-fadeUp 0.8s ease both" }}>
          <span style={{ height: 1, width: 50, background: "linear-gradient(to right, transparent, #3FC1A9)" }} />
          AI-Powered Product Intelligence
          <span style={{ height: 1, width: 50, background: "linear-gradient(to left, transparent, #3FC1A9)" }} />
        </div>

        {/* h1 */}
        <h1 style={{
          fontSize: "clamp(38px, 6vw, 78px)", fontWeight: 800, lineHeight: 1.05,
          background: "linear-gradient(160deg, #ECF2F7 0%, #7A95A8 60%, #3FC1A9 100%)",
          WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
          marginBottom: 0, position: "relative", zIndex: 1,
          animation: "lp-fadeUp 0.9s ease both",
        }}>
          Industrial Product Data
        </h1>
        <h1 style={{
          fontSize: "clamp(38px, 6vw, 78px)", fontWeight: 800, lineHeight: 1.05,
          background: "linear-gradient(90deg, #3FC1A9, #52D9BE, #E8A33D)",
          WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text",
          marginBottom: 20, position: "relative", zIndex: 1,
          animation: "lp-fadeUp 0.9s 0.1s ease both",
        }}>
          Is Broken. We Fixed It.
        </h1>

        <p style={{ maxWidth: 620, fontSize: 17, color: "#7A95A8", lineHeight: 1.7, margin: "0 auto 36px", position: "relative", zIndex: 1, animation: "lp-fadeUp 0.9s 0.2s ease both" }}>
          Manufacturers lose <strong style={{ color: "#E8A33D" }}>thousands of hours</strong> reconciling
          conflicting specs across datasheets, ERPs, and websites. Veritas automatically
          extracts, arbitrates, and verifies — turning chaos into a single, trusted product record.
        </p>

        {/* CTAs */}
        <div style={{ display: "flex", alignItems: "center", gap: 16, justifyContent: "center", position: "relative", zIndex: 1, animation: "lp-fadeUp 0.9s 0.3s ease both" }}>
          <button onClick={onEnterApp} style={{
            display: "inline-flex", alignItems: "center", gap: 10,
            padding: "14px 32px", borderRadius: 10, fontWeight: 700, fontSize: 15,
            background: "#3FC1A9", color: "#051210", border: "none", cursor: "pointer",
            transition: "all 0.2s", fontFamily: "'Space Grotesk', sans-serif",
            boxShadow: "0 0 30px rgba(63,193,169,0.3)",
          }}
            onMouseEnter={e => { e.currentTarget.style.background = "#52D9BE"; e.currentTarget.style.transform = "translateY(-2px)"; e.currentTarget.style.boxShadow = "0 0 50px rgba(63,193,169,0.5)"; }}
            onMouseLeave={e => { e.currentTarget.style.background = "#3FC1A9"; e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "0 0 30px rgba(63,193,169,0.3)"; }}
          >
            🚀 Launch Demo App →
          </button>
          <button onClick={() => scrollTo("pipeline")} style={{
            display: "inline-flex", alignItems: "center", gap: 8,
            padding: "13px 24px", borderRadius: 10, fontWeight: 600, fontSize: 14,
            background: "transparent", color: "#7A95A8", border: "1px solid #1D2A38", cursor: "pointer",
            transition: "all 0.2s", fontFamily: "'Space Grotesk', sans-serif",
          }}
            onMouseEnter={e => { e.currentTarget.style.borderColor = "#3FC1A9"; e.currentTarget.style.color = "#3FC1A9"; }}
            onMouseLeave={e => { e.currentTarget.style.borderColor = "#1D2A38"; e.currentTarget.style.color = "#7A95A8"; }}
          >
            See How It Works ↓
          </button>
        </div>

        {/* Stats bar */}
        <div style={{
          display: "flex", justifyContent: "center", marginTop: 48, position: "relative", zIndex: 1,
          animation: "lp-fadeUp 0.9s 0.45s ease both",
          background: "rgba(20,27,35,0.6)", backdropFilter: "blur(12px)", WebkitBackdropFilter: "blur(12px)",
          border: "1px solid #17222E", borderRadius: 14, overflow: "hidden", width: "fit-content", maxWidth: "100%",
        }}>
          <StatPill value="3×" label="Source Types" color="#3FC1A9" />
          <StatPill value="87%" label="Quality Score" color="#52D9BE" />
          <StatPill value="100%" label="Conflicts Resolved" color="#E8A33D" />
          <StatPill value="&lt;1s" label="Pipeline Time" color="#3FC1A9" />
        </div>

        {/* 3D Cards */}
        <div style={{ display: "flex", gap: 18, justifyContent: "center", flexWrap: "wrap", padding: "56px 24px 0", position: "relative", zIndex: 1, animation: "lp-fadeUp 0.9s 0.55s ease both" }}>
          <Card3D icon="📄" title="Multi-Source Ingest" label="EXTRACT" accentColor="#3FC1A9" delay={0}>
            PDF datasheets, ERP CSVs, web pages, image labels — all ingested automatically.
          </Card3D>
          <Card3D icon="⚖️" title="Conflict Arbitration" label="ARBITRATE" accentColor="#E8A33D" delay={100}>
            Weighted reliability scoring resolves contradictions with a full evidence trail.
          </Card3D>
          <Card3D icon="🏷️" title="Auto Classification" label="CLASSIFY" accentColor="#52D9BE" delay={200}>
            Auto-maps to ETIM, ECLASS, UNSPSC codes — required by every industrial marketplace.
          </Card3D>
          <Card3D icon="🔍" title="Human Review Loop" label="VERIFY" accentColor="#E05C3A" delay={300}>
            Low-confidence attributes flagged for expert review. Corrections improve future runs.
          </Card3D>
        </div>
      </section>

      {/* DIVIDER */}
      <div style={{ height: 1, maxWidth: 1100, margin: "0 auto", background: "linear-gradient(to right, transparent, #1D2A38, transparent)" }} />

      {/* PROBLEM / SOLUTION */}
      <section style={{ maxWidth: 1100, margin: "0 auto", padding: "100px 24px" }}>
        <div style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 10, letterSpacing: "0.15em", color: "#3FC1A9", textTransform: "uppercase", marginBottom: 16 }}>The Problem Statement</div>
        <h2 style={{ fontSize: "clamp(28px, 4vw, 50px)", fontWeight: 800, lineHeight: 1.1, marginBottom: 16 }}>
          $500B Market.<br />
          <span style={{ color: "#3FC1A9" }}>Still Managed in Spreadsheets.</span>
        </h2>
        <p style={{ fontSize: 16, color: "#7A95A8", maxWidth: 580, lineHeight: 1.7, marginBottom: 48 }}>
          Industrial manufacturers manage tens of thousands of SKUs — each with conflicting spec sheets,
          outdated ERP entries, and unreliable web pages. There is no single source of truth.
        </p>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
          {/* Problem card */}
          <div className="lp-prob-card" style={{ background: "linear-gradient(145deg, rgba(14,20,28,0.9), rgba(8,12,18,0.6))", border: "1px solid #1D2A38", borderRadius: 14, padding: 28, transition: "border-color 0.2s" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20, fontSize: 13, fontWeight: 700 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#E05C3A", display: "block" }} />
              Before Veritas — The Pain
            </div>
            <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 12 }}>
              {[
                "3 sources say 3 different voltages for the same PLC",
                "Manual reconciliation takes days per product family",
                "No auditability — who changed what and why?",
                "ETIM / ECLASS codes applied inconsistently or not at all",
                "Errors propagate to customer portals causing returns",
                "Domain knowledge locked in individual engineers' heads",
              ].map((t, i) => (
                <li key={i} style={{ display: "flex", gap: 10, fontSize: 13.5, color: "#7A95A8", fontFamily: "'IBM Plex Mono', monospace", lineHeight: 1.5 }}>
                  <span style={{ color: "#4A606E", flexShrink: 0 }}>//</span> {t}
                </li>
              ))}
            </ul>
          </div>

          {/* Solution card */}
          <div className="lp-prob-card" style={{ background: "linear-gradient(145deg, rgba(14,20,28,0.9), rgba(8,12,18,0.6))", border: "1px solid rgba(63,193,169,0.2)", borderRadius: 14, padding: 28, transition: "border-color 0.2s" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20, fontSize: 13, fontWeight: 700 }}>
              <span style={{ width: 8, height: 8, borderRadius: "50%", background: "#3FC1A9", display: "block" }} />
              After Veritas — The Solution
            </div>
            <ul style={{ listStyle: "none", display: "flex", flexDirection: "column", gap: 12 }}>
              {[
                "Arbitration engine resolves conflicts via source reliability weighting",
                "Full evidence ledger — every value traceable to its source snippet",
                "Human review loop for low-confidence attributes with full audit trail",
                "Auto ETIM / ECLASS / UNSPSC mapping for marketplace readiness",
                "Learned reliability weights improve automatically from reviewer feedback",
                "Export to JSON or Akeneo CSV in one click",
              ].map((t, i) => (
                <li key={i} style={{ display: "flex", gap: 10, fontSize: 13.5, color: "#7A95A8", fontFamily: "'IBM Plex Mono', monospace", lineHeight: 1.5 }}>
                  <span style={{ color: "#3FC1A9", flexShrink: 0 }}>✓</span> {t}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* DIVIDER */}
      <div style={{ height: 1, maxWidth: 1100, margin: "0 auto", background: "linear-gradient(to right, transparent, #1D2A38, transparent)" }} />

      {/* PIPELINE + TERMINAL */}
      <section id="pipeline" style={{ background: "linear-gradient(180deg, #080D12 0%, #0C1117 100%)", padding: "80px 24px" }}>
        <div style={{ maxWidth: 980, margin: "0 auto", display: "grid", gridTemplateColumns: "1fr 1.4fr", gap: 48, alignItems: "center" }}>
          <div>
            <div style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 10, letterSpacing: "0.15em", color: "#3FC1A9", textTransform: "uppercase", marginBottom: 16 }}>Live Pipeline</div>
            <h2 style={{ fontSize: "clamp(24px,3vw,40px)", fontWeight: 800, lineHeight: 1.15, marginBottom: 32 }}>
              Watch the<br />
              <span style={{ color: "#3FC1A9" }}>Arbitration Engine</span><br />
              in Action
            </h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              <Step n="01" title="Ingest"         color="#3FC1A9"  desc="PDF, CSV, plain text, images — accepted via drag-and-drop or API." />
              <Step n="02" title="Extract"        color="#52D9BE"  desc="Regex + LLM fallback pulls structured attributes from raw content." />
              <Step n="03" title="Arbitrate"      color="#E8A33D"  desc="Source reliability weights decide which value wins when sources disagree." />
              <Step n="04" title="Classify"       color="#3FC1A9"  desc="Product mapped to ETIM / ECLASS / UNSPSC taxonomy automatically." />
              <Step n="05" title="Score & Review" color="#E05C3A"  desc="Quality score computed. Unresolved conflicts routed to human reviewers." />
            </div>
          </div>
          <Terminal />
        </div>
      </section>

      {/* DIVIDER */}
      <div style={{ height: 1, maxWidth: 1100, margin: "0 auto", background: "linear-gradient(to right, transparent, #1D2A38, transparent)" }} />

      {/* BIG CTA */}
      <section style={{ textAlign: "center", padding: "120px 24px", background: "radial-gradient(ellipse at center bottom, rgba(63,193,169,0.07) 0%, transparent 60%)" }}>
        <div style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 10, letterSpacing: "0.15em", color: "#3FC1A9", textTransform: "uppercase", marginBottom: 16 }}>Ready to See It Live?</div>
        <h2 style={{ fontSize: "clamp(32px,5vw,62px)", fontWeight: 800, marginBottom: 20 }}>
          One Pipeline.<br />
          <span style={{ background: "linear-gradient(90deg,#3FC1A9,#E8A33D)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent" }}>
            One Source of Truth.
          </span>
        </h2>
        <p style={{ fontSize: 16, color: "#7A95A8", marginBottom: 40, maxWidth: 540, margin: "0 auto 40px" }}>
          Load the demo dataset — a real Siemens SIMATIC S7-1200 with three genuinely
          conflicting source documents — and watch Veritas resolve every conflict in under a second.
        </p>
        <button className="lp-cta-big" onClick={onEnterApp} style={{
          display: "inline-flex", alignItems: "center", gap: 14,
          padding: "18px 44px", borderRadius: 14, fontSize: 17, fontWeight: 800,
          background: "linear-gradient(135deg, #3FC1A9 0%, #52D9BE 50%, #E8A33D 100%)",
          color: "#051210", border: "none", cursor: "pointer",
          transition: "transform 0.2s, box-shadow 0.2s", fontFamily: "'Space Grotesk', sans-serif",
          boxShadow: "0 0 60px rgba(63,193,169,0.3)",
        }}
          onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-3px) scale(1.02)"; e.currentTarget.style.boxShadow = "0 0 80px rgba(63,193,169,0.5)"; }}
          onMouseLeave={e => { e.currentTarget.style.transform = "none"; e.currentTarget.style.boxShadow = "0 0 60px rgba(63,193,169,0.3)"; }}
        >
          Open Veritas App
          <span className="lp-arrow" style={{ fontSize: 22, transition: "transform 0.2s", display: "inline-block" }}>→</span>
        </button>
        <div style={{ marginTop: 16, fontFamily: "'IBM Plex Mono', monospace", fontSize: 12, color: "#4A606E" }}>
          Log in with demo / demo123 · then click "Run Demo Pipeline"
        </div>
      </section>

      {/* FOOTER */}
      <footer style={{ textAlign: "center", padding: "32px 24px", borderTop: "1px solid #17222E", fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, color: "#4A606E" }}>
        VERITAS · Industrial Product Intelligence · Built for uniHack 2026 ·
        Stack: FastAPI · React · SQLite · Python · Vite
      </footer>
    </div>
  );
}
