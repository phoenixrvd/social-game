import { useEntityCommands } from "../features/entities/entityCommands"
import { useImageCommands } from "../features/image/imageCommands"
import { useHistoryCommands } from "../features/options/historyCommands"
import { useSessionCommands } from "./sessionCommands"

export function useAppCommands() {
  const session = useSessionCommands()
  const image = useImageCommands()
  const history = useHistoryCommands()
  const entity = useEntityCommands()

  return {
    pending: {
      session: session.pending.session,
      profile: session.pending.profile,
      sceneContext: session.pending.sceneContext,
      reset: session.pending.reset,
      image: image.pending,
      history: history.pending,
      entity: entity.pending,
    },
    errors: {
      session: session.errors.session,
      profile: session.errors.profile,
      sceneContext: session.errors.sceneContext,
      reset: session.errors.reset,
      image: image.error,
      history: history.error,
      entity: entity.error,
    },
    selectContext: session.selectContext,
    saveUserProfile: session.saveUserProfile,
    saveSceneContext: session.saveSceneContext,
    generateSceneContext: session.generateSceneContext,
    resetNpc: session.resetNpc,
    deleteNpc: session.deleteNpc,
    deleteScene: session.deleteScene,
    refreshImage: image.refreshImage,
    revertImage: image.revertImage,
    deleteImage: image.deleteImage,
    createCheckpoint: history.createCheckpoint,
    restoreCheckpoint: history.restoreCheckpoint,
    resetScene: entity.resetScene,
    createNpc: entity.createNpc,
    createAvatar: entity.createAvatar,
    updateAvatar: entity.updateAvatar,
    deleteAvatar: entity.deleteAvatar,
    resetAvatar: entity.resetAvatar,
    createScene: entity.createScene,
    updateScene: entity.updateScene,
  }
}

export type AppCommands = ReturnType<typeof useAppCommands>
