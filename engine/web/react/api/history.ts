import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { jsonRequest, requestJson } from "./client"
import { stateQueryKey } from "./state"
import type { CheckpointsDto } from "./types"

export const checkpointsQueryKey = ["checkpoints"] as const

export function useCheckpointsQuery(enabled: boolean) {
  return useQuery({
    queryKey: checkpointsQueryKey,
    enabled,
    queryFn: async () => {
      const payload = await requestJson<CheckpointsDto>("/api/history/list", { cache: "no-store" }, "Checkpoints konnten nicht geladen werden.")
      return Array.isArray(payload.checkpoints) ? payload.checkpoints : []
    },
  })
}

export function useSaveCheckpointMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["history"],
    mutationFn: () => requestJson<Record<string, unknown>>("/api/history/save", { method: "POST" }, "Checkpoint konnte nicht erstellt werden."),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: checkpointsQueryKey }),
  })
}

export function useRestoreCheckpointMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["history"],
    mutationFn: (commitHash: string) => requestJson<Record<string, unknown>>("/api/history/restore", jsonRequest({ commit_hash: commitHash }), "Spielstand konnte nicht wiederhergestellt werden."),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: stateQueryKey })
      void queryClient.invalidateQueries({ queryKey: checkpointsQueryKey })
    },
  })
}
