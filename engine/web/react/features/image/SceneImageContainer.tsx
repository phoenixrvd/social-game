import { useIsMutating } from "@tanstack/react-query"
import { getImageCurrentBackupsQueryKey, useImageCurrentBackups } from "../../api/generated/session/session"
import type { AppView } from "../../state/appViewTypes"
import { overlayImages } from "../../shared/imageUtils"
import { useImageOverlayState } from "./imageUiState"
import { SceneImageView } from "./SceneImageView"

type SceneImageContainerProps = {
  className?: string
  appView?: AppView
}

export function SceneImageContainer({ className = "", appView }: SceneImageContainerProps) {
  const image = appView?.image
  const overlay = useImageOverlayState(image?.signature)
  const backupsQuery = useImageCurrentBackups({
    query: {
      queryKey: [
        ...getImageCurrentBackupsQueryKey(),
        appView?.session.npcId,
        appView?.session.sceneId,
        image?.signature,
      ],
      enabled: Boolean(image?.url),
      select: (response) => (response.status === 200 ? response.data : []),
    },
  })
  const refreshMutations = useIsMutating({ mutationKey: ["imageCurrentRefresh"] })
  const revertMutations = useIsMutating({ mutationKey: ["imageCurrentRevert"] })
  const deleteMutations = useIsMutating({ mutationKey: ["imageCurrentDelete"] })
  const imageMutationCount = refreshMutations + revertMutations + deleteMutations

  return (
    <SceneImageView
      className={className}
      imageUrl={image?.url ?? null}
      videoUrl={image?.videoUrl ?? null}
      imageIsOriginal={image?.isOriginal ?? true}
      images={overlayImages(image, backupsQuery.data ?? [])}
      isRefreshing={imageMutationCount > 0}
      open={overlay.open}
      index={overlay.index}
      setIndex={overlay.setIndex}
      onOpen={() => overlay.setOpen(true)}
      onClose={() => overlay.setOpen(false)}
    />
  )
}
