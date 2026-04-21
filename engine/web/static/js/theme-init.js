function isInstalledApp() {
  const standalone = window.matchMedia("(display-mode: standalone)").matches
  const fullscreen = window.matchMedia("(display-mode: fullscreen)").matches
  const minimalUi = window.matchMedia("(display-mode: minimal-ui)").matches

  return standalone || fullscreen || minimalUi || window.navigator.standalone === true
}

function getThemeColor(theme, installedApp) {
  if (!installedApp) {
    return theme === "light" ? "#f4f4f5" : "#18181b"
  }

  return theme === "light" ? "#f3f4f640" : "#09090b40"
}

const theme = localStorage.getItem("theme") === "light" ? "light" : "dark"
const installedApp = isInstalledApp()

document.documentElement.setAttribute("data-theme", theme)
document.documentElement.setAttribute("data-installed-app", installedApp ? "true" : "false")

const themeColorMeta = document.querySelector("#theme-color-meta") || document.querySelector('meta[name="theme-color"]')
if (themeColorMeta) {
  themeColorMeta.setAttribute("content", getThemeColor(theme, installedApp))
}

