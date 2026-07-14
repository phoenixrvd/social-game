import { useEffect, useState } from "react"

export function useImageOverlayState(imageKey?: string | null) {
  const [open, setOpen] = useState(false)
  const [index, setIndex] = useState(0)

  useEffect(() => {
    setIndex(0)
  }, [imageKey])

  return { open, setOpen, index, setIndex }
}
