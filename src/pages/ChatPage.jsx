import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { authService } from '../services/authService'
import { chatService } from '../services/chatService'
import { Spinner } from '@heroui/react'
import { motion, AnimatePresence } from 'framer-motion'
import DocumentViewerModal from '../components/DocumentViewerModal'

function ChatPage() {
  const navigate = useNavigate()
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
  const [selectedQuery, setSelectedQuery] = useState('')
  const [user, setUser] = useState(null)
  const [showAccountMenu, setShowAccountMenu] = useState(false)
  const [activeMenu, setActiveMenu] = useState('chat')
  const messagesEndRef = useRef(null)

  useEffect(() => {
    loadUser()
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadUser = async () => {
    const currentUser = await authService.getCurrentUser()
    setUser(currentUser)
  }

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
      const data = await chatService.sendChatMessage({
        query: userQuery,
        conversationId,
        userId: user?.username || 'anonymous',
        template: 'default',
        topK: 3,  // Only top 3 most relevant citations
        includeHistory: true
      })
      
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

  const handleViewDocument = (citation, query) => {
    setSelectedCitation(citation)
    setSelectedQuery(query || '')
  }

  const handleCloseModal = () => {
    setSelectedCitation(null)
    setSelectedQuery('')
  }

  const handleLogout = async () => {
    await authService.logout()
    navigate('/login')
  }

  const handleNewChat = () => {
    setMessages([{
      role: 'assistant',
      content: 'Hello! I can help you search through academic research papers. Ask me anything!',
      timestamp: new Date().toISOString()
    }])
    setConversationId(null)
    setError(null)
  }

  const menuItems = [
    { id: 'chat', label: 'Chat', icon: '💬' },
    { id: 'history', label: 'History', icon: '📜' },
    { id: 'admin', label: 'Admin Panel', icon: '⚙️', onClick: () => navigate('/admin'), adminOnly: true },
  ]

  const isAdmin = user?.groups?.includes('admin')

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className="w-64 bg-white border-r flex flex-col">
        {/* Logo */}
        <div className="p-4 border-b">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center text-white font-bold text-sm">
              ARC
            </div>
            <div>
              <h1 className="font-semibold text-gray-800">ARC Chatbot</h1>
              <p className="text-xs text-gray-500">Research Assistant</p>
            </div>
          </div>
        </div>

        {/* New Chat Button */}
        <div className="p-4">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-500 hover:bg-blue-600 text-white rounded-lg transition-colors"
          >
            <span>➕</span>
            <span>New Chat</span>
          </button>
        </div>

        {/* Menu */}
        <nav className="flex-1 px-4 space-y-1">
          {menuItems.map((item) => {
            if (item.adminOnly && !isAdmin) return null
            return (
              <button
                key={item.id}
                onClick={item.onClick || (() => setActiveMenu(item.id))}
                className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                  activeMenu === item.id
                    ? 'bg-blue-50 text-blue-600 font-medium'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </button>
            )
          })}
        </nav>

        {/* Bottom Menu */}
        <div className="p-4 border-t space-y-1">
          <button className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-600 hover:bg-gray-100">
            <span>❓</span>
            <span>Help</span>
          </button>
          <button 
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-600 hover:bg-gray-100"
          >
            <span>🚪</span>
            <span>Logout</span>
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b px-6 py-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-800">Chat</h2>
          
          {/* Account Menu */}
          <div className="relative">
            <button
              onClick={() => setShowAccountMenu(!showAccountMenu)}
              className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-gray-100 transition-colors"
            >
              <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center font-medium text-sm">
                {user?.email?.charAt(0).toUpperCase() || 'U'}
              </div>
              <svg className="w-4 h-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {/* Dropdown */}
            {showAccountMenu && (
              <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-lg border py-2 z-50">
                <div className="px-4 py-3 border-b">
                  <p className="text-sm font-medium text-gray-800">{user?.username || 'User'}</p>
                  <p className="text-xs text-gray-500">{user?.email || 'No email'}</p>
                  {isAdmin && (
                    <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 text-blue-600 text-xs rounded-full">
                      Admin
                    </span>
                  )}
                </div>
                <button
                  onClick={() => { setShowAccountMenu(false) }}
                  className="w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 flex items-center gap-2"
                >
                  <span>👤</span>
                  <span>Account Settings</span>
                </button>
                <button
                  onClick={() => { setShowAccountMenu(false); handleLogout() }}
                  className="w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
                >
                  <span>🚪</span>
                  <span>Logout</span>
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <AnimatePresence>
            {messages.map((msg, idx) => (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className="max-w-3xl w-full">
                  {msg.role === 'user' && (
                    <div className="flex justify-end mb-2">
                      <span className="text-sm font-medium text-gray-700">You</span>
                    </div>
                  )}

                  {msg.role === 'assistant' && (
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3z"/>
                        </svg>
                      </div>
                      <span className="text-sm font-medium text-gray-700">ARC Chatbot</span>
                    </div>
                  )}

                  <div
                    className={`px-4 py-3 rounded-2xl ${
                      msg.role === 'user'
                        ? 'bg-gray-100 text-gray-800'
                        : msg.isError
                        ? 'bg-red-50 border border-red-200 text-red-800'
                        : 'bg-white border border-gray-200'
                    }`}
                  >
                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                    
                    {msg.citations && msg.citations.length > 0 && (
                      <div className="mt-4 pt-3 border-t border-gray-100 space-y-2">
                        <p className="text-xs text-gray-500 mb-2">📚 Sources:</p>
                        {msg.citations.map((citation) => {
                          // Find the user query that triggered this response
                          const userQuery = idx > 0 && messages[idx - 1]?.role === 'user' 
                            ? messages[idx - 1].content 
                            : ''
                          return (
                          <div 
                            key={citation.id} 
                            onClick={() => handleViewDocument(citation, userQuery)}
                            className="p-3 bg-blue-50 border border-blue-100 rounded-lg cursor-pointer hover:bg-blue-100 transition-colors"
                          >
                            <p className="text-xs font-medium text-blue-700 mb-1">
                              {citation.doc_id?.slice(0, 8) || 'Document'}...
                            </p>
                            <p className="text-xs text-blue-600 line-clamp-2 mb-2">
                              {citation.text_snippet}
                            </p>
                            <div className="flex items-center gap-3 text-xs text-blue-500">
                              <span className="px-1.5 py-0.5 bg-blue-200 rounded">[{citation.id}]</span>
                              {citation.page && <span>Page {citation.page}</span>}
                              {citation.score && <span>Score: {Math.round(citation.score)}%</span>}
                            </div>
                          </div>
                        )})}
                      </div>
                    )}
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {loading && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                  <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10.394 2.08a1 1 0 00-.788 0l-7 3a1 1 0 000 1.84L5.25 8.051a.999.999 0 01.356-.257l4-1.714a1 1 0 11.788 1.838L7.667 9.088l1.94.831a1 1 0 00.787 0l7-3a1 1 0 000-1.838l-7-3z"/>
                  </svg>
                </div>
                <div className="bg-white border border-gray-200 px-4 py-3 rounded-2xl">
                  <div className="flex items-center gap-2">
                    <Spinner size="sm" />
                    <span className="text-sm text-gray-500">Thinking...</span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="bg-white px-6 py-6 border-t">
          <div className="max-w-4xl mx-auto">
            <form onSubmit={handleSend} className="relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Enter a prompt here"
                disabled={loading}
                className="w-full h-14 pl-5 pr-14 text-sm text-gray-700 bg-white border border-blue-200 rounded-full focus:outline-none focus:border-blue-400 focus:ring-2 focus:ring-blue-100 transition-all placeholder:text-gray-400"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="absolute right-2 top-1/2 -translate-y-1/2 w-10 h-10 flex items-center justify-center bg-blue-400 hover:bg-blue-500 disabled:bg-gray-300 text-white rounded-full transition-colors"
              >
                {loading ? (
                  <Spinner size="sm" color="white" />
                ) : (
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                  </svg>
                )}
              </button>
            </form>
            
            {error && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg"
              >
                <p className="text-sm text-red-800">⚠️ {error}</p>
              </motion.div>
            )}
          </div>
        </div>
      </div>

      {selectedCitation && (
        <DocumentViewerModal 
          citation={selectedCitation} 
          onClose={handleCloseModal} 
          query={selectedQuery}
        />
      )}
    </div>
  )
}

export default ChatPage
