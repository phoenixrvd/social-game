import { useQueryClient } from "@tanstack/react-query"
import { getNpcListOptionsQueryKey, useNpcCreate } from "../../api/generated/npc/npc"
import {
  getSceneListOptionsQueryKey,
  useSceneCreate,
  useSceneResetActive,
  useSceneUpdate,
} from "../../api/generated/scene/scene"
import { getSessionGetStateQueryKey } from "../../api/generated/session/session"
import type { NpcCreateRequest, SceneCreateRequest } from "../../api/generated/model"

export function useEntityCommands() {
  const queryClient = useQueryClient()
  const createNpcMutation = useNpcCreate()
  const createSceneMutation = useSceneCreate()
  const updateSceneMutation = useSceneUpdate()
  const resetSceneMutation = useSceneResetActive()
  const entityMutations = [
    createNpcMutation,
    createSceneMutation,
    updateSceneMutation,
    resetSceneMutation,
  ]

  const invalidateState = () => queryClient.invalidateQueries({ queryKey: getSessionGetStateQueryKey() })
  const invalidateEntities = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: getSessionGetStateQueryKey() }),
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
