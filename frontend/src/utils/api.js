import axios from 'axios'

const api = axios.create({ baseURL: '/api', timeout: 60000 })

// Invoices
export const getInvoices = (status = null) =>
  api.get('/invoices', { params: status ? { status } : {} }).then(r => r.data)
export const getInvoice = (id) => api.get(`/invoices/${id}`).then(r => r.data)
export const getStats = () => api.get('/invoices/stats').then(r => r.data)
export const getExplanations = (id) => api.get(`/invoices/${id}/explain`).then(r => r.data)

// Upload
export const uploadInvoice = (file) => {
  const form = new FormData(); form.append('file', file)
  return api.post('/upload', form, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)
}
export const uploadPO = (file) => {
  const form = new FormData(); form.append('file', file)
  return api.post('/upload/po', form, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)
}
export const uploadBatch = (files) => {
  const form = new FormData(); files.forEach(f => form.append('files', f))
  return api.post('/upload/batch', form, { headers: { 'Content-Type': 'multipart/form-data' } }).then(r => r.data)
}

// Review
export const reviewInvoice = (id, action, correctedData = null) =>
  api.patch(`/invoices/${id}/review`, { action, corrected_data: correctedData }).then(r => r.data)
export const updateField = (id, field, value) =>
  api.patch(`/invoices/${id}/field`, null, { params: { field, value } }).then(r => r.data)

// Export
export const exportCsv = (id) => window.open(`/api/export/${id}/csv`, '_blank')
export const exportJson = (id) => window.open(`/api/export/${id}/json`, '_blank')
export const exportBatchCsv = (status = 'approved') => window.open(`/api/export/batch/csv?status=${status}`, '_blank')

// Purchase Orders
export const getPOs = () => api.get('/purchase-orders').then(r => r.data)
export const getPO = (id) => api.get(`/purchase-orders/${id}`).then(r => r.data)

// Analytics
export const getAnalyticsSummary = () => api.get('/analytics/summary').then(r => r.data)
export const getVendorAnalytics = () => api.get('/analytics/vendors').then(r => r.data)
export const getTrend = (days = 14) => api.get('/analytics/trend', { params: { days } }).then(r => r.data)
export const getGLDistribution = () => api.get('/analytics/gl-codes').then(r => r.data)
export const getPOStats = () => api.get('/analytics/po-stats').then(r => r.data)

export default api
