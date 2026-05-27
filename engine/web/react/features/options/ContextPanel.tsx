import { useEffect, useRef, useState } from "react"
import type { MouseEvent, Ref } from "react"
import { Link } from "react-router-dom"
import { useStateQuery } from "../../api/state"
import type { ContextItem } from "../../api/types"
import { PlusIcon } from "../../shared/icons"
import { buildOptionsPath, useOptionsParams } from "./routes"

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
  const selectedItemRef = useRef<HTMLAnchorElement | null>(null)
  const previousSelectedIdRef = useRef<string | null>(null)
  const [playingVideoItemId, setPlayingVideoItemId] = useState("")
  const items = type === "scene" ? data?.scenes ?? [] : data?.npcs ?? []
  const selectedId = type === "scene" ? data?.sceneId : data?.npcId

  useEffect(() => {
    selectedItemRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" })
  }, [selectedId])

  useEffect(() => {
    if (previousSelectedIdRef.current === selectedId) return
    previousSelectedIdRef.current = selectedId || null
    if (playingVideoItemId && playingVideoItemId !== selectedId) setPlayingVideoItemId("")
  }, [playingVideoItemId, selectedId])

  function select(item: ContextItem, clickedMedia: boolean) {
    if (clickedMedia && item.video_url) {
      setPlayingVideoItemId(item.id)
    } else if (playingVideoItemId !== item.id) {
      setPlayingVideoItemId("")
    }
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
            const nextNpcId = type === "scene" ? data?.npcId : item.id
            const nextSceneId = type === "scene" ? item.id : data?.sceneId
            const href = nextNpcId && nextSceneId ? buildOptionsPath(nextNpcId, nextSceneId, options.panel) : "/"
            return <GalleryItem key={item.id} ref={selected ? selectedItemRef : undefined} item={item} href={href} selected={selected} playingVideo={item.id === playingVideoItemId} onSelect={(clickedMedia) => select(item, clickedMedia)} />
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

function GalleryItem({ item, href, selected, playingVideo, onSelect, ref }: { item: ContextItem; href: string; selected: boolean; playingVideo: boolean; onSelect: (clickedMedia: boolean) => void; ref?: Ref<HTMLAnchorElement> }) {
  const videoRef = useRef<HTMLVideoElement | null>(null)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return
    if (!playingVideo) {
      video.pause()
      return
    }
    video.muted = true
    video.defaultMuted = true
    video.currentTime = 0
    video.play().catch(() => {})
  }, [playingVideo, item.video_url])

  function handleClick(event: MouseEvent<HTMLAnchorElement>) {
    const target = event.target
    onSelect(target instanceof Element && Boolean(target.closest(".sg-context-gallery-media")))
  }

  return (
    <Link ref={ref} to={href} className={`sg-context-gallery-item ${selected ? "sg-context-gallery-item--selected" : ""}`} aria-current={selected ? "page" : undefined} onClick={handleClick}>
      <span className="sg-context-gallery-media">
        <img className="sg-context-gallery-image" src={item.image_url || ""} alt={item.label || item.id} loading="eager" />
        {item.video_url ? <video ref={videoRef} className={`sg-context-gallery-video ${playingVideo ? "sg-context-gallery-video--playing" : ""}`} src={item.video_url} preload="auto" muted playsInline disablePictureInPicture disableRemotePlayback /> : null}
      </span>
      <span className="sg-context-gallery-label">{item.label || item.id}</span>
    </Link>
  )
}
