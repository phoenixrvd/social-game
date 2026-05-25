import { useEffect, useRef } from "react"
import type { Ref } from "react"
import { useStateQuery } from "../../api/state"
import type { ContextItem } from "../../api/types"
import { PlusIcon } from "../../shared/icons"
import { useOptionsParams } from "./routes"

export function ContextPanel() {
  return (
    <section className="sg-settings-section">
      <div className="sg-session-row">
        <ContextGallery type="npc" />
        <ContextGallery type="scene" />
      </div>
    </section>
  )
}

function ContextGallery({ type }: { type: "npc" | "scene" }) {
  const { data } = useStateQuery()
  const options = useOptionsParams()
  const selectedItemRef = useRef<HTMLButtonElement | null>(null)
  const items = type === "scene" ? data?.scenes ?? [] : data?.npcs ?? []
  const selectedId = type === "scene" ? data?.sceneId : data?.npcId

  useEffect(() => {
    selectedItemRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" })
  }, [selectedId])

  function select(item: ContextItem) {
    const nextNpcId = type === "scene" ? data?.npcId : item.id
    const nextSceneId = type === "scene" ? item.id : data?.sceneId
    if (nextNpcId && nextSceneId) options.navigateToOptions(nextNpcId, nextSceneId, options.panel)
  }

  return (
    <div className="sg-context-gallery" data-context-type={type}>
      <div className="sg-context-gallery-label-wrap">
        <span className="sg-selector-legend">{type === "scene" ? "SZENE" : "NPC"}</span>
      </div>
      <fieldset className="sg-context-gallery-fieldset">
        <div className="sg-context-gallery-scroll">
          {items.map((item) => {
            const selected = item.id === selectedId
            return <GalleryItem key={item.id} ref={selected ? selectedItemRef : undefined} item={item} selected={selected} onSelect={() => select(item)} />
          })}
          <button type="button" className="sg-context-gallery-item sg-context-gallery-create sg-context-gallery-create-scene" aria-label={type === "scene" ? "Szene erstellen" : "NPC erstellen"} onClick={() => options.navigateToPanel(type === "scene" ? "scene-creator" : "npc-creator")}>
            <div className="sg-context-gallery-image sg-context-gallery-create-scene-image"><PlusIcon /></div>
            <span className="sg-context-gallery-label">{type === "scene" ? "Szene erstellen" : "NPC erstellen"}</span>
          </button>
        </div>
      </fieldset>
    </div>
  )
}

function GalleryItem({ item, selected, onSelect, ref }: { item: ContextItem; selected: boolean; onSelect: () => void; ref?: Ref<HTMLButtonElement> }) {
  return (
    <button ref={ref} type="button" className={`sg-context-gallery-item ${selected ? "sg-context-gallery-item--selected" : ""}`} aria-pressed={selected ? "true" : "false"} onClick={onSelect}>
      <span className="sg-context-gallery-media">
        <img className="sg-context-gallery-image" src={item.image_url || ""} alt={item.label || item.id} loading="eager" />
        {item.video_url ? <video className="sg-context-gallery-video" src={item.video_url} preload="metadata" muted playsInline disablePictureInPicture /> : null}
      </span>
      <span className="sg-context-gallery-label">{item.label || item.id}</span>
    </button>
  )
}
