import { HashRouter } from 'react-router-dom'
import { AppRouter } from './router/AppRouter'

export function App() {
  return (
    <HashRouter>
      <AppRouter />
    </HashRouter>
  )
}
