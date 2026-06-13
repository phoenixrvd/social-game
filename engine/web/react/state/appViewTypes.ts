import type { AvatarResponse, MessageResponse, NpcResponse, SceneResponse } from "../api/generated/model"

export type MessageView = MessageResponse & {
  contextActions?: {
    sceneContextHref: string
    sceneEditorHref: string
  }
}

export type NpcView = NpcResponse & {
  imageUrl: string
  videoUrl: string | null
}

export type SceneView = SceneResponse & {
  imageUrl: string
}

export type AvatarView = AvatarResponse & {
  imageUrl: string
}

export type NpcOption = NpcView
export type SceneOption = SceneView
export type AvatarOption = AvatarView

export type AppView = {
  session: {
    npcId: string
    sceneId: string
    avatarId: string
    defaultNpcId: string
    defaultSceneId: string
    defaultAvatarId: string
  }
  chat: {
    messages: MessageView[]
    messagesSignature: string
  }
  npc: {
    active: NpcView | null
    options: NpcOption[]
  }
  scene: {
    active: SceneView | null
    options: SceneOption[]
    context: string
    canReset: boolean
  }
  avatar: {
    active: AvatarView | null
    options: AvatarOption[]
  }
  image: {
    url: string
    originalUrl: string | null
    signature: string | null
    isOriginal: boolean
    autogenerate: boolean
    videoUrl: string | null
  }
  user: {
    profile: string
  }
}
