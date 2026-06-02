import { useQueryClient } from "@tanstack/react-query"
import {
  getImageCurrentBackupsQueryKey,
  getImageCurrentSignatureQueryKey,
  getSessionGetStateQueryKey,
  useImageCurrentDelete,
  useImageCurrentRefresh,
  useImageCurrentRevert,
} from "../../api/generated/session/session"

export function useImageCommands() {
  const queryClient = useQueryClient()
  const refreshImageMutation = useImageCurrentRefresh()
  const revertImageMutation = useImageCurrentRevert()
  const deleteImageMutation = useImageCurrentDelete()
  const imageMutations = [refreshImageMutation, revertImageMutation, deleteImageMutation]

  const invalidateImage = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: getSessionGetStateQueryKey() }),
      queryClient.invalidateQueries({ queryKey: getImageCurrentSignatureQueryKey() }),
      queryClient.invalidateQueries({ queryKey: getImageCurrentBackupsQueryKey() }),
    ])

  return {
    pending: imageMutations.some((mutation) => mutation.isPending),
    error: imageMutations.find((mutation) => mutation.error)?.error,
    async refreshImage(): Promise<void> {
      await refreshImageMutation.mutateAsync()
      await invalidateImage()
    },
    async revertImage(): Promise<void> {
      await revertImageMutation.mutateAsync()
      await invalidateImage()
    },
    async deleteImage(): Promise<void> {
      await deleteImageMutation.mutateAsync()
      await invalidateImage()
    },
  }
}
