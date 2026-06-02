type SafeHtmlProps = {
  html: string
  className?: string
}

const URI_ATTRIBUTES = new Set(["href", "src", "xlink:href", "formaction"])

export function SafeHtml({ html, className }: SafeHtmlProps) {
  return <div className={className} dangerouslySetInnerHTML={{ __html: sanitizeHtml(html) }} />
}

function sanitizeHtml(html: string) {
  const template = document.createElement("template")
  template.innerHTML = html

  for (const element of Array.from(
    template.content.querySelectorAll("script, style, iframe, object, embed, link, meta, base"),
  )) {
    element.remove()
  }

  for (const element of Array.from(template.content.querySelectorAll("*"))) {
    for (const attribute of Array.from(element.attributes)) {
      const name = attribute.name.toLowerCase()
      const value = attribute.value.trim().toLowerCase()
      if (name.startsWith("on")) {
        element.removeAttribute(attribute.name)
        continue
      }
      if (URI_ATTRIBUTES.has(name) && value.startsWith("javascript:")) {
        element.removeAttribute(attribute.name)
      }
    }
  }

  return template.innerHTML.trim()
}
