import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from '../components/auth/ProtectedRoute'
import { MainLayout } from '../components/layout/MainLayout'
import { AdminUsersPage } from '../pages/AdminUsersPage'
import { AlertsPage } from '../pages/AlertsPage'
import { AuthPage } from '../pages/AuthPage'
import { CasesPage } from '../pages/CasesPage'
import { DashboardPage } from '../pages/DashboardPage'
import { MunicipalitiesPage } from '../pages/MunicipalitiesPage'
import { SettingsPage } from '../pages/SettingsPage'
import { RiskMapPage } from '../pages/RiskMapPage'
import { EndemicPage } from '../pages/EndemicPage'
import { MunicipalityDetailPage } from '../pages/MunicipalityDetailPage'

export function AppRouter() {
  return (
    <Routes>
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/register" element={<AuthPage mode="register" />} />
      <Route
        path="/*"
        element={
          <ProtectedRoute roles={['analyst', 'admin']}>
            <MainLayout>
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<DashboardPage />} />
                <Route path="/municipalities" element={<MunicipalitiesPage />} />
                <Route path="/municipalities/:id" element={<MunicipalityDetailPage />} />
                <Route path="/risk-map" element={<RiskMapPage />} />
                <Route path="/endemic" element={<EndemicPage />} />
                <Route path="/cases" element={<CasesPage />} />
                <Route path="/alerts" element={<AlertsPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route
                  path="/admin/users"
                  element={
                    <ProtectedRoute roles={['admin']}>
                      <AdminUsersPage />
                    </ProtectedRoute>
                  }
                />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Routes>
            </MainLayout>
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}
