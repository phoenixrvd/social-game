import { useMutation, useQueryClient } from "@tanstack/react-query"
import { requestJson } from "./client"
import { imageSignatureQueryKey, mapState, stateQueryKey } from "./state"
import type { StateDto } from "./types"

export function useRefreshImageMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["image"],
    mutationFn: () => requestJson<Record<string, unknown>>("/api/image/refresh-active", { method: "POST" }, "Bild konnte nicht aktualisiert werden."),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: imageSignatureQueryKey })
      void queryClient.invalidateQueries({ queryKey: stateQueryKey })
    },
  })
}

export function useRevertImageMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["image"],
    mutationFn: () => requestJson<Record<string, unknown>>("/api/image/revert-active", { method: "POST" }, "Bild konnte nicht zurückgesetzt werden."),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: imageSignatureQueryKey })
      void queryClient.invalidateQueries({ queryKey: stateQueryKey })
    },
  })
}

export function useDeleteImageMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["image"],
    mutationFn: async () => mapState(await requestJson<StateDto>("/api/image/delete-active", { method: "DELETE" }, "Bild konnte nicht gelöscht werden.")),
    onSuccess: (state) => {
      queryClient.setQueryData(stateQueryKey, state)
      void queryClient.invalidateQueries({ queryKey: imageSignatureQueryKey })
    },
  })
}
