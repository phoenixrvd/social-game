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

type PreviewImageInput = {
  description: string
  referenceImageDataUrl?: string | null
}

export function useCreateSceneMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["scene-creator", "create"],
    mutationFn: createScene,
    onSuccess: (state) => queryClient.setQueryData(stateQueryKey, state),
  })
}

export function useUpdateActiveSceneMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["scene-editor", "update-active"],
    mutationFn: updateActiveScene,
    onSuccess: (state) => queryClient.setQueryData(stateQueryKey, state),
  })
}

export function useCreateNpcMutation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationKey: ["npc-creator", "create"],
    mutationFn: createNpc,
    onSuccess: (state) => queryClient.setQueryData(stateQueryKey, state),
  })
}

export function useDescribeSceneReferenceMutation() {
  return useMutation({
    mutationKey: ["scene-creator", "describe-reference"],
    mutationFn: describeSceneReference,
  })
}

export function useDescribeNpcReferenceMutation() {
  return useMutation({
    mutationKey: ["npc-creator", "describe-reference"],
    mutationFn: describeNpcReference,
  })
}

export function useScenePreviewImageMutation() {
  return useMutation({
    mutationKey: ["scene-creator", "preview-image"],
    mutationFn: createScenePreviewImage,
  })
}

export function useNpcPreviewImageMutation() {
  return useMutation({
    mutationKey: ["npc-creator", "preview-image"],
    mutationFn: createNpcPreviewImage,
  })
}

async function createScene(input: CreateSceneInput) {
  return requestState("/api/scenes/create", scenePayload(input), "Szene und NPC-Kontext konnten nicht erstellt werden.")
}

async function updateActiveScene(input: CreateSceneInput) {
  return requestState("/api/scenes/update-active", scenePayload(input), "Szene konnte nicht aktualisiert werden.", "PUT")
}

async function createNpc(input: CreateNpcInput) {
  return requestState(
    "/api/npcs/create",
    {
      character_description: input.characterDescription,
      npc_image_data_url: input.npcImageDataUrl || null,
      reference_image_data_url: input.referenceImageDataUrl || null,
    },
    "NPC konnte nicht erstellt werden.",
  )
}

async function describeSceneReference(imageDataUrl: string | null) {
  const payload = await requestJson<SceneDescriptionDto>(
    "/api/scenes/describe-reference",
    jsonRequest({ image_data_url: imageDataUrl || "" }),
    "Beschreibung aus Bild konnte nicht erstellt werden.",
  )
  return payload.scene_description || ""
}

async function describeNpcReference(imageDataUrl: string | null) {
  const payload = await requestJson<CharacterDescriptionDto>(
    "/api/npcs/describe-reference",
    jsonRequest({ image_data_url: imageDataUrl || "" }),
    "Beschreibung aus Bild konnte nicht erstellt werden.",
  )
  return payload.character_description || ""
}

async function createScenePreviewImage(input: PreviewImageInput) {
  const payload = await requestJson<ImageDataUrlDto>(
    "/api/scenes/preview-image",
    jsonRequest({ scene_description: input.description, reference_image_data_url: input.referenceImageDataUrl || null }),
    "Bild aus Beschreibung konnte nicht erstellt werden.",
  )
  return payload.image_data_url || ""
}

async function createNpcPreviewImage(input: PreviewImageInput) {
  const payload = await requestJson<ImageDataUrlDto>(
    "/api/npcs/preview-image",
    jsonRequest({ character_description: input.description, reference_image_data_url: input.referenceImageDataUrl || null }),
    "Bild aus Beschreibung konnte nicht erstellt werden.",
  )
  return payload.image_data_url || ""
}

async function requestState(url: string, body: object, errorMessage: string, method = "POST") {
  return mapState(await requestJson<StateDto>(url, jsonRequest(body, method), errorMessage))
}

function scenePayload(input: CreateSceneInput) {
  return {
    scene_description: input.sceneDescription,
    scene_image_data_url: input.sceneImageDataUrl || null,
    reference_image_data_url: input.referenceImageDataUrl || null,
  }
}
