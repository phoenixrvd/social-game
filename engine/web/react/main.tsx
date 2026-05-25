import { createRoot } from "react-dom/client"
import { RouterProvider } from "react-router-dom"
import { AppProviders } from "./app/providers"
import { router } from "./app/router"

const root = document.getElementById("root")

if (root) {
  createRoot(root).render(
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>,
  )
}
