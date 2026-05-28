import { useMutation, useQueryClient } from "@tanstack/react-query"
import { jsonRequest, requestJson } from "./client"
import { stateQueryKey } from "./state"
import type { AppStateView, ResetNpcInput, SessionInput, StateDto } from "./types"
import { mapState } from "./state"

export function useUpdateSessionMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["session"],
    mutationFn: async (input: SessionInput) => {
      const payload = await requestJson<StateDto>(
        "/api/session",
        jsonRequest(
          {
            npc_id: input.npcId,
            scene_id: input.sceneId,
            image_autogenerate: input.imageAutogenerate,
          },
          "PUT",
        ),
        "Session konnte nicht aktualisiert werden.",
      )
      return mapState(payload)
    },
    onSuccess: (state: AppStateView) => {
      queryClient.setQueryData(stateQueryKey, state)
    },
  })
}

export function useResetNpcMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["session", "reset"],
    mutationFn: async (input: ResetNpcInput) => {
      const params = new URLSearchParams()
      if (input.deleteNpc) params.set("delete_npc", "true")
      if (input.deleteScene) params.set("delete_scene", "true")
      if (input.deleteNpcContext) params.set("delete_npc_context", "true")
      const suffix = params.toString() ? `?${params.toString()}` : ""
      const payload = await requestJson<StateDto>(
        `/api/npc/reset-active${suffix}`,
        { method: "DELETE" },
        "Verlauf konnte nicht geloescht werden.",
      )
      return mapState(payload)
    },
    onSuccess: (state: AppStateView) => {
      queryClient.setQueryData(stateQueryKey, state)
    },
  })
}

export function useResetSceneMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["session", "reset-scene"],
    mutationFn: async () => {
      const payload = await requestJson<StateDto>(
        "/api/scenes/reset-active",
        { method: "DELETE" },
        "Scene konnte nicht zurueckgesetzt werden.",
      )
      return mapState(payload)
    },
    onSuccess: (state: AppStateView) => {
      queryClient.setQueryData(stateQueryKey, state)
    },
  })
}
