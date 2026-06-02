export async function imageUrlToDataUrl(imageUrl: string): Promise<string> {
  const response = await fetch(imageUrl)
  if (!response.ok) throw new Error("Szenenbild konnte nicht geladen werden.")
  const blob = await response.blob()
  return blobToDataUrl(blob)
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ""))
    reader.onerror = () => reject(new Error("Szenenbild konnte nicht gelesen werden."))
    reader.readAsDataURL(blob)
  })
}
