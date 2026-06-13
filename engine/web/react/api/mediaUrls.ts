import { getAvatarImageUrl } from "./generated/avatar/avatar"
import { getNpcImageUrl, getNpcVideoUrl } from "./generated/npc/npc"
import { getSceneOptionImageUrl } from "./generated/scene/scene"
import { getImageCurrentUrl } from "./generated/session/session"

export function currentImageUrl(signature: string | null): string {
  const url = getImageCurrentUrl()
  return signature ? `${url}?v=${encodeURIComponent(signature)}` : url
}

export function avatarImageUrl(avatarId: string): string {
  return getAvatarImageUrl(avatarId)
}

export function npcImageUrl(npcId: string): string {
  return getNpcImageUrl(npcId)
}

export function npcVideoUrl(npcId: string): string {
  return getNpcVideoUrl(npcId)
}

export function sceneImageUrl(sceneId: string): string {
  return getSceneOptionImageUrl(sceneId)
}

export function originalNpcImageUrl(npcId: string | null): string | null {
  return npcId ? `${getNpcImageUrl(npcId)}/original` : null
}
