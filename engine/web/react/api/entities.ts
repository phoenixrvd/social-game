import { useMutation, useQueryClient } from "@tanstack/react-query"
import { jsonRequest, requestJson } from "./client"
import { mapState, stateQueryKey } from "./state"
import type {
  CharacterDescriptionDto,
  CreateNpcInput,
  CreateSceneInput,
  ImageDataUrlDto,
  SceneDescriptionDto,
  StateDto,
} from "./types"

export function useCreateSceneMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["scene-creator", "create"],
    mutationFn: async (input: CreateSceneInput) => mapState(await requestJson<StateDto>(
      "/api/scenes/create",
      jsonRequest({
        scene_description: input.sceneDescription,
        scene_image_data_url: input.sceneImageDataUrl || null,
        reference_image_data_url: input.referenceImageDataUrl || null,
      }),
      "Szene und NPC-Kontext konnten nicht erstellt werden.",
    )),
    onSuccess: (state) => queryClient.setQueryData(stateQueryKey, state),
  })
}

export function useCreateNpcMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["npc-creator", "create"],
    mutationFn: async (input: CreateNpcInput) => mapState(await requestJson<StateDto>(
      "/api/npcs/create",
      jsonRequest({
        character_description: input.characterDescription,
        npc_image_data_url: input.npcImageDataUrl || null,
        reference_image_data_url: input.referenceImageDataUrl || null,
      }),
      "NPC konnte nicht erstellt werden.",
    )),
    onSuccess: (state) => queryClient.setQueryData(stateQueryKey, state),
  })
}

export function useDescribeSceneReferenceMutation() {
  return useMutation({
    mutationKey: ["scene-creator", "describe-reference"],
    mutationFn: async (imageDataUrl: string | null) => {
      const payload = await requestJson<SceneDescriptionDto>("/api/scenes/describe-reference", jsonRequest({ image_data_url: imageDataUrl || "" }), "Beschreibung aus Bild konnte nicht erstellt werden.")
      return payload.scene_description || ""
    },
  })
}

export function useDescribeNpcReferenceMutation() {
  return useMutation({
    mutationKey: ["npc-creator", "describe-reference"],
    mutationFn: async (imageDataUrl: string | null) => {
      const payload = await requestJson<CharacterDescriptionDto>("/api/npcs/describe-reference", jsonRequest({ image_data_url: imageDataUrl || "" }), "Beschreibung aus Bild konnte nicht erstellt werden.")
      return payload.character_description || ""
    },
  })
}

export function useScenePreviewImageMutation() {
  return useMutation({
    mutationKey: ["scene-creator", "preview-image"],
    mutationFn: async (input: { description: string; referenceImageDataUrl?: string | null }) => {
      const payload = await requestJson<ImageDataUrlDto>("/api/scenes/preview-image", jsonRequest({ scene_description: input.description, reference_image_data_url: input.referenceImageDataUrl || null }), "Bild aus Beschreibung konnte nicht erstellt werden.")
      return payload.image_data_url || ""
    },
  })
}

export function useNpcPreviewImageMutation() {
  return useMutation({
    mutationKey: ["npc-creator", "preview-image"],
    mutationFn: async (input: { description: string; referenceImageDataUrl?: string | null }) => {
      const payload = await requestJson<ImageDataUrlDto>("/api/npcs/preview-image", jsonRequest({ character_description: input.description, reference_image_data_url: input.referenceImageDataUrl || null }), "Bild aus Beschreibung konnte nicht erstellt werden.")
      return payload.image_data_url || ""
    },
  })
}
