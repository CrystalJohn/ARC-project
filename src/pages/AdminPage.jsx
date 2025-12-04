import { useState } from 'react'

function AdminPage() {
  const [documents, setDocuments] = useState([
    { id: '1', filename: 'sample-paper.pdf', status: 'EMBEDDING_DONE', uploaded_at: '2024-12-03T10:30:00Z' },
    { id: '2', filename: 'research-doc.pdf', status: 'IDP_RUNNING', uploaded_at: '2024-12-03T11:15:00Z' },
  ])
  const [dragActive, setDragActive] = useState(false)

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
    
    // TODO: Implement file upload in M3
    const files = e.dataTransfer.files
    console.log('Files dropped:', files)
    alert(`Dropped ${files.length} file(s). Upload API integration coming in M3.`)
  }

  const handleFileInput = (e) => {
    // TODO: Implement file upload in M3
    const files = e.target.files
    console.log('Files selected:', files)
    alert(`Selected ${files.length} file(s). Upload API integration coming in M3.`)
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
              dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300'
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
              Drag and drop PDF files here, or
            </p>
            <label className="mt-2 inline-block">
              <span className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer">
                Browse Files
              </span>
              <input
                type="file"
                className="hidden"
                accept=".pdf"
                multiple
                onChange={handleFileInput}
              />
            </label>
            <p className="mt-2 text-xs text-gray-500">
              Placeholder - Upload API integration in M3
            </p>
          </div>
        </div>

        {/* Documents List */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b">
            <h2 className="text-lg font-semibold">Documents</h2>
          </div>
          
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
                    Uploaded
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {documents.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 text-sm text-gray-900">
                      {doc.filename}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(doc.status)}`}>
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {new Date(doc.uploaded_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          <div className="px-6 py-4 border-t bg-gray-50">
            <p className="text-xs text-gray-500">
              Placeholder data - API integration in M3
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AdminPage
