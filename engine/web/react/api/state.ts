import { useQuery } from "@tanstack/react-query"
import type { MessageResponse, NpcResponse, SceneResponse } from "./generated/model"
import {
  getImageCurrentSignatureQueryKey,
  getSessionGetStateQueryKey,
  imageCurrentSignature,
  sessionGetState,
} from "./generated/session/session"

export type AppStateView = {
  messages: MessageResponse[]
  imageUrl: string | null
  imageOriginalUrl: string | null
  imageSignature: string | null
  npcs: Array<NpcResponse & { imageUrl?: string; hasVideo?: boolean }>
  scenes: SceneResponse[]
  npcId: string | null
  sceneId: string | null
  defaultNpcId: string | null
  defaultSceneId: string | null
  isDynamicNpc: boolean
  isDynamicScene: boolean
  canResetScene: boolean
  userProfile: string
  sceneContext: string
  npcName: string
  characterDescription: string
  sceneDescription: string
  sceneLocationDescription: string
  imageAutogenerate: boolean
  videoUrl: string | null
  hasVideo: boolean
  imageIsOriginal: boolean
}

export const stateQueryKey = getSessionGetStateQueryKey()
export const imageSignatureQueryKey = getImageCurrentSignatureQueryKey()

const noStoreRequest = { cache: "no-store" } as const

export function useStateQuery() {
  const stateQuery = useQuery({
    queryKey: stateQueryKey,
    queryFn: async () => {
      const response = await sessionGetState(noStoreRequest)
      return normalizeStateDynamic(response.data)
    },
  })

  const npcId = stateQuery.data?.npcId
  const sceneId = stateQuery.data?.sceneId

  const npcQuery = useQuery({
    queryKey: ["npc", npcId],
    enabled: Boolean(npcId),
    staleTime: Number.POSITIVE_INFINITY,
    queryFn: async () => normalizeNpc(await readJson(`/api/npcs/${npcId}`)),
  })

  const sceneQuery = useQuery({
    queryKey: ["scene", sceneId],
    enabled: Boolean(sceneId),
    staleTime: Number.POSITIVE_INFINITY,
    queryFn: async () => normalizeScene(await readJson(`/api/scenes/${sceneId}`)),
  })

  return {
    ...stateQuery,
    data: mergeState(stateQuery.data, npcQuery.data, sceneQuery.data),
  }
}

export function useImageSignatureQuery(enabled: boolean, npcId?: string | null, sceneId?: string | null) {
  return useQuery({
    queryKey: [...imageSignatureQueryKey, npcId, sceneId],
    enabled,
    refetchInterval: enabled ? 5000 : false,
    queryFn: async () => {
      const response = await imageCurrentSignature(noStoreRequest)
      const payload = (response.data ?? {}) as {
        signature?: unknown
        imageIsOriginal?: unknown
      }
      return {
        imageSignature: typeof payload.signature === "string" ? payload.signature : null,
        imageUrl: currentImageUrl(payload.signature),
        imageIsOriginal: typeof payload.imageIsOriginal === "boolean" ? payload.imageIsOriginal : undefined,
      } as Partial<AppStateView>
    },
  })
}

type DynamicState = Omit<
  AppStateView,
  | "npcName"
  | "characterDescription"
  | "sceneDescription"
  | "sceneLocationDescription"
  | "isDynamicNpc"
  | "isDynamicScene"
>

type NpcDetailState = Pick<
  AppStateView,
  | "npcName"
  | "characterDescription"
  | "isDynamicNpc"
  | "hasVideo"
>

type SceneDetailState = Pick<AppStateView, "sceneDescription" | "sceneLocationDescription" | "isDynamicScene">

export function normalizeStateDynamic(data: unknown): DynamicState {
  const payload = (data ?? {}) as Record<string, unknown>
  const imageSignature = stringOrNull(payload.imageSignature)
  return {
    messages: Array.isArray(payload.messages) ? (payload.messages as MessageResponse[]) : [],
    imageUrl: currentImageUrl(imageSignature),
    imageSignature,
    npcs: Array.isArray(payload.npcs) ? (payload.npcs as Array<NpcResponse & { imageUrl?: string; hasVideo?: boolean }>) : [],
    scenes: Array.isArray(payload.scenes) ? (payload.scenes as SceneResponse[]) : [],
    npcId: stringOrNull(payload.npc),
    sceneId: stringOrNull(payload.scene),
    defaultNpcId: stringOrNull(payload.defaultNpc),
    defaultSceneId: stringOrNull(payload.defaultScene),
    canResetScene: Boolean(payload.canResetScene),
    userProfile: typeof payload.userProfile === "string" ? payload.userProfile : "",
    sceneContext: typeof payload.sceneContext === "string" ? payload.sceneContext : "",
    imageAutogenerate: typeof payload.imageAutogenerate === "boolean" ? payload.imageAutogenerate : true,
    imageOriginalUrl: null,
    videoUrl: null,
    hasVideo: false,
    imageIsOriginal: typeof payload.imageIsOriginal === "boolean" ? payload.imageIsOriginal : true,
  }
}

function normalizeNpc(data: unknown): NpcDetailState {
  const payload = (data ?? {}) as Record<string, unknown>
  return {
    npcName: typeof payload.name === "string" ? payload.name : "",
    characterDescription: typeof payload.description === "string" ? payload.description : "",
    hasVideo: typeof payload.hasVideo === "boolean" ? payload.hasVideo : false,
    isDynamicNpc: Boolean(payload.isDynamicNpc),
  }
}

function normalizeScene(data: unknown): SceneDetailState {
  const payload = (data ?? {}) as Record<string, unknown>
  return {
    sceneDescription: typeof payload.name === "string" ? payload.name : "",
    sceneLocationDescription: typeof payload.description === "string" ? payload.description : "",
    isDynamicScene: Boolean(payload.isDynamicScene),
  }
}

function mergeState(
  dynamicState: DynamicState | undefined,
  npcState: NpcDetailState | undefined,
  sceneState: SceneDetailState | undefined,
): AppStateView | undefined {
  if (!dynamicState) return undefined
  const imageOriginalUrl = dynamicState.npcId ? `/api/npcs/${dynamicState.npcId}/image/original` : null
  return {
    ...dynamicState,
    npcName: npcState?.npcName ?? "",
    characterDescription: npcState?.characterDescription ?? "",
    sceneDescription: sceneState?.sceneDescription ?? "",
    sceneLocationDescription: sceneState?.sceneLocationDescription ?? "",
    isDynamicNpc: npcState?.isDynamicNpc ?? false,
    isDynamicScene: sceneState?.isDynamicScene ?? false,
    imageUrl: dynamicState.imageUrl,
    imageOriginalUrl,
    imageIsOriginal: dynamicState.imageIsOriginal,
    hasVideo: npcState?.hasVideo ?? false,
    videoUrl: npcState?.hasVideo && dynamicState.npcId ? `/api/npcs/${dynamicState.npcId}/video` : null,
  }
}

async function readJson(url: string): Promise<unknown> {
  const response = await fetch(url, noStoreRequest)
  if (!response.ok) throw new Error("Anfrage fehlgeschlagen.")
  return await response.json().catch(() => ({}))
}

function stringOrNull(value: unknown): string | null {
  return typeof value === "string" && value ? value : null
}

function currentImageUrl(signature: unknown): string {
  return typeof signature === "string" && signature ? `/api/session/image?v=${encodeURIComponent(signature)}` : "/api/session/image"
}
