import { useQueryClient } from "@tanstack/react-query"
import {
  getSessionGetStateQueryKey,
  getSessionHistoryCheckpointsQueryKey,
  useSessionHistoryCreateCheckpoint,
  useSessionHistoryRestoreCheckpoint,
} from "../../api/generated/session/session"

export function useHistoryCommands() {
  const queryClient = useQueryClient()
  const createCheckpointMutation = useSessionHistoryCreateCheckpoint()
  const restoreCheckpointMutation = useSessionHistoryRestoreCheckpoint()
  const checkpointKey = getSessionHistoryCheckpointsQueryKey()

  return {
    pending: createCheckpointMutation.isPending || restoreCheckpointMutation.isPending,
    error: createCheckpointMutation.error || restoreCheckpointMutation.error,
    async createCheckpoint(): Promise<void> {
      await createCheckpointMutation.mutateAsync()
      await queryClient.invalidateQueries({ queryKey: checkpointKey })
    },
    async restoreCheckpoint(commitHash: string): Promise<void> {
      await restoreCheckpointMutation.mutateAsync({ commitHash })
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: getSessionGetStateQueryKey() }),
        queryClient.invalidateQueries({ queryKey: checkpointKey }),
      ])
    },
  }
}
