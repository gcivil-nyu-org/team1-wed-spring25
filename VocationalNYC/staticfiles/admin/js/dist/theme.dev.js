'use strict';

{
  var setTheme = function setTheme(mode) {
    if (mode !== "light" && mode !== "dark" && mode !== "auto") {
      console.error("Got invalid theme mode: ".concat(mode, ". Resetting to auto."));
      mode = "auto";
    }

    document.documentElement.dataset.theme = mode;
    localStorage.setItem("theme", mode);
  };

  var cycleTheme = function cycleTheme() {
    var currentTheme = localStorage.getItem("theme") || "auto";
    var prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;

    if (prefersDark) {
      // Auto (dark) -> Light -> Dark
      if (currentTheme === "auto") {
        setTheme("light");
      } else if (currentTheme === "light") {
        setTheme("dark");
      } else {
        setTheme("auto");
      }
    } else {
      // Auto (light) -> Dark -> Light
      if (currentTheme === "auto") {
        setTheme("dark");
      } else if (currentTheme === "dark") {
        setTheme("light");
      } else {
        setTheme("auto");
      }
    }
  };

  var initTheme = function initTheme() {
    // set theme defined in localStorage if there is one, or fallback to auto mode
    var currentTheme = localStorage.getItem("theme");
    currentTheme ? setTheme(currentTheme) : setTheme("auto");
  };

  window.addEventListener('load', function (_) {
    var buttons = document.getElementsByClassName("theme-toggle");
    Array.from(buttons).forEach(function (btn) {
      btn.addEventListener("click", cycleTheme);
    });
  });
  initTheme();
}