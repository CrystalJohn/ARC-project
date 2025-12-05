import { useState, useEffect, useRef } from 'react'
import { authService } from '../services/authService'
import { chatService } from '../services/chatService'
import CitationCard from '../components/CitationCard'
import DocumentViewerModal from '../components/DocumentViewerModal'

function ChatPage() {
  const [messages, setMessages] = useState([
    { 
      role: 'assistant', 
      content: 'Hello! I can help you search through academic research papers. Ask me anything!',
      timestamp: new Date().toISOString()
    }
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [conversationId, setConversationId] = useState(null)
  const [selectedCitation, setSelectedCitation] = useState(null)
  const messagesEndRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = async (e) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userQuery = input
    const userMessage = { 
      role: 'user', 
      content: userQuery,
      timestamp: new Date().toISOString()
    }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const user = await authService.getCurrentUser()
      
      const data = await chatService.sendChatMessage({
        query: userQuery,
        conversationId,
        userId: user?.username || 'anonymous',
        template: 'default',
        topK: 5,
        includeHistory: true
      })
      
      // Set conversation ID for future messages
      if (data.conversation_id && !conversationId) {
        setConversationId(data.conversation_id)
      }

      const assistantMessage = {
        role: 'assistant',
        content: data.answer,
        citations: data.citations || [],
        usage: data.usage,
        model: data.model,
        timestamp: data.timestamp
      }
      
      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      console.error('Chat error:', err)
      setError(err.message || 'Failed to get response. Please try again.')
      
      // Add error message to chat
      const errorMessage = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${err.message}. Please try again.`,
        isError: true,
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setLoading(false)
    }
  }

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp)
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
  }

  const handleViewDocument = (citation) => {
    setSelectedCitation(citation)
  }

  const handleCloseModal = () => {
    setSelectedCitation(null)
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <h1 className="text-xl font-semibold">Research Chat</h1>
        <p className="text-sm text-gray-600">Ask questions about academic papers</p>
        {conversationId && (
          <p className="text-xs text-gray-400 mt-1">
            Conversation ID: {conversationId.slice(0, 8)}...
          </p>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div className="max-w-3xl">
              <div
                className={`px-4 py-3 rounded-lg ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : msg.isError
                    ? 'bg-red-50 border border-red-200 text-red-800'
                    : 'bg-white border border-gray-200'
                }`}
              >
                <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                
                {/* Citations */}
                {msg.citations && msg.citations.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <p className="text-xs font-semibold text-gray-600 mb-2">
                      📚 Sources ({msg.citations.length}):
                    </p>
                    <div className="space-y-2">
                      {msg.citations.map((citation) => (
                        <CitationCard
                          key={citation.id}
                          citation={citation}
                          onViewDocument={handleViewDocument}
                        />
                      ))}
                    </div>
                  </div>
                )}

                {/* Metadata */}
                {msg.usage && (
                  <div className="mt-2 pt-2 border-t border-gray-200">
                    <p className="text-xs text-gray-500">
                      {msg.model} • {msg.usage.total_tokens} tokens • {formatTimestamp(msg.timestamp)}
                    </p>
                  </div>
                )}
              </div>
              
              {/* Timestamp for user messages */}
              {msg.role === 'user' && (
                <p className="text-xs text-gray-400 mt-1 text-right">
                  {formatTimestamp(msg.timestamp)}
                </p>
              )}
            </div>
          </div>
        ))}

        {/* Loading indicator */}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-gray-200 px-4 py-3 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-sm text-gray-500">Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Error banner */}
      {error && (
        <div className="bg-red-50 border-t border-red-200 px-6 py-3">
          <p className="text-sm text-red-800">
            ⚠️ {error}
          </p>
        </div>
      )}

      {/* Input */}
      <div className="bg-white border-t px-6 py-4">
        <form onSubmit={handleSend} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about research papers..."
            disabled={loading}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Powered by Claude 3.5 Sonnet • RAG with citations
        </p>
      </div>

      {/* Document Viewer Modal */}
      {selectedCitation && (
        <DocumentViewerModal
          citation={selectedCitation}
          onClose={handleCloseModal}
        />
      )}
    </div>
  )
}

export default ChatPage
