import Page from './app/page'
import ErrorBoundary from './components/ErrorBoundary'
import { Toaster } from './components/ui/toaster'

function App() {
  return (
    <ErrorBoundary>
      <Page />
      <Toaster />
    </ErrorBoundary>
  )
}

export default App
