export type ChatMessage = {
  id?: string
  role?: "user" | "assistant" | string
  content?: string
  html?: string
  timestamp_utc?: string
  is_editable_scene_context?: boolean
}

export type ContextItem = {
  id: string
  label?: string
  image_url?: string
  video_url?: string | null
}

export type ImageBackup = {
  name: string
  url: string
  signature?: string
}

export type Checkpoint = {
  commit_hash: string
  commit_date: string
  commit_message: string
}

export type StateDto = {
  messages?: ChatMessage[]
  image_url?: string | null
  image_original_url?: string | null
  image_backups?: ImageBackup[]
  image_signature?: string | null
  npcs?: ContextItem[]
  scenes?: ContextItem[]
  npc_id?: string | null
  scene_id?: string | null
  default_npc_id?: string | null
  default_scene_id?: string | null
  is_dynamic_npc?: boolean
  is_dynamic_scene?: boolean
  user_profile?: string
  scene_context?: string
  image_autogenerate?: boolean
  video_url?: string | null
  image_is_original?: boolean
  signature?: string | null
}

export type AppStateView = {
  messages: ChatMessage[]
  imageUrl: string | null
  imageOriginalUrl: string | null
  imageBackups: ImageBackup[]
  imageSignature: string | null
  npcs: ContextItem[]
  scenes: ContextItem[]
  npcId: string | null
  sceneId: string | null
  defaultNpcId: string | null
  defaultSceneId: string | null
  isDynamicNpc: boolean
  isDynamicScene: boolean
  userProfile: string
  sceneContext: string
  imageAutogenerate: boolean
  videoUrl: string | null
  imageIsOriginal: boolean
}

export type CheckpointsDto = {
  checkpoints?: Checkpoint[]
}

export type ImageDataUrlDto = {
  image_data_url?: string
}

export type SceneDescriptionDto = {
  scene_description?: string
}

export type CharacterDescriptionDto = {
  character_description?: string
}

export type SceneContextDto = {
  scene_context?: string
}

export type SessionInput = {
  npcId?: string
  sceneId?: string
  imageAutogenerate?: boolean
}

export type ResetNpcInput = {
  deleteNpc?: boolean
  deleteScene?: boolean
  deleteNpcContext?: boolean
}

export type CreateSceneInput = {
  sceneDescription: string
  sceneImageDataUrl?: string | null
  referenceImageDataUrl?: string | null
}

export type CreateNpcInput = {
  characterDescription: string
  npcImageDataUrl?: string | null
  referenceImageDataUrl?: string | null
}
