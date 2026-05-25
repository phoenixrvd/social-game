import { useQuery } from "@tanstack/react-query"
import { requestJson } from "./client"
import type { AppStateView, ImageBackup, StateDto } from "./types"

export const stateQueryKey = ["state"] as const
export const imageSignatureQueryKey = ["image-signature"] as const

export function useStateQuery() {
  return useQuery({
    queryKey: stateQueryKey,
    queryFn: async () => mapState(await requestJson<StateDto>("/api/state", { cache: "no-store" })),
  })
}

export function useImageSignatureQuery(enabled: boolean) {
  return useQuery({
    queryKey: imageSignatureQueryKey,
    enabled,
    refetchInterval: enabled ? 5000 : false,
    queryFn: async () => mapState(await requestJson<StateDto>("/api/image/signature", { cache: "no-store" })),
  })
}

export function mapState(payload: StateDto = {}): AppStateView {
  return {
    messages: Array.isArray(payload.messages) ? payload.messages : [],
    imageUrl: appendCacheBuster(payload.image_url),
    imageOriginalUrl: stringOrNull(payload.image_original_url),
    imageBackups: mapImageBackups(payload.image_backups),
    imageSignature: stringOrNull(payload.image_signature || payload.signature),
    npcs: Array.isArray(payload.npcs) ? payload.npcs : [],
    scenes: Array.isArray(payload.scenes) ? payload.scenes : [],
    npcId: stringOrNull(payload.npc_id),
    sceneId: stringOrNull(payload.scene_id),
    defaultNpcId: stringOrNull(payload.default_npc_id),
    defaultSceneId: stringOrNull(payload.default_scene_id),
    isDynamicNpc: Boolean(payload.is_dynamic_npc),
    isDynamicScene: Boolean(payload.is_dynamic_scene),
    userProfile: typeof payload.user_profile === "string" ? payload.user_profile : "",
    sceneContext: typeof payload.scene_context === "string" ? payload.scene_context : "",
    imageAutogenerate: typeof payload.image_autogenerate === "boolean" ? payload.image_autogenerate : true,
    videoUrl: stringOrNull(payload.video_url),
    imageIsOriginal: typeof payload.image_is_original === "boolean" ? payload.image_is_original : true,
  }
}

function appendCacheBuster(url: unknown): string | null {
  if (typeof url !== "string" || !url) return null
  const separator = url.includes("?") ? "&" : "?"
  return `${url}${separator}t=${Date.now()}`
}

function stringOrNull(value: unknown): string | null {
  return typeof value === "string" && value ? value : null
}

function mapImageBackups(backups: unknown): ImageBackup[] {
  if (!Array.isArray(backups)) return []
  return backups
    .map((backup) => ({
      name: typeof backup?.name === "string" ? backup.name : "",
      url: typeof backup?.url === "string" ? backup.url : "",
      signature: typeof backup?.signature === "string" ? backup.signature : "",
    }))
    .filter((backup) => backup.name && backup.url)
}
