/**
 * Document Viewer Modal Component
 * Task #37: Display citations with document links
 * 
 * Modal to view document details and download/preview PDFs
 * - Admin: Full details (Document ID, Status, Chunks, Open in S3)
 * - Researcher: Simple view (Citation, Filename, Page, Download)
 */

import { useState, useEffect, useMemo } from 'react'
import { authService } from '../services/authService'

function DocumentViewerModal({ citation, onClose, query = '' }) {
  const [documentInfo, setDocumentInfo] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [isAdmin, setIsAdmin] = useState(false)
  const apiUrl = import.meta.env.VITE_API_URL

  // Extract keywords from query for highlighting
  const keywords = useMemo(() => {
    if (!query) return []
    // Remove Vietnamese stop words and short words
    const stopWords = ['là', 'gì', 'và', 'của', 'có', 'được', 'trong', 'cho', 'với', 'này', 'đó', 'các', 'một', 'những', 'như', 'thế', 'nào', 'khi', 'để', 'từ', 'về', 'theo', 'trên', 'the', 'is', 'are', 'what', 'how', 'and', 'or', 'a', 'an', 'to', 'of', 'in', 'for', 'on', 'with']
    return query
      .toLowerCase()
      .split(/\s+/)
      .filter(word => word.length > 2 && !stopWords.includes(word))
  }, [query])

  // Highlight keywords in text - returns JSX elements
  const highlightText = (text) => {
    if (!text || keywords.length === 0) return text
    
    // Escape special regex characters in keywords
    const escapeRegex = (str) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    
    // Build regex pattern for all keywords
    const pattern = keywords.map(escapeRegex).join('|')
    const regex = new RegExp(`(${pattern})`, 'gi')
    
    // Split text by keywords
    const parts = text.split(regex)
    
    return parts.map((part, i) => {
      // Check if this part matches any keyword
      const isKeyword = keywords.some(kw => part.toLowerCase() === kw.toLowerCase())
      if (isKeyword) {
        return <mark key={i} className="bg-yellow-200 px-0.5 rounded font-medium">{part}</mark>
      }
      return <span key={i}>{part}</span>
    })
  }

  useEffect(() => {
    checkUserRole()
  }, [])

  useEffect(() => {
    if (citation) {
      fetchDocumentInfo()
    }
  }, [citation])

  const checkUserRole = async () => {
    const user = await authService.getCurrentUser()
    setIsAdmin(user?.groups?.includes('admin') || false)
  }

  const fetchDocumentInfo = async () => {
    try {
      setLoading(true)
      const token = await authService.getAccessToken()
      
      // Use chat endpoint for regular users (doesn't require admin)
      const response = await fetch(`${apiUrl}/api/chat/document/${citation.doc_id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })

      if (!response.ok) {
        throw new Error('Failed to fetch document info')
      }

      const data = await response.json()
      setDocumentInfo(data)
    } catch (err) {
      console.error('Error fetching document:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async () => {
    try {
      const token = await authService.getAccessToken()
      
      // Generate presigned URL for download
      const response = await fetch(
        `${apiUrl}/api/admin/documents/${citation.doc_id}/download`,
        {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      )

      if (!response.ok) {
        throw new Error('Failed to generate download link')
      }

      const data = await response.json()
      
      // Open download link in new tab
      window.open(data.download_url, '_blank')
    } catch (err) {
      console.error('Download error:', err)
      alert('Failed to download document. Please try again.')
    }
  }

  const handleOpenInS3 = () => {
    // Construct S3 URL (for admin users with S3 access)
    const s3Url = `https://s3.console.aws.amazon.com/s3/object/arc-chatbot-documents-427995028618?prefix=uploads/${citation.doc_id}.pdf`
    window.open(s3Url, '_blank')
  }

  if (!citation) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold">Document Details</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl leading-none"
          >
            ×
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="flex flex-col items-center gap-3">
                <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                <p className="text-gray-600">Loading document info...</p>
              </div>
            </div>
          ) : error ? (
            <div className="space-y-4">
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">⚠️ {error}</p>
                <p className="text-sm text-red-600 mt-1">Document may not exist in database or was deleted.</p>
              </div>
              
              {/* Still show citation info even if document fetch failed */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">Citation Context</h3>
                <p className="text-sm text-blue-800 mb-2">{citation.text_snippet}</p>
                <div className="flex gap-4 text-xs text-blue-700">
                  <span>📄 Page {citation.page}</span>
                  <span>🎯 {(citation.score).toFixed(1)}% relevance</span>
                  <span>🔑 ID: {citation.doc_id?.slice(0, 8)}...</span>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Citation Context with Highlighted Keywords */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">📖 Citation Context</h3>
                <p className="text-sm text-blue-800 mb-3 leading-relaxed whitespace-pre-wrap">
                  {highlightText(citation.text_snippet)}
                </p>
                <div className="flex flex-wrap gap-3 text-xs text-blue-700 pt-2 border-t border-blue-200">
                  <span className="flex items-center gap-1">
                    <span>📄</span> Page {citation.page}
                  </span>
                  <span className="flex items-center gap-1">
                    <span>🎯</span> {citation.score?.toFixed(1)}% relevance
                  </span>
                  {keywords.length > 0 && (
                    <span className="flex items-center gap-1">
                      <span>🔍</span> Keywords: {keywords.slice(0, 3).join(', ')}
                    </span>
                  )}
                </div>
              </div>

              {/* Document Info - Different views for Admin vs Researcher */}
              {documentInfo && (
                <div className="space-y-3">
                  {isAdmin ? (
                    /* Admin View - Full details */
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Document ID</p>
                        <p className="text-sm font-mono bg-gray-100 px-2 py-1 rounded">
                          {citation.doc_id}
                        </p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Filename</p>
                        <p className="text-sm font-medium">{documentInfo.filename}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Status</p>
                        <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${
                          documentInfo.status === 'EMBEDDING_DONE' ? 'bg-green-100 text-green-800' :
                          documentInfo.status === 'IDP_RUNNING' ? 'bg-yellow-100 text-yellow-800' :
                          documentInfo.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {documentInfo.status}
                        </span>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Pages</p>
                        <p className="text-sm">{documentInfo.page_count || 'N/A'} pages</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Chunks</p>
                        <p className="text-sm">{documentInfo.chunk_count || 'N/A'} chunks</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Uploaded</p>
                        <p className="text-sm">
                          {new Date(documentInfo.uploaded_at).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                  ) : (
                    /* Researcher View - Simple info */
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Document</p>
                        <p className="text-sm font-medium">{documentInfo.filename}</p>
                      </div>
                      <div>
                        <p className="text-xs text-gray-500 mb-1">Location</p>
                        <p className="text-sm">Page {citation.page}</p>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons - Different for Admin vs Researcher */}
              <div className="flex gap-3 pt-4 border-t">
                <button
                  onClick={handleDownload}
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors font-medium"
                >
                  📥 Download PDF
                </button>
                {isAdmin && (
                  <button
                    onClick={handleOpenInS3}
                    className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                  >
                    🔗 Open in S3
                  </button>
                )}
              </div>

              {/* Note - Only for Admin */}
              {isAdmin && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-3">
                  <p className="text-xs text-gray-600">
                    💡 <strong>Note:</strong> PDF preview and download features require backend API support. 
                    The "Open in S3" button requires AWS console access.
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )
}

export default DocumentViewerModal
