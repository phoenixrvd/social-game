import { useEffect, useRef, useState } from "react"
import type { MouseEvent, Ref } from "react"
import { Link } from "react-router-dom"
import type { AppView, NpcOption, SceneOption } from "../../../state/appViewTypes"
import { PlusIcon } from "../../../shared/icons"
import { buildOptionsPath } from "../optionsRoutes"

export function ContextPanelView({ appView }: { appView: AppView }) {
  return (
    <section className="sg-settings-section">
      <div className="sg-session-row">
        <ContextGallery type="npc" appView={appView} />
        <ContextGallery type="scene" appView={appView} />
      </div>
    </section>
  )
}

function ContextGallery({ type, appView }: { type: "npc" | "scene"; appView: AppView }) {
  const selectedItemRef = useRef<HTMLAnchorElement | null>(null)
  const previousSelectedIdRef = useRef<string | null>(null)
  const [playingVideoItemId, setPlayingVideoItemId] = useState("")
  const items = type === "scene" ? appView.scene.options : appView.npc.options
  const selectedId = type === "scene" ? appView.session.sceneId : appView.session.npcId

  useEffect(
    () => selectedItemRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest", inline: "center" }),
    [selectedId],
  )
  useEffect(() => {
    if (previousSelectedIdRef.current === selectedId) return
    previousSelectedIdRef.current = selectedId || null
    if (playingVideoItemId && playingVideoItemId !== selectedId) setPlayingVideoItemId("")
  }, [playingVideoItemId, selectedId])

  return (
    <div className="sg-context-gallery" data-context-type={type}>
      <div className="sg-context-gallery-label-wrap">
        <span className="sg-selector-legend">{type === "scene" ? "SZENE" : "NPC"}</span>
      </div>
      <fieldset className="sg-context-gallery-fieldset">
        <div className="sg-context-gallery-scroll">
          {items.map((item) => {
            const selected = item.id === selectedId
            const nextNpcId = type === "scene" ? appView.session.npcId : item.id
            const nextSceneId = type === "scene" ? item.id : appView.session.sceneId
            return (
              <GalleryItem
                key={item.id}
                ref={selected ? selectedItemRef : undefined}
                item={item}
                href={buildOptionsPath(nextNpcId, nextSceneId, "context")}
                selected={selected}
                playingVideo={item.id === playingVideoItemId}
                onSelect={(clickedMedia) =>
                  setPlayingVideoItemId(clickedMedia && "videoUrl" in item && item.videoUrl ? item.id : "")
                }
              />
            )
          })}
          <Link
            className="sg-context-gallery-item sg-context-gallery-create sg-context-gallery-create-scene"
            aria-label={type === "scene" ? "Szene erstellen" : "NPC erstellen"}
            to={buildOptionsPath(
              appView.session.npcId,
              appView.session.sceneId,
              type === "scene" ? "scene-creator" : "npc-creator",
            )}
          >
            <div className="sg-context-gallery-image sg-context-gallery-create-scene-image">
              <PlusIcon />
            </div>
            <span className="sg-context-gallery-label">{type === "scene" ? "Szene erstellen" : "NPC erstellen"}</span>
          </Link>
        </div>
      </fieldset>
    </div>
  )
}

function GalleryItem({
  item,
  href,
  selected,
  playingVideo,
  onSelect,
  ref,
}: {
  item: NpcOption | SceneOption
  href: string
  selected: boolean
  playingVideo: boolean
  onSelect: (clickedMedia: boolean) => void
  ref?: Ref<HTMLAnchorElement>
}) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const videoUrl = "videoUrl" in item ? item.videoUrl : null

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
    <Link
      ref={ref}
      to={href}
      className={`sg-context-gallery-item ${selected ? "sg-context-gallery-item--selected" : ""}`}
      aria-current={selected ? "page" : undefined}
      onClick={handleClick}
    >
      <span className="sg-context-gallery-media">
        <img className="sg-context-gallery-image" src={item.imageUrl} alt={item.name || item.id} loading="eager" />
        {videoUrl ? (
          <video
            ref={videoRef}
            className={`sg-context-gallery-video ${playingVideo ? "sg-context-gallery-video--playing" : ""}`}
            src={videoUrl}
            preload="auto"
            muted
            playsInline
            disablePictureInPicture
            disableRemotePlayback
          />
        ) : null}
      </span>
      <span className="sg-context-gallery-label">{item.name || item.id}</span>
    </Link>
  )
}
