import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from '../layout/AppShell'
import { DashboardPage } from '../../pages/DashboardPage/index'
import { ProductsPage } from '../../pages/ProductsPage/index'
import { ProductDetailPage } from '../../pages/ProductDetailPage/index'
import { DataLakePage } from '../../pages/DataLakePage/index'
import { GovernancePage } from '../../pages/GovernancePage/index'
import { PlatformOpsPage } from '../../pages/PlatformOpsPage/index'
import { SettingsPage } from '../../pages/SettingsPage/index'

export function AppRouter() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/products" element={<ProductsPage />} />
          <Route path="/products/:productId" element={<ProductDetailPage />} />
          <Route path="/datalake" element={<DataLakePage />} />
          <Route path="/governance" element={<GovernancePage />} />
          <Route path="/platform-ops" element={<PlatformOpsPage />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}
