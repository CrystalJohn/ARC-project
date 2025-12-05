import { useState, useEffect } from 'react'
import { adminService } from '../services/adminService'

function AdminPage() {
  const [documents, setDocuments] = useState([])
  const [dragActive, setDragActive] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [statusFilter, setStatusFilter] = useState(null)
  const [page, setPage] = useState(1)
  const [totalPages, setTotalPages] = useState(1)
  const [autoRefresh, setAutoRefresh] = useState(true)

  // Fetch documents on mount and when filters change
  useEffect(() => {
    fetchDocuments()
  }, [page, statusFilter])

  // Auto-refresh every 5 seconds if enabled
  useEffect(() => {
    if (!autoRefresh) return
    
    const interval = setInterval(() => {
      fetchDocuments(true) // Silent refresh
    }, 5000)
    
    return () => clearInterval(interval)
  }, [autoRefresh, page, statusFilter])

  const fetchDocuments = async (silent = false) => {
    try {
      if (!silent) setLoading(true)
      setError(null)
      
      const data = await adminService.listDocuments({
        page,
        pageSize: 20,
        status: statusFilter
      })
      
      setDocuments(data.items)
      setTotalPages(Math.ceil(data.total / data.page_size))
    } catch (err) {
      console.error('Error fetching documents:', err)
      if (!silent) setError(err.message)
    } finally {
      if (!silent) setLoading(false)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)
  }

  const handleFileInput = (e) => {
    const files = Array.from(e.target.files)
    handleFiles(files)
    e.target.value = '' // Reset input
  }

  const handleFiles = async (files) => {
    // Filter only PDF files
    const pdfFiles = files.filter(file => file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'))
    
    if (pdfFiles.length === 0) {
      alert('Please select PDF files only')
      return
    }

    if (pdfFiles.length !== files.length) {
      alert(`${files.length - pdfFiles.length} non-PDF file(s) were skipped`)
    }

    setUploading(true)
    const progress = pdfFiles.map(file => ({
      filename: file.name,
      status: 'uploading',
      progress: 0
    }))
    setUploadProgress(progress)

    // Upload files sequentially
    for (let i = 0; i < pdfFiles.length; i++) {
      const file = pdfFiles[i]
      
      try {
        // Update progress
        setUploadProgress(prev => prev.map((p, idx) => 
          idx === i ? { ...p, status: 'uploading', progress: 50 } : p
        ))

        const result = await adminService.uploadDocument(file)
        
        // Update progress - success
        setUploadProgress(prev => prev.map((p, idx) => 
          idx === i ? { ...p, status: 'success', progress: 100, doc_id: result.doc_id } : p
        ))
      } catch (err) {
        console.error(`Upload failed for ${file.name}:`, err)
        
        // Update progress - error
        setUploadProgress(prev => prev.map((p, idx) => 
          idx === i ? { ...p, status: 'error', progress: 0, error: err.message } : p
        ))
      }
    }

    setUploading(false)
    
    // Refresh document list after 2 seconds
    setTimeout(() => {
      fetchDocuments()
      setUploadProgress([])
    }, 2000)
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'UPLOADED': return 'bg-blue-100 text-blue-800'
      case 'IDP_RUNNING': return 'bg-yellow-100 text-yellow-800'
      case 'EMBEDDING_DONE': return 'bg-green-100 text-green-800'
      case 'FAILED': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <h1 className="text-xl font-semibold">Admin Dashboard</h1>
        <p className="text-sm text-gray-600">Upload and manage research documents</p>
      </div>

      <div className="max-w-6xl mx-auto p-6 space-y-6">
        {/* Upload Section */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Upload Documents</h2>
          
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
              dragActive ? 'border-blue-500 bg-blue-50' : 
              uploading ? 'border-gray-300 bg-gray-50' : 'border-gray-300'
            }`}
          >
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              stroke="currentColor"
              fill="none"
              viewBox="0 0 48 48"
            >
              <path
                d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                strokeWidth={2}
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <p className="mt-2 text-sm text-gray-600">
              {uploading ? 'Uploading...' : 'Drag and drop PDF files here, or'}
            </p>
            <label className="mt-2 inline-block">
              <span className={`px-4 py-2 rounded-md transition-colors ${
                uploading 
                  ? 'bg-gray-400 cursor-not-allowed' 
                  : 'bg-blue-600 hover:bg-blue-700 cursor-pointer'
              } text-white`}>
                {uploading ? 'Uploading...' : 'Browse Files'}
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
            <p className="mt-2 text-xs text-gray-500">
              PDF files only • Multiple files supported
            </p>
          </div>

          {/* Upload Progress */}
          {uploadProgress.length > 0 && (
            <div className="mt-4 space-y-2">
              {uploadProgress.map((item, idx) => (
                <div key={idx} className="bg-gray-50 rounded-lg p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700 truncate flex-1">
                      {item.filename}
                    </span>
                    <span className={`text-xs font-medium ml-2 ${
                      item.status === 'success' ? 'text-green-600' :
                      item.status === 'error' ? 'text-red-600' :
                      'text-blue-600'
                    }`}>
                      {item.status === 'success' ? '✓ Uploaded' :
                       item.status === 'error' ? '✗ Failed' :
                       'Uploading...'}
                    </span>
                  </div>
                  {item.status === 'uploading' && (
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${item.progress}%` }}
                      ></div>
                    </div>
                  )}
                  {item.status === 'error' && (
                    <p className="text-xs text-red-600 mt-1">{item.error}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Documents List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">Documents</h2>
              <div className="flex items-center gap-3">
                {/* Auto-refresh toggle */}
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={autoRefresh}
                    onChange={(e) => setAutoRefresh(e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-gray-600">Auto-refresh (5s)</span>
                </label>
                
                {/* Refresh button */}
                <button
                  onClick={() => fetchDocuments()}
                  disabled={loading}
                  className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded transition-colors disabled:opacity-50"
                >
                  🔄 Refresh
                </button>
              </div>
            </div>
            
            {/* Status Filter */}
            <div className="mt-3 flex gap-2">
              <button
                onClick={() => setStatusFilter(null)}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  statusFilter === null 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setStatusFilter('UPLOADED')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  statusFilter === 'UPLOADED' 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-blue-100 text-blue-800 hover:bg-blue-200'
                }`}
              >
                Uploaded
              </button>
              <button
                onClick={() => setStatusFilter('IDP_RUNNING')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  statusFilter === 'IDP_RUNNING' 
                    ? 'bg-yellow-600 text-white' 
                    : 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                }`}
              >
                Processing
              </button>
              <button
                onClick={() => setStatusFilter('EMBEDDING_DONE')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  statusFilter === 'EMBEDDING_DONE' 
                    ? 'bg-green-600 text-white' 
                    : 'bg-green-100 text-green-800 hover:bg-green-200'
                }`}
              >
                Done
              </button>
              <button
                onClick={() => setStatusFilter('FAILED')}
                className={`px-3 py-1 text-xs rounded-full transition-colors ${
                  statusFilter === 'FAILED' 
                    ? 'bg-red-600 text-white' 
                    : 'bg-red-100 text-red-800 hover:bg-red-200'
                }`}
              >
                Failed
              </button>
            </div>
          </div>
          
          {/* Loading State */}
          {loading && documents.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <div className="flex flex-col items-center gap-3">
                <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-gray-600">Loading documents...</p>
              </div>
            </div>
          ) : error ? (
            <div className="p-6">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">⚠️ {error}</p>
                <button
                  onClick={() => fetchDocuments()}
                  className="mt-2 text-sm text-red-600 hover:text-red-700 underline"
                >
                  Try again
                </button>
              </div>
            </div>
          ) : documents.length === 0 ? (
            <div className="p-12 text-center">
              <p className="text-gray-500">No documents found</p>
              <p className="text-sm text-gray-400 mt-1">Upload some PDFs to get started</p>
            </div>
          ) : (
            <>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Filename
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Status
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Pages
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Chunks
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Uploaded
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {documents.map((doc) => (
                      <tr key={doc.doc_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <span className="text-sm font-medium text-gray-900">
                              {doc.filename}
                            </span>
                            <span className="text-xs text-gray-500 font-mono">
                              {doc.doc_id.slice(0, 8)}...
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(doc.status)}`}>
                            {doc.status}
                          </span>
                          {doc.error_message && (
                            <p className="text-xs text-red-600 mt-1">{doc.error_message}</p>
                          )}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {doc.page_count || '-'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {doc.chunk_count || '-'}
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          {new Date(doc.uploaded_at).toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              
              {/* Pagination */}
              {totalPages > 1 && (
                <div className="px-6 py-4 border-t bg-gray-50 flex items-center justify-between">
                  <button
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={page === 1}
                    className="px-3 py-1 text-sm bg-white border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    ← Previous
                  </button>
                  <span className="text-sm text-gray-600">
                    Page {page} of {totalPages}
                  </span>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                    disabled={page === totalPages}
                    className="px-3 py-1 text-sm bg-white border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next →
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default AdminPage
