import { useEffect } from "react"

export function useViewportHeightCssVar() {
  useEffect(() => {
    syncViewportHeight()
    window.addEventListener("resize", syncViewportHeight)
    window.visualViewport?.addEventListener("resize", syncViewportHeight)
    window.visualViewport?.addEventListener("scroll", syncViewportHeight)
    return () => {
      window.removeEventListener("resize", syncViewportHeight)
      window.visualViewport?.removeEventListener("resize", syncViewportHeight)
      window.visualViewport?.removeEventListener("scroll", syncViewportHeight)
    }
  }, [])
}

function syncViewportHeight() {
  const height = Math.max(Math.round(window.visualViewport?.height || window.innerHeight), 1)
  document.documentElement.style.setProperty("--app-vh", `${height}px`)
}
