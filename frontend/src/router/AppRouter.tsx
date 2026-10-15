import { Navigate, Route, Routes } from 'react-router-dom'
import { MainLayout } from '../components/layout/MainLayout'
import { AlertsPage } from '../pages/AlertsPage'
import { CasesPage } from '../pages/CasesPage'
import { DashboardPage } from '../pages/DashboardPage'
import { MunicipalitiesPage } from '../pages/MunicipalitiesPage'
import { SettingsPage } from '../pages/SettingsPage'
import { RiskMapPage } from '../pages/RiskMapPage'
import { EndemicPage } from '../pages/EndemicPage'
import { MunicipalityDetailPage } from '../pages/MunicipalityDetailPage'

export function AppRouter() {
  return (
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
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </MainLayout>
  )
}
