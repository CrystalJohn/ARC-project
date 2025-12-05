/**
 * Citation Card Component
 * Task #37: Display citations with document links
 * 
 * Shows citation details with clickable links to view source documents
 */

import { useState } from 'react'

function CitationCard({ citation, onViewDocument }) {
  const [expanded, setExpanded] = useState(false)

  const handleViewDocument = () => {
    if (onViewDocument) {
      onViewDocument(citation)
    }
  }

  return (
    <div className="text-xs bg-gray-50 p-3 rounded border border-gray-200 hover:border-blue-300 transition-colors">
      <div className="flex items-start gap-2">
        {/* Citation Number */}
        <span className="font-semibold text-blue-600 flex-shrink-0 text-sm">
          [{citation.id}]
        </span>
        
        <div className="flex-1 min-w-0">
          {/* Text Snippet */}
          <p className={`text-gray-700 mb-2 ${!expanded && 'line-clamp-2'}`}>
            {citation.text_snippet}
          </p>
          
          {/* Expand/Collapse for long snippets */}
          {citation.text_snippet.length > 150 && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-blue-600 hover:text-blue-700 text-xs mb-2"
            >
              {expanded ? '▼ Show less' : '▶ Show more'}
            </button>
          )}
          
          {/* Document Info */}
          <div className="flex flex-wrap items-center gap-2 text-gray-500 mb-2">
            <span className="flex items-center gap-1">
              📄 <span className="font-mono">{citation.doc_id.slice(0, 12)}...</span>
            </span>
            <span>•</span>
            <span>Page {citation.page}</span>
            <span>•</span>
            <span className="flex items-center gap-1">
              <span className={`inline-block w-2 h-2 rounded-full ${
                citation.score >= 0.7 ? 'bg-green-500' : 
                citation.score >= 0.5 ? 'bg-yellow-500' : 
                'bg-gray-400'
              }`}></span>
              {(citation.score * 100).toFixed(1)}% match
            </span>
          </div>
          
          {/* Action Buttons */}
          <div className="flex gap-2">
            <button
              onClick={handleViewDocument}
              className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors text-xs font-medium"
            >
              📖 View Document
            </button>
            <button
              onClick={() => {
                navigator.clipboard.writeText(citation.text_snippet)
              }}
              className="px-3 py-1 bg-gray-200 text-gray-700 rounded hover:bg-gray-300 transition-colors text-xs font-medium"
            >
              📋 Copy Text
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CitationCard
