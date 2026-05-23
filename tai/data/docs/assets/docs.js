/* ── tai docs — runtime ──────────────────────────────────────────────────
   Handles: sidebar navigation, client-side validation, hot reload via SSE.
   Injected by every doc via <script src="_assets/docs.js"></script>.
   ────────────────────────────────────────────────────────────────────── */

(function () {
  "use strict";

  /* ── Validation schemas ────────────────────────────────────────────── */

  const SCHEMAS = {
    intent: {
      required: ["context", "problem", "solution", "success-criteria"],
      meta: ["date"],
    },
    decision: {
      required: ["context", "decision", "consequences"],
      meta: ["date"],
    },
    design: {
      required: ["overview", "components"],
      meta: ["date"],
    },
    spec: {
      required: ["overview", "requirements"],
      meta: ["date"],
    },
    guide: {
      required: ["overview"],
      meta: ["date"],
    },
    plan: {
      required: ["phases"],
      meta: ["date"],
    },
    review: {
      required: ["findings"],
      meta: ["date"],
    },
    trace: {
      required: [],
      meta: ["date"],
    },
    changelog: {
      required: [],
      meta: ["date"],
    },
  };

  /* ── Helpers ───────────────────────────────────────────────────────── */

  function getMeta(name) {
    const el = document.querySelector(`meta[name="doc-${name}"]`);
    return el ? el.content : null;
  }

  function isServed() {
    return location.protocol.startsWith("http");
  }

  /* ── Navigation sidebar ────────────────────────────────────────────── */

  function buildNav() {
    if (!isServed()) return;

    fetch("/_api/docs")
      .then((r) => (r.ok ? r.json() : Promise.reject()))
      .then((docs) => {
        const nav = document.createElement("nav");
        nav.className = "docs-nav";

        const title = document.createElement("div");
        title.className = "nav-title";
        title.textContent = "Docs";
        nav.appendChild(title);

        const groups = {};
        docs.forEach((doc) => {
          const parts = doc.path.split("/");
          const group = parts.length > 1 ? parts.slice(0, -1).join("/") : "";
          if (!groups[group]) groups[group] = [];
          groups[group].push(doc);
        });

        const currentPath = location.pathname.replace(/^\//, "");

        Object.keys(groups)
          .sort()
          .forEach((group) => {
            if (group) {
              const heading = document.createElement("div");
              heading.className = "nav-group";
              heading.textContent = group.replace(/\//g, " / ");
              nav.appendChild(heading);
            }

            groups[group]
              .sort((a, b) => a.title.localeCompare(b.title))
              .forEach((item) => {
                const a = document.createElement("a");
                a.href = "/" + item.path;
                a.className = "nav-link";
                a.textContent = item.title;
                if (currentPath === item.path) a.classList.add("active");
                nav.appendChild(a);
              });
          });

        document.body.prepend(nav);
        document.body.classList.add("has-nav");
      })
      .catch(() => {
        /* not served via tai docs serve — skip nav */
      });
  }

  /* ── Client-side validation ────────────────────────────────────────── */

  function validateDoc() {
    const article = document.querySelector("article");
    if (!article) return;

    const issues = [];
    const docType = getMeta("type");
    const docDate = getMeta("date");

    if (!document.title || document.title === "Untitled") {
      issues.push("Missing <title>");
    }
    if (!docType) {
      issues.push('Missing <meta name="doc-type">');
    }
    if (!docDate) {
      issues.push('Missing <meta name="doc-date">');
    }

    const schema = SCHEMAS[docType];
    if (schema) {
      schema.required.forEach((section) => {
        const el = article.querySelector(`[data-section="${section}"]`);
        if (!el) {
          issues.push(`Missing section: ${section}`);
        }
      });

      schema.meta.forEach((field) => {
        if (!getMeta(field)) {
          issues.push(`Missing meta: doc-${field}`);
        }
      });
    } else if (docType) {
      issues.push(`Unknown doc-type: ${docType}`);
    }

    /* check internal links */
    document.querySelectorAll("a[href]").forEach((a) => {
      const href = a.getAttribute("href");
      if (
        href.startsWith("#") ||
        href.startsWith("http") ||
        href.startsWith("mailto:")
      )
        return;
      /* mark for visual feedback — server validates reachability */
      a.dataset.internalLink = "true";
    });

    showValidationBadge(issues);
    return issues;
  }

  function showValidationBadge(issues) {
    const badge = document.createElement("div");
    badge.className =
      "validation-badge " + (issues.length ? "validation-fail" : "validation-pass");
    badge.textContent = issues.length
      ? `${issues.length} issue${issues.length !== 1 ? "s" : ""}`
      : "\u2713 Valid";

    const panel = document.createElement("div");
    panel.className = "validation-panel";
    if (issues.length) {
      issues.forEach((msg) => {
        const div = document.createElement("div");
        div.className = "issue";
        div.textContent = msg;
        panel.appendChild(div);
      });
    } else {
      const div = document.createElement("div");
      div.style.color = "var(--success)";
      div.textContent = "All validation checks passed.";
      panel.appendChild(div);
    }

    badge.addEventListener("click", () => panel.classList.toggle("open"));
    document.addEventListener("click", (e) => {
      if (!badge.contains(e.target) && !panel.contains(e.target)) {
        panel.classList.remove("open");
      }
    });

    document.body.appendChild(panel);
    document.body.appendChild(badge);
  }

  /* ── Hot reload via SSE ────────────────────────────────────────────── */

  function connectHotReload() {
    if (!isServed()) return;

    let es;
    function connect() {
      es = new EventSource("/_events");
      es.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          if (data.type === "reload") location.reload();
        } catch (_) {
          /* ignore parse errors */
        }
      };
      es.onerror = () => {
        es.close();
        setTimeout(connect, 2000);
      };
    }
    connect();
  }

  /* ── Auto-generate metadata display ────────────────────────────────── */

  function renderMeta() {
    const article = document.querySelector("article");
    if (!article) return;
    /* skip if author already placed a dl.meta */
    if (article.querySelector("dl.meta")) return;

    const fields = ["type", "date", "author"];
    const entries = fields
      .map((f) => [f, getMeta(f)])
      .filter(([, v]) => v);

    if (!entries.length) return;

    const dl = document.createElement("dl");
    dl.className = "meta";
    entries.forEach(([key, val]) => {
      const dt = document.createElement("dt");
      dt.textContent = key;
      const dd = document.createElement("dd");
      dd.textContent = val;
      dl.appendChild(dt);
      dl.appendChild(dd);
    });

    /* insert after first h1 */
    const h1 = article.querySelector("h1");
    if (h1 && h1.nextSibling) {
      h1.parentNode.insertBefore(dl, h1.nextSibling);
    } else {
      article.prepend(dl);
    }
  }

  /* ── Theme toggle ───────────────────────────────────────────────────── */

  function initTheme() {
    const saved = localStorage.getItem("tai-docs-theme");
    if (saved === "dark") document.documentElement.setAttribute("data-theme", "dark");

    const btn = document.createElement("button");
    btn.className = "theme-toggle";
    btn.setAttribute("aria-label", "Toggle dark mode");
    btn.textContent = isDark() ? "\u2600" : "\u263E";
    btn.addEventListener("click", () => {
      const dark = !isDark();
      document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
      localStorage.setItem("tai-docs-theme", dark ? "dark" : "light");
      btn.textContent = dark ? "\u2600" : "\u263E";
    });
    document.body.appendChild(btn);
  }

  function isDark() {
    return document.documentElement.getAttribute("data-theme") === "dark";
  }

  /* ── Font loading ─────────────────────────────────────────────────── */

  function loadFonts() {
    if (document.querySelector('link[data-tai-fonts]')) return;
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.dataset.taiFonts = "true";
    link.href =
      "https://fonts.googleapis.com/css2?family=VT323&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,700;1,8..60,400&family=JetBrains+Mono:wght@400;500;600&display=swap";
    document.head.appendChild(link);
  }

  /* ── Init ──────────────────────────────────────────────────────────── */

  document.addEventListener("DOMContentLoaded", () => {
    loadFonts();
    renderMeta();
    buildNav();
    validateDoc();
    connectHotReload();
    initTheme();
  });
})();
