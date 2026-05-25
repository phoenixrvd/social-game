import { useEffect } from "react"

export function useBodyScrollLock(locked: boolean) {
  useEffect(() => {
    const shouldLock = locked && window.matchMedia("(max-width: 1023px)").matches
    document.body.classList.toggle("sg-overflow-y-hidden", shouldLock)
    return () => {
      document.body.classList.toggle("sg-overflow-y-hidden", false)
    }
  }, [locked])
}
