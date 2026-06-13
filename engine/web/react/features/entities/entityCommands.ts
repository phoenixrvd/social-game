import { useQueryClient } from "@tanstack/react-query"
import {
  getAvatarGetAvatarQueryKey,
  getAvatarListOptionsQueryKey,
  useAvatarCreate,
  useAvatarDelete,
  useAvatarResetActive,
  useAvatarUpdate,
} from "../../api/generated/avatar/avatar"
import { getNpcListOptionsQueryKey, useNpcCreate } from "../../api/generated/npc/npc"
import {
  getSceneListOptionsQueryKey,
  useSceneCreate,
  useSceneResetActive,
  useSceneUpdate,
} from "../../api/generated/scene/scene"
import { getSessionGetStateQueryKey } from "../../api/generated/session/session"
import type { AvatarCreateRequest, AvatarUpdateRequest, NpcCreateRequest, SceneCreateRequest } from "../../api/generated/model"

export function useEntityCommands() {
  const queryClient = useQueryClient()
  const createNpcMutation = useNpcCreate()
  const createAvatarMutation = useAvatarCreate()
  const updateAvatarMutation = useAvatarUpdate()
  const deleteAvatarMutation = useAvatarDelete()
  const resetAvatarMutation = useAvatarResetActive()
  const createSceneMutation = useSceneCreate()
  const updateSceneMutation = useSceneUpdate()
  const resetSceneMutation = useSceneResetActive()
  const entityMutations = [
    createAvatarMutation,
    updateAvatarMutation,
    deleteAvatarMutation,
    resetAvatarMutation,
    createNpcMutation,
    createSceneMutation,
    updateSceneMutation,
    resetSceneMutation,
  ]

  const invalidateState = () => queryClient.invalidateQueries({ queryKey: getSessionGetStateQueryKey() })
  const invalidateEntities = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: getSessionGetStateQueryKey() }),
      queryClient.invalidateQueries({ queryKey: getAvatarListOptionsQueryKey() }),
      queryClient.invalidateQueries({ queryKey: getNpcListOptionsQueryKey() }),
      queryClient.invalidateQueries({ queryKey: getSceneListOptionsQueryKey() }),
    ])

  return {
    pending: entityMutations.some((mutation) => mutation.isPending),
    error: entityMutations.find((mutation) => mutation.error)?.error,
    async resetScene(scene: string): Promise<void> {
      await resetSceneMutation.mutateAsync({ scene })
      await invalidateState()
    },
    async createNpc(data: NpcCreateRequest): Promise<string | null> {
      const response = await createNpcMutation.mutateAsync({ data })
      await invalidateEntities()
      return response.status === 200 ? response.data.id : null
    },
    async createAvatar(data: AvatarCreateRequest): Promise<string | null> {
      const response = await createAvatarMutation.mutateAsync({ data })
      await invalidateEntities()
      return response.status === 200 ? response.data.id : null
    },
    async updateAvatar(avatar: string, data: AvatarUpdateRequest): Promise<void> {
      await updateAvatarMutation.mutateAsync({ avatar, data })
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: getSessionGetStateQueryKey() }),
        queryClient.invalidateQueries({ queryKey: getAvatarListOptionsQueryKey() }),
        queryClient.invalidateQueries({ queryKey: getAvatarGetAvatarQueryKey(avatar) }),
      ])
    },
    async deleteAvatar(avatar: string): Promise<void> {
      await deleteAvatarMutation.mutateAsync({ avatar })
      await invalidateEntities()
    },
    async resetAvatar(avatar: string): Promise<void> {
      await resetAvatarMutation.mutateAsync({ avatar })
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: getSessionGetStateQueryKey() }),
        queryClient.invalidateQueries({ queryKey: getAvatarListOptionsQueryKey() }),
        queryClient.invalidateQueries({ queryKey: getAvatarGetAvatarQueryKey(avatar) }),
      ])
    },
    async createScene(data: SceneCreateRequest): Promise<string | null> {
      const response = await createSceneMutation.mutateAsync({ data })
      await invalidateEntities()
      return response.status === 200 ? response.data.id : null
    },
    async updateScene(scene: string, data: { description: string; imageDataUrl?: string | null }): Promise<void> {
      await updateSceneMutation.mutateAsync({ scene, data })
      await invalidateState()
    },
  }
}
