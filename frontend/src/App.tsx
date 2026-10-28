import { HashRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { AppRouter } from './router/AppRouter'

export function App() {
  return (
    <HashRouter>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </HashRouter>
  )
}
