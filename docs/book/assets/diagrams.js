/* 把 Mermaid 源码画成图；脚本加载失败时，页面上保留图的源代码。 */
(function () {
  if (!window.mermaid) return;
  var sources = [];
  Array.prototype.forEach.call(document.querySelectorAll("pre.mermaid"), function (pre) { sources.push([pre, pre.textContent]); });
  function isDark() {
    var t = document.documentElement.dataset.theme;
    return t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  }
  // 宽图在手机上不要缩得太小：最多缩到原尺寸的 65%，再宽就横向滚动
  function keepReadable() {
    sources.forEach(function (s) {
      var svg = s[0].querySelector("svg");
      if (!svg || !svg.viewBox || !svg.viewBox.baseVal) return;
      svg.style.minWidth = Math.round(svg.viewBox.baseVal.width * 0.65) + "px";
    });
    markWide();
  }
  function markWide() {
    sources.forEach(function (s) {
      var fig = s[0].parentNode;
      fig.classList.toggle("wide", fig.scrollWidth > fig.clientWidth + 4);
    });
  }
  function draw() {
    sources.forEach(function (s) { s[0].removeAttribute("data-processed"); s[0].textContent = s[1]; });
    mermaid.initialize({ startOnLoad: false, theme: isDark() ? "dark" : "neutral", securityLevel: "strict" });
    mermaid.run({ nodes: sources.map(function (s) { return s[0]; }) }).then(keepReadable);
  }
  draw();
  document.addEventListener("themechange", draw);
  window.addEventListener("resize", markWide);
})();
