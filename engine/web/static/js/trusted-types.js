const _tt = typeof window !== "undefined" ? window.trustedTypes : undefined

let _policy = null

if (_tt && typeof trustedTypes.createPolicy === "function") {
  try {
    _policy = trustedTypes.createPolicy("sg", { createHTML: (html) => html })
  } catch {
    _policy = null
  }

  // Sicherheitsnetz: erlaubt automatische Konvertierung an TT-Sinks, falls irgendwo doch ein String ankommt.
  try {
    trustedTypes.createPolicy("default", { createHTML: (html) => html })
  } catch {
    // Policy existiert bereits oder kann nicht angelegt werden.
  }
}

export function trustedHtml(html) {
  return _policy !== null ? _policy.createHTML(html) : html
}

