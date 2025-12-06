import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminService } from '../services/adminService'
import { authService } from '../services/authService'
import { 
  Card, 
  CardBody, 
  Chip, 
  Progress,
  Checkbox,
  Spinner,
  Pagination
} from '@heroui/react'
import { motion, AnimatePresence } from 'framer-motion'

function AdminPage() {
  const navigate = useNavigate()
  const [documents, setDocuments] = useState([])
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState('all')
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [totalDocs, setTotalDocs] = useState(0)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [activeMenu, setActiveMenu] = useState('documents')

  useEffect(() => {
    fetchDocuments()
  }, [page, statusFilter])

  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(() => fetchDocuments(true), 5000)
    return () => clearInterval(interval)
  }, [autoRefresh, page, statusFilter])

  const PAGE_SIZE = 5 // Mỗi trang tối đa 5 dòng

  const fetchDocuments = async (silent = false) => {
    try {
      if (!silent) setLoading(true)
      setError(null)
      const data = await adminService.listDocuments({
        page,
        pageSize: PAGE_SIZE,
        status: statusFilter === 'all' ? null : statusFilter
      })
      setDocuments(data.items)
      setTotalPages(Math.ceil(data.total / PAGE_SIZE))
      setTotalDocs(data.total)
    } catch (err) {
      if (!silent) setError(err.message)
    } finally {
      if (!silent) setLoading(false)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') setDragActive(true)
    else if (e.type === 'dragleave') setDragActive(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    handleFiles(Array.from(e.dataTransfer.files))
  }

  const handleFileInput = (e) => {
    handleFiles(Array.from(e.target.files))
    e.target.value = ''
  }

  const handleFiles = async (files) => {
    const pdfFiles = files.filter(f => f.type === 'application/pdf' || f.name.toLowerCase().endsWith('.pdf'))
    if (pdfFiles.length === 0) return alert('Please select PDF files only')

    setUploading(true)
    setUploadProgress(pdfFiles.map(f => ({ filename: f.name, size: f.size, status: 'uploading', progress: 0 })))

    for (let i = 0; i < pdfFiles.length; i++) {
      try {
        setUploadProgress(prev => prev.map((p, idx) => idx === i ? { ...p, progress: 65 } : p))
        await adminService.uploadDocument(pdfFiles[i])
        setUploadProgress(prev => prev.map((p, idx) => idx === i ? { ...p, status: 'success', progress: 100 } : p))
      } catch (err) {
        setUploadProgress(prev => prev.map((p, idx) => idx === i ? { ...p, status: 'error', error: err.message } : p))
      }
    }
    setUploading(false)
    setTimeout(() => fetchDocuments(), 2000)
  }

  const removeUploadItem = (idx) => setUploadProgress(prev => prev.filter((_, i) => i !== idx))

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B'
    const k = 1024, sizes = ['B', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
  }

  const getStatusChip = (status) => {
    const config = {
      'UPLOADED': { color: 'default' },
      'IDP_RUNNING': { color: 'warning' },
      'EMBEDDING_DONE': { color: 'success' },
      'FAILED': { color: 'danger' }
    }[status] || { color: 'default' }
    return <Chip size="sm" color={config.color} variant="flat">{status}</Chip>
  }

  const handleLogout = async () => {
    await authService.logout()
    navigate('/login')
  }

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: '📊' },
    { id: 'chatbot', label: 'Chatbot', icon: '💬', onClick: () => navigate('/chat') },
    { id: 'documents', label: 'Document Management', icon: '📄' },
    { id: 'users', label: 'Users', icon: '👥' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
  ]

  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r flex flex-col">
        <div className="p-4 border-b">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">ARC</div>
            <div>
              <h1 className="font-semibold text-gray-800">ARC Chatbot</h1>
              <p className="text-xs text-gray-500">Researcher Portal</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-4 space-y-1">
          {menuItems.map((item) => (
            <button
              key={item.id}
              onClick={item.onClick || (() => setActiveMenu(item.id))}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                activeMenu === item.id ? 'bg-blue-50 text-blue-600 font-medium' : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="p-4 border-t space-y-1">
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-600 hover:bg-gray-100">
            <span>❓</span><span>Help</span>
          </button>
          <button onClick={handleLogout} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-600 hover:bg-gray-100">
            <span>🚪</span><span>Logout</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 p-8">
        <h1 className="text-2xl font-bold text-gray-800 mb-8">Document Management</h1>

        {/* Upload Section */}
        <Card className="mb-8">
          <CardBody className="p-6">
            <h2 className="text-lg font-semibold mb-4">Upload New Documents</h2>
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-all ${
                dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
              }`}
            >
              <div className="w-12 h-12 mx-auto mb-4 bg-green-100 rounded-full flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <p className="text-gray-800 font-medium mb-1">Drag & drop PDF files here</p>
              <p className="text-sm text-gray-500 mb-4">Supports multiple PDF files. Max size: 50MB per file.</p>
              <label className="inline-block cursor-pointer">
                <span className="px-6 py-2.5 bg-blue-500 hover:bg-blue-600 text-white font-medium rounded-lg transition-colors">
                  Browse Files
                </span>
                <input 
                  type="file" 
                  className="hidden" 
                  accept=".pdf" 
                  multiple 
                  disabled={uploading} 
                  onChange={handleFileInput} 
                />
              </label>
            </div>

            {/* Upload Progress */}
            <AnimatePresence>
              {uploadProgress.length > 0 && (
                <div className="mt-4 space-y-3">
                  {uploadProgress.map((item, idx) => (
                    <motion.div
                      key={idx}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, x: 100 }}
                      className={`flex items-center gap-4 p-4 rounded-lg ${
                        item.status === 'success' ? 'bg-green-50' : item.status === 'error' ? 'bg-red-50' : 'bg-gray-50'
                      }`}
                    >
                      <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center flex-shrink-0">
                        <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-800 truncate">{item.filename}</p>
                        {item.status === 'uploading' && <p className="text-xs text-gray-500">{formatFileSize(item.size * item.progress / 100)} of {formatFileSize(item.size)}</p>}
                        {item.status === 'success' && <p className="text-xs text-green-600">Upload Complete</p>}
                        {item.status === 'error' && <p className="text-xs text-red-600">Upload Failed</p>}
                      </div>
                      {item.status === 'uploading' && (
                        <div className="flex items-center gap-3 w-48">
                          <Progress value={item.progress} color="primary" size="sm" className="flex-1" />
                          <span className="text-sm text-gray-600 w-10">{item.progress}%</span>
                        </div>
                      )}
                      {item.status === 'success' && (
                        <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                          <svg className="w-4 h-4 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                          </svg>
                        </div>
                      )}
                      {item.status === 'error' && (
                        <div className="w-6 h-6 bg-red-500 rounded-full flex items-center justify-center">
                          <span className="text-white text-xs font-bold">!</span>
                        </div>
                      )}
                      {(item.status === 'success' || item.status === 'error') && (
                        <button onClick={() => removeUploadItem(idx)} className="text-gray-400 hover:text-gray-600">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                          </svg>
                        </button>
                      )}
                    </motion.div>
                  ))}
                </div>
              )}
            </AnimatePresence>
          </CardBody>
        </Card>

        {/* Documents Table */}
        <Card>
          <CardBody className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold">All Documents</h2>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Status:</span>
                  <select 
                    value={statusFilter} 
                    onChange={(e) => setStatusFilter(e.target.value)} 
                    className="w-40 px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All</option>
                    <option value="UPLOADED">Uploaded</option>
                    <option value="IDP_RUNNING">Processing</option>
                    <option value="EMBEDDING_DONE">Done</option>
                    <option value="FAILED">Failed</option>
                  </select>
                </div>
                <Checkbox isSelected={autoRefresh} onValueChange={setAutoRefresh} size="sm">
                  <span className="text-sm text-gray-600">Auto-refresh (5s)</span>
                </Checkbox>
                <button 
                  onClick={() => fetchDocuments()} 
                  disabled={loading}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
                >
                  {loading ? <Spinner size="sm" /> : '🔄'}
                </button>
              </div>
            </div>

            {loading && documents.length === 0 ? (
              <div className="flex items-center justify-center py-12"><Spinner size="lg" /></div>
            ) : error ? (
              <div className="p-6 bg-red-50 rounded-lg text-center">
                <p className="text-red-800">⚠️ {error}</p>
                <button 
                  onClick={() => fetchDocuments()} 
                  className="mt-2 px-4 py-1.5 text-sm text-red-600 hover:text-red-700 hover:bg-red-100 rounded-lg transition-colors"
                >
                  Try again
                </button>
              </div>
            ) : documents.length === 0 ? (
              <div className="py-12 text-center">
                <p className="text-gray-500">No documents found</p>
                <p className="text-sm text-gray-400 mt-1">Upload some PDFs to get started</p>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Filename</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Doc ID</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Page Count</th>
                        <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Chunk Count</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Upload Time</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {documents.map((doc) => (
                        <tr key={doc.doc_id} className="hover:bg-gray-50">
                          <td className="px-4 py-4 text-sm font-medium text-gray-800">{doc.filename}</td>
                          <td className="px-4 py-4 text-sm text-gray-500 font-mono">doc_{doc.doc_id.slice(0, 7)}</td>
                          <td className="px-4 py-4">{getStatusChip(doc.status)}</td>
                          <td className="px-4 py-4 text-center text-sm text-gray-600">{doc.page_count || 0}</td>
                          <td className="px-4 py-4 text-center text-sm text-gray-600">{doc.chunk_count || 0}</td>
                          <td className="px-4 py-4 text-sm text-gray-600">
                            {new Date(doc.uploaded_at).toLocaleString('en-US', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: true })}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div className="flex items-center justify-between mt-6 pt-4 border-t">
                  <p className="text-sm text-gray-600">
                    Showing <span className="font-medium">{(page - 1) * PAGE_SIZE + 1}-{Math.min(page * PAGE_SIZE, totalDocs)}</span> of <span className="font-medium">{totalDocs}</span>
                  </p>
                  {totalPages > 1 && (
                    <Pagination 
                      total={totalPages} 
                      page={page} 
                      onChange={setPage} 
                      showControls 
                      size="sm"
                      initialPage={1}
                      color="primary"
                    />
                  )}
                </div>
              </>
            )}
          </CardBody>
        </Card>
      </div>
    </div>
  )
}

export default AdminPage
