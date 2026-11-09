/* 在线阅读页的交互：目录抽屉、深浅色、复制代码、本页目录高亮、全书搜索。 */
(function () {
  var root = document.body.dataset.root || "";
  var body = document.body;

  // 目录抽屉（窄屏）
  var menu = document.querySelector(".menu");
  var scrim = document.querySelector(".scrim");
  function setNav(open) {
    body.classList.toggle("nav-open", open);
    menu.setAttribute("aria-expanded", String(open));
    scrim.hidden = !open;
  }
  menu.addEventListener("click", function () { setNav(!body.classList.contains("nav-open")); });
  scrim.addEventListener("click", function () { setNav(false); });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") setNav(false); });

  // 让当前章节在侧栏里可见
  var current = document.querySelector('.sidebar a[aria-current="page"]');
  var side = document.getElementById("sidebar");
  if (current) side.scrollTop = current.offsetTop - side.clientHeight / 2;

  // 深浅色
  document.querySelector(".theme").addEventListener("click", function () {
    var html = document.documentElement;
    var dark = html.dataset.theme ? html.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    html.dataset.theme = dark ? "light" : "dark";
    try { localStorage.setItem("dp-theme", html.dataset.theme); } catch (e) {}
    document.dispatchEvent(new Event("themechange"));
  });

  // 复制代码
  Array.prototype.forEach.call(document.querySelectorAll(".code"), function (box) {
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "copy";
    btn.textContent = "复制";
    btn.addEventListener("click", function () {
      var text = box.querySelector("code").textContent;
      var done = function () { btn.textContent = "已复制"; setTimeout(function () { btn.textContent = "复制"; }, 1500); };
      if (navigator.clipboard) navigator.clipboard.writeText(text).then(done, function () { btn.textContent = "复制失败"; });
    });
    box.appendChild(btn);
  });

  // 本页目录：高亮当前小节
  var tocLinks = Array.prototype.slice.call(document.querySelectorAll(".pagetoc a"));
  if (tocLinks.length && "IntersectionObserver" in window) {
    var byId = {};
    tocLinks.forEach(function (a) { byId[decodeURIComponent(a.getAttribute("href").slice(1))] = a; });
    var visible = {};
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { visible[e.target.id] = e.isIntersecting; });
      var ids = Object.keys(byId);
      var on = ids.filter(function (id) { return visible[id]; })[0];
      if (!on) return;
      tocLinks.forEach(function (a) { a.classList.toggle("on", a === byId[on]); });
    }, { rootMargin: "-60px 0px -70% 0px" });
    Object.keys(byId).forEach(function (id) { var el = document.getElementById(id); if (el) io.observe(el); });
  }

  // 全书搜索：第一次输入时才加载索引
  var q = document.getElementById("q");
  var hits = document.getElementById("hits");
  var index = null, loading = null;
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }
  function load() {
    if (!loading) {
      loading = fetch(root + "search.json").then(function (r) { return r.json(); }).then(function (data) { index = data; });
    }
    return loading;
  }
  function snippet(text, term) {
    var i = text.toLowerCase().indexOf(term.toLowerCase());
    var start = Math.max(0, i - 24);
    var s = (start ? "…" : "") + text.slice(start, start + 80) + (start + 80 < text.length ? "…" : "");
    var out = esc(s);
    var safe = esc(term).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    return out.replace(new RegExp(safe, "gi"), function (m) { return "<mark>" + m + "</mark>"; });
  }
  function search() {
    var terms = q.value.trim().split(/\s+/).filter(Boolean);
    if (!terms.length) { hits.hidden = true; hits.innerHTML = ""; return; }
    load().then(function () {
      if (q.value.trim().split(/\s+/).filter(Boolean).join(" ") !== terms.join(" ")) return;
      var found = index.filter(function (it) {
        var hay = (it.p + " " + it.h + " " + it.x).toLowerCase();
        return terms.every(function (t) { return hay.indexOf(t.toLowerCase()) !== -1; });
      });
      found.sort(function (a, b) {
        var ta = (a.p + a.h).toLowerCase().indexOf(terms[0].toLowerCase()) !== -1 ? 0 : 1;
        var tb = (b.p + b.h).toLowerCase().indexOf(terms[0].toLowerCase()) !== -1 ? 0 : 1;
        return ta - tb;
      });
      hits.hidden = false;
      hits.innerHTML = found.length
        ? found.slice(0, 30).map(function (it) {
            var where = it.h && it.h !== it.p ? it.p + " › " + it.h : it.p;
            return '<a href="' + root + it.u + '"><b>' + esc(where) + "</b><span>" + snippet(it.x, terms[0]) + "</span></a>";
          }).join("") + (found.length > 30 ? '<div class="none">还有 ' + (found.length - 30) + " 处，换个更具体的词试试</div>" : "")
        : '<div class="none">没有找到“' + esc(terms.join(" ")) + "”</div>";
    }, function () {
      hits.hidden = false;
      hits.innerHTML = '<div class="none">搜索索引加载失败</div>';
    });
  }
  q.addEventListener("focus", load);
  q.addEventListener("input", search);
  q.addEventListener("keydown", function (e) {
    if (e.key === "Escape") { q.value = ""; search(); }
  });
  hits.addEventListener("click", function () { setNav(false); });
})();
