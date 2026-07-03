import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import InvoiceDetail from './pages/InvoiceDetail'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/invoice/:id" element={<InvoiceDetail />} />
    </Routes>
  )
}
