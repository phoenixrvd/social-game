import { useMutation, useQueryClient } from "@tanstack/react-query"
import { jsonRequest, requestJson } from "./client"
import { mapState, stateQueryKey } from "./state"
import type { SceneContextDto, StateDto } from "./types"

export function useUpdateUserProfileMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["user-profile"],
    mutationFn: async (content: string) => mapState(await requestJson<StateDto>("/api/user-profile", jsonRequest({ content }, "PUT"), "User Profile konnte nicht aktualisiert werden.")),
    onSuccess: (state) => queryClient.setQueryData(stateQueryKey, state),
  })
}

export function useGenerateSceneContextMutation() {
  return useMutation({
    mutationKey: ["scene-context", "generate"],
    mutationFn: async (content: string) => {
      const payload = await requestJson<SceneContextDto>("/api/scene-context/generate", jsonRequest({ content }), "Scene Context konnte nicht generiert werden.")
      return payload.scene_context || ""
    },
  })
}

export function useUpdateSceneContextMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["scene-context", "update"],
    mutationFn: async (content: string) => mapState(await requestJson<StateDto>("/api/scene-context", jsonRequest({ content }, "PUT"), "Scene Context konnte nicht gespeichert werden.")),
    onSuccess: (state) => queryClient.setQueryData(stateQueryKey, state),
  })
}
