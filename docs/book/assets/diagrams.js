/* 把 Mermaid 源码画成图；脚本加载失败时，页面上保留图的源代码。 */
(function () {
  if (!window.mermaid) return;
  var sources = [];
  Array.prototype.forEach.call(document.querySelectorAll("pre.mermaid"), function (pre) { sources.push([pre, pre.textContent]); });
  function isDark() {
    var t = document.documentElement.dataset.theme;
    return t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  }
  function draw() {
    sources.forEach(function (s) { s[0].removeAttribute("data-processed"); s[0].textContent = s[1]; });
    mermaid.initialize({ startOnLoad: false, theme: isDark() ? "dark" : "neutral", securityLevel: "strict" });
    mermaid.run({ nodes: sources.map(function (s) { return s[0]; }) });
  }
  draw();
  document.addEventListener("themechange", draw);
})();
