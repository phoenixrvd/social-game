import { useEffect, useRef, useState } from "react"
import type { MouseEvent, Ref } from "react"
import { Link } from "react-router-dom"
import { useNpcListOptions } from "../../api/generated/npc/npc"
import { useSceneListOptions } from "../../api/generated/scene/scene"
import { useStateQuery } from "../../api/state"
import { PlusIcon } from "../../shared/icons"
import { buildOptionsPath, useOptionsParams } from "./routes"

type ContextItem = {
  id: string
  label?: string
  name?: string
  imageUrl?: string
  hasVideo?: boolean
}

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
  const npcOptionsQuery = useNpcListOptions({ query: { staleTime: Number.POSITIVE_INFINITY } })
  const sceneOptionsQuery = useSceneListOptions({ query: { staleTime: Number.POSITIVE_INFINITY } })
  const options = useOptionsParams()
  const selectedItemRef = useRef<HTMLAnchorElement | null>(null)
  const previousSelectedIdRef = useRef<string | null>(null)
  const [playingVideoItemId, setPlayingVideoItemId] = useState("")
  const npcItems = npcOptionsQuery.data?.status === 200 ? npcOptionsQuery.data.data : []
  const sceneItems = sceneOptionsQuery.data?.status === 200 ? sceneOptionsQuery.data.data : []
  const items: ContextItem[] = type === "scene"
    ? sceneItems.map((scene) => ({ id: scene.id, name: scene.name }))
    : npcItems.map((npc) => ({ id: npc.id, name: npc.name, imageUrl: `/api/npcs/${npc.id}/image`, hasVideo: npc.hasVideo === true }))
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
    const videoUrl = type === "npc" && item.hasVideo ? `/api/npcs/${item.id}/video` : null
    if (clickedMedia && videoUrl) {
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
            return <GalleryItem key={item.id} ref={selected ? selectedItemRef : undefined} item={item} href={href} selected={selected} playingVideo={item.id === playingVideoItemId} imageUrl={type === "scene" ? `/api/scenes/${item.id}/image` : item.imageUrl || null} videoUrl={type === "npc" && item.hasVideo ? `/api/npcs/${item.id}/video` : null} onSelect={(clickedMedia) => select(item, clickedMedia)} />
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

function GalleryItem({ item, href, selected, playingVideo, imageUrl, videoUrl, onSelect, ref }: { item: ContextItem; href: string; selected: boolean; playingVideo: boolean; imageUrl: string | null; videoUrl: string | null; onSelect: (clickedMedia: boolean) => void; ref?: Ref<HTMLAnchorElement> }) {
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
  }, [playingVideo, videoUrl])

  function handleClick(event: MouseEvent<HTMLAnchorElement>) {
    const target = event.target
    onSelect(target instanceof Element && Boolean(target.closest(".sg-context-gallery-media")))
  }

  return (
    <Link ref={ref} to={href} className={`sg-context-gallery-item ${selected ? "sg-context-gallery-item--selected" : ""}`} aria-current={selected ? "page" : undefined} onClick={handleClick}>
      <span className="sg-context-gallery-media">
        <img className="sg-context-gallery-image" src={imageUrl || ""} alt={item.name || item.label || item.id} loading="eager" />
        {videoUrl ? <video ref={videoRef} className={`sg-context-gallery-video ${playingVideo ? "sg-context-gallery-video--playing" : ""}`} src={videoUrl} preload="auto" muted playsInline disablePictureInPicture disableRemotePlayback /> : null}
      </span>
      <span className="sg-context-gallery-label">{item.name || item.label || item.id}</span>
    </Link>
  )
}
