import { Navigate, createBrowserRouter } from "react-router-dom"
import { App } from "./App"

export const router = createBrowserRouter([
  {
    path: "/",
    element: <App />,
    children: [
      { index: true, element: null },
      {
        path: "sg/:npcId/:sceneId/options",
        element: <Navigate to="context" replace />,
      },
      { path: "sg/:npcId/:sceneId/options/:panel", element: null },
      { path: "sg/*", element: <Navigate to="/" replace /> },
      { path: "*", element: <Navigate to="/" replace /> },
    ],
  },
])
