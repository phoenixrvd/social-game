import { useAvatarGetAvatar, useAvatarListOptions } from "../api/generated/avatar/avatar"
import { useNpcGetNpc, useNpcListOptions } from "../api/generated/npc/npc"
import { useSceneGetScene, useSceneListOptions } from "../api/generated/scene/scene"
import { useSessionGetState } from "../api/generated/session/session"
import type { AvatarResponse, NpcResponse, SceneResponse, StateResponse } from "../api/generated/model"
import { buildOptionsPath } from "../features/options/optionsRoutes"
import { avatarImageUrl, currentImageUrl, npcImageUrl, npcVideoUrl, originalNpcImageUrl, sceneImageUrl } from "../api/mediaUrls"
import type { AppView, AvatarView, MessageView, NpcView, SceneView } from "./appViewTypes"

const noStoreRequest = { cache: "no-store" } as const

export function useAppView() {
  const stateQuery = useSessionGetState({ request: noStoreRequest })
  const state = stateQuery.data?.status === 200 ? stateQuery.data.data : null
  const npcId = state?.npc
  const sceneId = state?.scene
  const avatarId = state?.avatar
  const npcQuery = useNpcGetNpc(npcId || "", {
    query: { enabled: Boolean(npcId), staleTime: Number.POSITIVE_INFINITY },
  })
  const sceneQuery = useSceneGetScene(sceneId || "", {
    query: { enabled: Boolean(sceneId), staleTime: Number.POSITIVE_INFINITY },
  })
  const avatarQuery = useAvatarGetAvatar(avatarId || "", {
    query: { enabled: Boolean(avatarId), staleTime: Number.POSITIVE_INFINITY },
  })
  const npcOptionsQuery = useNpcListOptions({ query: { staleTime: Number.POSITIVE_INFINITY } })
  const sceneOptionsQuery = useSceneListOptions({ query: { staleTime: Number.POSITIVE_INFINITY } })
  const avatarOptionsQuery = useAvatarListOptions({ query: { staleTime: Number.POSITIVE_INFINITY } })
  const npc = npcQuery.data?.status === 200 ? npcQuery.data.data : null
  const scene = sceneQuery.data?.status === 200 ? sceneQuery.data.data : null
  const avatar = avatarQuery.data?.status === 200 ? avatarQuery.data.data : null
  const npcOptions = npcOptionsQuery.data?.status === 200 ? npcOptionsQuery.data.data : []
  const sceneOptions = sceneOptionsQuery.data?.status === 200 ? sceneOptionsQuery.data.data : []
  const avatarOptions = avatarOptionsQuery.data?.status === 200 ? avatarOptionsQuery.data.data : []
  const isLoadingRelatedData = npcQuery.isLoading || sceneQuery.isLoading || avatarQuery.isLoading

  return {
    ...stateQuery,
    data: state ? mapAppView(state, npc, scene, avatar, npcOptions, sceneOptions, avatarOptions) : undefined,
    isLoading: stateQuery.isLoading || isLoadingRelatedData,
  }
}

export function mapAppView(
  state: StateResponse,
  activeNpc: NpcResponse | null,
  activeScene: SceneResponse | null,
  activeAvatar: AvatarResponse | null,
  npcOptions: NpcResponse[],
  sceneOptions: SceneResponse[],
  avatarOptions: AvatarResponse[],
): AppView {
  const activeNpcView = activeNpc ? mapNpcView(activeNpc) : null
  const videoUrl = activeNpcView?.videoUrl ?? null
  return {
    session: {
      npcId: state.npc,
      sceneId: state.scene,
      avatarId: state.avatar,
      defaultNpcId: state.defaultNpc,
      defaultSceneId: state.defaultScene,
      defaultAvatarId: state.defaultAvatar,
    },
    chat: {
      messages: state.messages.map((message) => mapMessageView(message, state.npc, state.scene)),
      messagesSignature: state.messagesSignature,
    },
    npc: {
      active: activeNpcView,
      options: npcOptions.map(mapNpcView),
    },
    scene: {
      active: activeScene ? mapSceneView(activeScene) : null,
      options: sceneOptions.map(mapSceneView),
      context: state.sceneContext,
      canReset: state.canResetScene,
    },
    avatar: {
      active: activeAvatar ? mapAvatarView(activeAvatar) : null,
      options: avatarOptions.map(mapAvatarView),
    },
    image: {
      url: currentImageUrl(state.imageSignature),
      originalUrl: originalNpcImageUrl(state.npc),
      signature: state.imageSignature,
      isOriginal: state.imageIsOriginal,
      autogenerate: state.imageAutogenerate,
      videoUrl,
    },
    user: {
      profile: state.userProfile,
    },
  }
}

function mapNpcView(npc: NpcResponse): NpcView {
  return {
    ...npc,
    imageUrl: npcImageUrl(npc.id),
    videoUrl: npc.hasVideo ? npcVideoUrl(npc.id) : null,
  }
}

function mapSceneView(scene: SceneResponse): SceneView {
  return { ...scene, imageUrl: sceneImageUrl(scene.id) }
}

function mapAvatarView(avatar: AvatarResponse): AvatarView {
  return { ...avatar, imageUrl: avatarImageUrl(avatar.id) }
}

function mapMessageView(message: StateResponse["messages"][number], npcId: string, sceneId: string): MessageView {
  if (!message.isEditableSceneContext) return message
  return {
    ...message,
    contextActions: {
      sceneContextHref: buildOptionsPath(npcId, sceneId, "scene-context"),
      sceneEditorHref: buildOptionsPath(npcId, sceneId, "scene-editor"),
    },
  }
}
