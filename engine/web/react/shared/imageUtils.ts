import type { ImageBackupResponse } from "../api/generated/model"
import type { AppView } from "../state/appViewTypes"

export const EMPTY_IMAGE = "data:,"
const MAX_REFERENCE_IMAGE_BYTES = 3.5 * 1024 * 1024

export function overlayImages(image?: AppView["image"], backups: ImageBackupResponse[] = []): string[] {
  if (!image?.url) return []
  const backupUrls = backups.map((backup) => backup.url).filter(Boolean)
  const original = image.originalUrl && (backupUrls.length > 0 || !image.isOriginal) ? image.originalUrl : null
  return [image.url, ...backupUrls, original].filter(Boolean) as string[]
}

export function errorText(error: unknown, fallback = "Aktion fehlgeschlagen.") {
  return error instanceof Error ? error.message : fallback
}

export async function resizeReferenceImage(file: File): Promise<string> {
  if (!["image/png", "image/jpeg", "image/webp"].includes(file.type)) {
    throw new Error("Nur PNG, JPEG oder WebP sind erlaubt.")
  }
  const image = await loadImage(await readFile(file))
  const scale = Math.min(1, 1536 / image.width, 1536 / image.height)
  const canvas = document.createElement("canvas")
  const resizedWidth = Math.round(image.width * scale)
  const resizedHeight = Math.round(image.height * scale)
  canvas.width = Math.max(1, resizedWidth)
  canvas.height = Math.max(1, resizedHeight)
  canvas.getContext("2d")?.drawImage(image, 0, 0, canvas.width, canvas.height)
  return encodeImage(canvas)
}

function readFile(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ""))
    reader.onerror = () => reject(new Error("Bilddatei konnte nicht gelesen werden."))
    reader.readAsDataURL(file)
  })
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const image = new Image()
    image.onload = () => resolve(image)
    image.onerror = () => reject(new Error("Bilddatei konnte nicht dekodiert werden."))
    image.src = src
  })
}

function encodeImage(canvas: HTMLCanvasElement): string {
  for (const quality of [0.9, 0.82, 0.74, 0.66]) {
    const dataUrl = canvas.toDataURL("image/webp", quality)
    const bytes = Math.ceil(((dataUrl.split(",")[1] || "").length * 3) / 4)
    if (bytes <= MAX_REFERENCE_IMAGE_BYTES) return dataUrl
  }
  throw new Error("Das verkleinerte Referenzbild ist größer als 3,5 MB.")
}
