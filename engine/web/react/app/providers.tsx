import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import type { ReactNode } from "react"
import { ConfirmDialogProvider } from "../shared/ConfirmDialog"
import { ThemeProvider } from "../shared/hooks/useTheme"

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false,
    },
  },
})

type AppProvidersProps = {
  children: ReactNode
}

export function AppProviders({ children }: AppProvidersProps) {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ConfirmDialogProvider>{children}</ConfirmDialogProvider>
      </ThemeProvider>
    </QueryClientProvider>
  )
}
