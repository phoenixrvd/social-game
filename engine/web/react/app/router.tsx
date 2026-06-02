import { Navigate, createBrowserRouter } from "react-router-dom"
import { OptionsRouteContainer } from "../features/options/OptionsRouteContainer"
import { AppContainer } from "./AppContainer"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppContainer />,
    children: [
      { index: true, element: null },
      { path: "sg/:npcId/:sceneId", element: null },
      {
        path: "sg/:npcId/:sceneId/options",
        element: <Navigate to="context" replace />,
      },
      { path: "sg/:npcId/:sceneId/options/:panel", element: <OptionsRouteContainer /> },
      { path: "sg/*", element: <Navigate to="/" replace /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
])
