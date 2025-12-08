import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminService } from '../services/adminService'
import { authService } from '../services/authService'
import { Card, CardBody, Spinner, Pagination } from '@heroui/react'
import { motion } from 'framer-motion'
import Sidebar from '../components/Sidebar'

function ProcessingHistoryPage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalItems, setTotalItems] = useState(0)
  const [stats, setStats] = useState({ total: 0, completed: 0, processing: 0, failed: 0, uploaded: 0 })
  const [activeMenu, setActiveMenu] = useState('documents')
  const [user, setUser] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [errorModal, setErrorModal] = useState({ open: false, doc: null })

  const PAGE_SIZE = 20

  useEffect(() => {
    loadUser()
  }, [])

  useEffect(() => {
    fetchHistory()
  }, [page, statusFilter])

  const loadUser = async () => {
    const currentUser = await authService.getCurrentUser()
    setUser(currentUser)
  }

  const fetchHistory = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await adminService.listDocuments({
        page,
        pageSize: PAGE_SIZE,
        status: statusFilter === 'all' ? null : statusFilter,
      })
      setHistory(data.items)
      setTotalPages(Math.ceil(data.total / PAGE_SIZE))
      setTotalItems(data.total)
      // Update stats from API response
      if (data.stats) {
        setStats(data.stats)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const config = {
      UPLOADED: { text: 'text-blue-600', dot: 'bg-blue-500', label: 'Uploaded' },
      IDP_RUNNING: { text: 'text-orange-600', dot: 'bg-orange-500', label: 'Processing' },
      EMBEDDING_DONE: { text: 'text-emerald-600', dot: 'bg-emerald-500', label: 'Completed' },
      FAILED: { text: 'text-red-600', dot: 'bg-red-500', label: 'Failed' },
    }[status] || { text: 'text-gray-600', dot: 'bg-gray-400', label: status }

    return (
      <span className={`inline-flex items-center gap-2 text-sm font-medium ${config.text}`}>
        <span className={`w-2 h-2 rounded-full ${config.dot}`}></span>
        {config.label}
      </span>
    )
  }

  const formatDate = (dateStr) => {
    const date = new Date(dateStr)
    return date.toLocaleString('en-US', {
      month: '2-digit',
      day: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    })
  }

  const getProcessingDuration = (doc) => {
    if (!doc.uploaded_at) return '-'
    if (doc.status === 'IDP_RUNNING') return 'In progress...'
    if (doc.status === 'UPLOADED') return 'Pending'
    // Mock duration - in real app, calculate from actual timestamps
    return `${Math.floor(Math.random() * 30) + 5}s`
  }

  return (
    <div className="flex min-h-screen bg-slate-100">
      <Sidebar activeMenu={activeMenu} setActiveMenu={setActiveMenu} user={user} />

      <div className="flex-1 p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/admin')}
              className="p-2 text-gray-500 hover:text-gray-700 hover:bg-white rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-800">Processing History</h1>
              <p className="text-sm text-gray-500 mt-1">View document processing timeline and status</p>
            </div>
          </div>
          <button
            onClick={fetchHistory}
            disabled={loading}
            className="inline-flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50 transition-colors disabled:opacity-50"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-4 gap-4 mb-8">
          <Card className="bg-white">
            <CardBody className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                <div>
                  <p className="text-2xl font-bold text-gray-800">{stats.total}</p>
                  <p className="text-xs text-gray-500">Total Documents</p>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card className="bg-white">
            <CardBody className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <div>
                  <p className="text-2xl font-bold text-emerald-600">{stats.completed}</p>
                  <p className="text-xs text-gray-500">Completed</p>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card className="bg-white">
            <CardBody className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-2xl font-bold text-orange-600">
                    {stats.processing + stats.uploaded}
                  </p>
                  <p className="text-xs text-gray-500">Processing</p>
                </div>
              </div>
            </CardBody>
          </Card>

          <Card className="bg-white">
            <CardBody className="p-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <p className="text-2xl font-bold text-red-600">{stats.failed}</p>
                  <p className="text-xs text-gray-500">Failed</p>
                </div>
              </div>
            </CardBody>
          </Card>
        </div>

        {/* History Table */}
        <Card>
          <CardBody className="p-0">
            {/* Filter */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100">
              <h2 className="text-lg font-semibold text-gray-800">Processing Timeline</h2>
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Filter:</span>
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="px-3 py-1.5 text-sm border border-gray-200 rounded-lg bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="all">All Status</option>
                  <option value="UPLOADED">Uploaded</option>
                  <option value="IDP_RUNNING">Processing</option>
                  <option value="EMBEDDING_DONE">Completed</option>
                  <option value="FAILED">Failed</option>
                </select>
              </div>
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-16">
                <Spinner size="lg" />
              </div>
            ) : error ? (
              <div className="p-8 text-center">
                <p className="text-red-600 mb-2">⚠️ {error}</p>
                <button onClick={fetchHistory} className="text-sm text-blue-500 hover:underline">
                  Try again
                </button>
              </div>
            ) : history.length === 0 ? (
              <div className="py-16 text-center">
                <svg className="w-16 h-16 mx-auto text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-gray-500">No processing history found</p>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Document</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-400 uppercase tracking-wider">Pages</th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-400 uppercase tracking-wider">Chunks</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-400 uppercase tracking-wider">Started At</th>
                        <th className="px-6 py-3 text-center text-xs font-medium text-gray-400 uppercase tracking-wider">Duration</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {history.map((doc, idx) => (
                        <motion.tr
                          key={doc.doc_id}
                          initial={{ opacity: 0 }}
                          animate={{ opacity: 1 }}
                          transition={{ delay: idx * 0.03 }}
                          className="hover:bg-gray-50/50 transition-colors"
                        >
                          <td className="px-6 py-4">
                            <div>
                              <p className="text-sm font-medium text-gray-800 truncate max-w-xs" title={doc.filename}>
                                {doc.filename}
                              </p>
                              <p className="text-xs text-gray-400 font-mono">doc_{doc.doc_id.slice(0, 7)}</p>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              {getStatusBadge(doc.status)}
                              {doc.status === 'FAILED' && doc.error_message && (
                                <button
                                  onClick={() => setErrorModal({ open: true, doc })}
                                  className="p-1 text-red-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                                  title="View error details"
                                >
                                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                  </svg>
                                </button>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4 text-center text-sm text-gray-600">{doc.page_count || 0}</td>
                          <td className="px-6 py-4 text-center text-sm text-gray-600">{doc.chunk_count || 0}</td>
                          <td className="px-6 py-4 text-sm text-gray-500">{formatDate(doc.uploaded_at)}</td>
                          <td className="px-6 py-4 text-center">
                            <span className={`text-sm ${doc.status === 'IDP_RUNNING' ? 'text-orange-600' : 'text-gray-600'}`}>
                              {getProcessingDuration(doc)}
                            </span>
                          </td>
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between px-6 py-4 border-t border-gray-100">
                  <p className="text-sm text-gray-500">
                    Showing <span className="font-medium text-emerald-600">{(page - 1) * PAGE_SIZE + 1}-{Math.min(page * PAGE_SIZE, totalItems)}</span> of <span className="font-medium text-emerald-600">{totalItems}</span>
                  </p>
                  {totalPages > 1 && (
                    <Pagination total={totalPages} page={page} onChange={setPage} showControls size="sm" color="primary" />
                  )}
                </div>
              </>
            )}
          </CardBody>
        </Card>

        {/* Error Details Modal */}
        {errorModal.open && errorModal.doc && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setErrorModal({ open: false, doc: null })}>
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 overflow-hidden"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="px-6 py-4 bg-red-50 border-b border-red-100 flex items-center gap-3">
                <div className="w-10 h-10 bg-red-100 rounded-full flex items-center justify-center">
                  <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-red-800">Processing Failed</h3>
                  <p className="text-sm text-red-600">{errorModal.doc.filename}</p>
                </div>
              </div>
              <div className="p-6">
                <div className="mb-4">
                  <p className="text-xs text-gray-500 mb-1">Document ID</p>
                  <p className="text-sm font-mono text-gray-700 bg-gray-50 px-3 py-2 rounded">{errorModal.doc.doc_id}</p>
                </div>
                <div className="mb-4">
                  <p className="text-xs text-gray-500 mb-1">Error Message</p>
                  <p className="text-sm text-red-700 bg-red-50 px-3 py-2 rounded border border-red-100">
                    {errorModal.doc.error_message || 'Unknown error'}
                  </p>
                </div>
                <div className="mb-4">
                  <p className="text-xs text-gray-500 mb-1">Uploaded At</p>
                  <p className="text-sm text-gray-700">{formatDate(errorModal.doc.uploaded_at)}</p>
                </div>
                <div className="flex gap-3 mt-6">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(
                        `Document: ${errorModal.doc.filename}\nID: ${errorModal.doc.doc_id}\nError: ${errorModal.doc.error_message}\nTime: ${errorModal.doc.uploaded_at}`
                      )
                      alert('Error details copied to clipboard!')
                    }}
                    className="flex-1 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm font-medium"
                  >
                    Copy for Support
                  </button>
                  <button
                    onClick={() => setErrorModal({ open: false, doc: null })}
                    className="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors text-sm font-medium"
                  >
                    Close
                  </button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ProcessingHistoryPage
