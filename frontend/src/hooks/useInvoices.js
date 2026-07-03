import { useState, useEffect, useCallback, useRef } from 'react'
import { getInvoices, getStats, getInvoice } from '../utils/api'

export function useInvoices(statusFilter = null) {
  const [invoices, setInvoices] = useState([])
  const [stats, setStats] = useState({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)

  const fetchAll = useCallback(async () => {
    try {
      setLoading(true)
      const [invData, statsData] = await Promise.all([
        getInvoices(statusFilter),
        getStats()
      ])
      const fetchedInvoices = invData.invoices || []
      setInvoices(fetchedInvoices)
      setStats(statsData)

      // Check if any invoice is still processing
      const hasProcessing = fetchedInvoices.some(inv => inv.status === 'processing')

      if (hasProcessing) {
        // Poll every 5 seconds only while something is processing
        if (!intervalRef.current) {
          intervalRef.current = setInterval(fetchAll, 5000)
        }
      } else {
        // Nothing processing — stop polling
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
          intervalRef.current = null
        }
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [statusFilter])

  useEffect(() => {
    fetchAll()
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [fetchAll])

  return { invoices, stats, loading, error, refetch: fetchAll }
}

export function useInvoice(id) {
  const [invoice, setInvoice] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const intervalRef = useRef(null)

  const fetchInvoice = useCallback(async () => {
    if (!id) return
    try {
      setLoading(true)
      const data = await getInvoice(id)
      setInvoice(data)

      // Only poll while this invoice is still processing
      if (data.status === 'processing') {
        if (!intervalRef.current) {
          intervalRef.current = setInterval(fetchInvoice, 3000)
        }
      } else {
        // Done processing — stop polling
        if (intervalRef.current) {
          clearInterval(intervalRef.current)
          intervalRef.current = null
        }
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchInvoice()
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [fetchInvoice])

  return { invoice, loading, error, refetch: fetchInvoice }
}