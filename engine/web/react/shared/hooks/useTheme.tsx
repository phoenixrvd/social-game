import { createContext, useContext, useEffect, useState } from "react"
import type { ReactNode } from "react"

type Theme = "dark" | "light"
type ThemeContextValue = {
  theme: Theme
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

function initialTheme(): Theme {
  return localStorage.getItem("theme") === "light" ? "light" : "dark"
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(initialTheme)

  useEffect(() => {
    localStorage.setItem("theme", theme)
    document.documentElement.setAttribute("data-theme", theme)
    syncThemeChrome(theme)
  }, [theme])

  function toggleTheme() {
    setTheme((current) => (current === "dark" ? "light" : "dark"))
  }

  return <ThemeContext.Provider value={{ theme, toggleTheme }}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) throw new Error("useTheme muss innerhalb von ThemeProvider verwendet werden")
  return context
}

function syncThemeChrome(theme: Theme) {
  const installedApp =
    window.matchMedia("(display-mode: standalone)").matches ||
    window.matchMedia("(display-mode: fullscreen)").matches ||
    window.matchMedia("(display-mode: minimal-ui)").matches ||
    (window.navigator as Navigator & { standalone?: boolean }).standalone === true
  const themeColorMeta =
    document.querySelector("#theme-color-meta") || document.querySelector('meta[name="theme-color"]')
  document.documentElement.setAttribute("data-installed-app", installedApp ? "true" : "false")
  themeColorMeta?.setAttribute("content", theme === "light" ? "#f4f4f5" : "#18181b")
}
