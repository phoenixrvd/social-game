import { useQueryClient } from "@tanstack/react-query"
import { getAvatarListOptionsQueryKey } from "../api/generated/avatar/avatar"
import { getNpcListOptionsQueryKey, useNpcDelete, useNpcResetActive } from "../api/generated/npc/npc"
import { getSceneListOptionsQueryKey, useSceneDelete } from "../api/generated/scene/scene"
import {
  getImageCurrentBackupsQueryKey,
  getImageCurrentSignatureQueryKey,
  getSessionGetStateQueryKey,
  useSessionSceneContextGenerate,
  useSessionSceneContextUpdate,
  useSessionUpdateSession,
  useSessionUpdateUserProfile,
} from "../api/generated/session/session"
import type { SceneContextRequest, SessionRequest } from "../api/generated/model"

export function useSessionCommands() {
  const queryClient = useQueryClient()
  const updateSession = useSessionUpdateSession()
  const updateProfile = useSessionUpdateUserProfile()
  const updateSceneContext = useSessionSceneContextUpdate()
  const generateSceneContext = useSessionSceneContextGenerate()
  const resetNpcMutation = useNpcResetActive()
  const deleteNpcMutation = useNpcDelete()
  const deleteSceneMutation = useSceneDelete()
  const sceneContextMutations = [updateSceneContext, generateSceneContext]
  const resetMutations = [resetNpcMutation, deleteNpcMutation, deleteSceneMutation]

  const invalidateState = () => queryClient.invalidateQueries({ queryKey: getSessionGetStateQueryKey() })
  const invalidateImage = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: getSessionGetStateQueryKey() }),
      queryClient.invalidateQueries({ queryKey: getImageCurrentSignatureQueryKey() }),
      queryClient.invalidateQueries({ queryKey: getImageCurrentBackupsQueryKey() }),
    ])
    const invalidateEntities = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: getSessionGetStateQueryKey() }),
      queryClient.invalidateQueries({ queryKey: getAvatarListOptionsQueryKey() }),
      queryClient.invalidateQueries({ queryKey: getNpcListOptionsQueryKey() }),
      queryClient.invalidateQueries({ queryKey: getSceneListOptionsQueryKey() }),
    ])

  return {
    pending: {
      session: updateSession.isPending,
      profile: updateProfile.isPending,
      sceneContext: sceneContextMutations.some((mutation) => mutation.isPending),
      reset: resetMutations.some((mutation) => mutation.isPending),
    },
    errors: {
      session: updateSession.error,
      profile: updateProfile.error,
      sceneContext: sceneContextMutations.find((mutation) => mutation.error)?.error,
      reset: resetMutations.find((mutation) => mutation.error)?.error,
    },
    async selectContext(data: SessionRequest): Promise<void> {
      await updateSession.mutateAsync({ data })
      if (data.avatar && !data.npc && !data.scene && data.imageAutogenerate == null) {
        await invalidateState()
        return
      }
      await invalidateImage()
    },
    async saveUserProfile(content: string): Promise<void> {
      await updateProfile.mutateAsync({ data: { content } })
      await invalidateState()
    },
    async saveSceneContext(content: string): Promise<void> {
      await updateSceneContext.mutateAsync({ data: { content } })
      await invalidateState()
    },
    async generateSceneContext(data: SceneContextRequest): Promise<string> {
      const response = await generateSceneContext.mutateAsync({ data })
      return response.status === 200 ? response.data.context : ""
    },
    async resetNpc(npc: string): Promise<void> {
      await resetNpcMutation.mutateAsync({ npc })
      await invalidateState()
    },
    async deleteNpc(npc: string): Promise<void> {
      await deleteNpcMutation.mutateAsync({ npc })
      await invalidateEntities()
    },
    async deleteScene(scene: string): Promise<void> {
      await deleteSceneMutation.mutateAsync({ scene })
      await invalidateEntities()
    },
  }
}
