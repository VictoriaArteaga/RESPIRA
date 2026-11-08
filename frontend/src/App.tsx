import { HashRouter } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import { I18nProvider } from './i18n/I18nContext'
import { PreferencesProvider } from './preferences/PreferencesContext'
import { AppRouter } from './router/AppRouter'
import { ThemeProvider } from './theme/ThemeContext'

export function App() {
  return (
    <ThemeProvider>
      <I18nProvider>
        <PreferencesProvider>
          <HashRouter>
            <AuthProvider>
              <AppRouter />
            </AuthProvider>
          </HashRouter>
        </PreferencesProvider>
      </I18nProvider>
    </ThemeProvider>
  )
}
