/* ── tai docs — runtime ──────────────────────────────────────────────────
   Simple: fetch file tree from server, build sidebar, search, navigate.
   All links absolute. No broken paths.
   ────────────────────────────────────────────────────────────────────── */

(function () {
  "use strict";

  var served = location.protocol.startsWith("http");

  /* ── Sidebar ──────────────────────────────────────────────────────── */

  function buildSidebar() {
    /* try server API first, fall back to static index file */
    var urls = served
      ? ["/_api/docs", "_assets/_index.json"]
      : ["_assets/_index.json", "../_assets/_index.json"];

    fetchFirst(urls).then(function (docs) {
      if (!docs) return;
        var nav = document.createElement("nav");
        nav.className = "docs-nav";

        /* title */
        var title = document.createElement("a");
        title.className = "nav-title";
        title.href = "/";
        title.textContent = "Docs";
        nav.appendChild(title);

        /* search */
        var search = document.createElement("input");
        search.className = "nav-search";
        search.type = "text";
        search.placeholder = "Search...";
        search.addEventListener("input", function () {
          var q = search.value.toLowerCase();
          nav.querySelectorAll(".nav-link").forEach(function (a) {
            a.style.display = a.textContent.toLowerCase().includes(q) ? "" : "none";
          });
          nav.querySelectorAll(".nav-group").forEach(function (g) {
            var links = g.nextElementSibling;
            if (!links || !links.classList.contains("nav-group-items")) return;
            var anyVisible = false;
            links.querySelectorAll(".nav-link").forEach(function (a) {
              if (a.style.display !== "none") anyVisible = true;
            });
            g.style.display = anyVisible || !q ? "" : "none";
            links.style.display = anyVisible || !q ? "" : "none";
          });
        });
        nav.appendChild(search);

        /* back button — show parent dir */
        var current = location.pathname.replace(/^\//, "");
        var parts = current.split("/");
        if (parts.length > 1) {
          var back = document.createElement("a");
          back.className = "nav-back";
          back.href = "/" + parts.slice(0, -1).join("/") + "/";
          back.textContent = "\u2190 " + (parts.length > 2 ? parts[parts.length - 2] : "root");
          nav.appendChild(back);
        }

        /* build tree: group by first directory */
        var tree = {};
        docs.forEach(function (doc) {
          var segs = doc.path.split("/");
          var dir = segs.length > 1 ? segs[0] : "";
          if (!tree[dir]) tree[dir] = [];
          tree[dir].push(doc);
        });

        /* render root files first, then directories */
        var dirs = Object.keys(tree).sort(function (a, b) {
          if (a === "") return -1;
          if (b === "") return 1;
          return a.localeCompare(b);
        });

        dirs.forEach(function (dir) {
          if (dir) {
            var heading = document.createElement("div");
            heading.className = "nav-group";
            heading.textContent = dir;
            heading.addEventListener("click", function () {
              var items = heading.nextElementSibling;
              if (items) items.classList.toggle("collapsed");
              heading.classList.toggle("collapsed");
            });
            nav.appendChild(heading);

            var container = document.createElement("div");
            container.className = "nav-group-items";
            /* auto-expand current directory */
            if (!current.startsWith(dir + "/")) {
              container.classList.add("collapsed");
              heading.classList.add("collapsed");
            }

            tree[dir]
              .sort(function (a, b) { return a.title.localeCompare(b.title); })
              .forEach(function (doc) { container.appendChild(makeLink(doc, current)); });
            nav.appendChild(container);
          } else {
            tree[dir]
              .sort(function (a, b) { return a.title.localeCompare(b.title); })
              .forEach(function (doc) { nav.appendChild(makeLink(doc, current)); });
          }
        });

        document.body.prepend(nav);
        document.body.classList.add("has-nav");
      })
    });
  }

  function fetchFirst(urls) {
    var i = 0;
    function tryNext() {
      if (i >= urls.length) return Promise.resolve(null);
      return fetch(urls[i++])
        .then(function (r) { return r.ok ? r.json() : tryNext(); })
        .catch(function () { return tryNext(); });
    }
    return tryNext();
  }

  function makeLink(doc, current) {
    var a = document.createElement("a");
    a.href = "/" + doc.path;
    a.className = "nav-link";
    a.textContent = doc.title;
    if (current === doc.path) a.classList.add("active");
    if (doc.type) a.dataset.type = doc.type;
    return a;
  }

  /* ── Metadata display ─────────────────────────────────────────────── */

  function renderMeta() {
    var article = document.querySelector("article");
    if (!article || article.querySelector("dl.meta")) return;

    var docType = getMeta("type");
    var statusTypes = ["spec", "decision"];
    var fields = ["type", "status", "date", "author"];
    var entries = [];

    fields.forEach(function (f) {
      var v = getMeta(f);
      if (!v) return;
      if (f === "status" && statusTypes.indexOf(docType) === -1) return;
      entries.push([f, v]);
    });

    if (!entries.length) return;

    var dl = document.createElement("dl");
    dl.className = "meta";
    entries.forEach(function (pair) {
      var dt = document.createElement("dt");
      dt.textContent = pair[0];
      var dd = document.createElement("dd");
      if (pair[0] === "status") {
        var span = document.createElement("span");
        span.className = "status status-" + pair[1];
        span.textContent = pair[1];
        dd.appendChild(span);
      } else {
        dd.textContent = pair[1];
      }
      dl.appendChild(dt);
      dl.appendChild(dd);
    });

    var h1 = article.querySelector("h1");
    if (h1 && h1.nextSibling) h1.parentNode.insertBefore(dl, h1.nextSibling);
    else article.prepend(dl);
  }

  /* ── Validation ───────────────────────────────────────────────────── */

  var SCHEMAS = {
    intent:    { req: ["context", "problem", "solution", "success-criteria"], meta: ["date"] },
    decision:  { req: ["context", "decision", "consequences"], meta: ["date", "status"] },
    design:    { req: ["overview", "components"], meta: ["date"] },
    spec:      { req: ["problem", "requirements", "acceptance-criteria"], meta: ["date", "status"] },
    guide:     { req: ["overview"], meta: ["date"] },
    plan:      { req: ["phases"], meta: ["date"] },
    review:    { req: ["findings"], meta: ["date"] },
    trace:     { req: [], meta: ["date"] },
    changelog: { req: [], meta: ["date"] },
  };

  function validate() {
    var article = document.querySelector("article");
    if (!article) return;

    var issues = [];
    var docType = getMeta("type");

    if (!document.title || document.title === "Untitled") issues.push("Missing <title>");
    if (!docType) issues.push("Missing doc-type meta");
    if (!getMeta("date")) issues.push("Missing doc-date meta");

    var schema = SCHEMAS[docType];
    if (schema) {
      schema.req.forEach(function (s) {
        if (!article.querySelector('[data-section="' + s + '"]'))
          issues.push("Missing section: " + s);
      });
      schema.meta.forEach(function (m) {
        if (!getMeta(m)) issues.push("Missing meta: doc-" + m);
      });
    }

    /* badge */
    var badge = document.createElement("div");
    badge.className = "validation-badge " + (issues.length ? "validation-fail" : "validation-pass");
    badge.textContent = issues.length ? issues.length + " issue" + (issues.length > 1 ? "s" : "") : "\u2713 Valid";
    badge.title = issues.join("\n") || "All checks passed";

    var panel = document.createElement("div");
    panel.className = "validation-panel";
    issues.forEach(function (msg) {
      var div = document.createElement("div");
      div.className = "issue";
      div.textContent = msg;
      panel.appendChild(div);
    });
    if (!issues.length) {
      var ok = document.createElement("div");
      ok.style.color = "var(--success)";
      ok.textContent = "All checks passed.";
      panel.appendChild(ok);
    }

    badge.addEventListener("click", function () { panel.classList.toggle("open"); });
    document.addEventListener("click", function (e) {
      if (!badge.contains(e.target) && !panel.contains(e.target)) panel.classList.remove("open");
    });

    document.body.appendChild(panel);
    document.body.appendChild(badge);
  }

  /* ── Hot reload ───────────────────────────────────────────────────── */

  function hotReload() {
    if (!served) return;
    var es = new EventSource("/_events");
    es.onmessage = function (e) {
      try { if (JSON.parse(e.data).type === "reload") location.reload(); } catch (_) {}
    };
    es.onerror = function () { es.close(); setTimeout(hotReload, 2000); };
  }

  /* ── Theme ────────────────────────────────────────────────────────── */

  function initTheme() {
    if (localStorage.getItem("tai-docs-theme") === "dark")
      document.documentElement.setAttribute("data-theme", "dark");

    var btn = document.createElement("button");
    btn.className = "theme-toggle";
    btn.setAttribute("aria-label", "Toggle dark mode");
    btn.textContent = isDark() ? "\u2600" : "\u263E";
    btn.addEventListener("click", function () {
      var dark = !isDark();
      document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
      localStorage.setItem("tai-docs-theme", dark ? "dark" : "light");
      btn.textContent = dark ? "\u2600" : "\u263E";
    });
    document.body.appendChild(btn);
  }

  function isDark() { return document.documentElement.getAttribute("data-theme") === "dark"; }

  /* ── Fonts ────────────────────────────────────────────────────────── */

  function loadFonts() {
    if (document.querySelector("link[data-tai-fonts]")) return;
    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.dataset.taiFonts = "true";
    link.href = "https://fonts.googleapis.com/css2?family=VT323&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,700;1,8..60,400&family=JetBrains+Mono:wght@400;500;600&display=swap";
    document.head.appendChild(link);
  }

  /* ── Helpers ──────────────────────────────────────────────────────── */

  function getMeta(name) {
    var el = document.querySelector('meta[name="doc-' + name + '"]');
    return el ? el.content : null;
  }

  /* ── Init ──────────────────────────────────────────────────────────── */

  document.addEventListener("DOMContentLoaded", function () {
    loadFonts();
    renderMeta();
    buildSidebar();
    validate();
    hotReload();
    initTheme();
  });
})();
