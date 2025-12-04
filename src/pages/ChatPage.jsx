import { useState } from 'react'

function ChatPage() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Hello! I can help you search through academic research papers. Ask me anything!' }
  ])
  const [input, setInput] = useState('')

  const handleSend = (e) => {
    e.preventDefault()
    if (!input.trim()) return

    // Add user message
    const userMessage = { role: 'user', content: input }
    setMessages([...messages, userMessage])
    
    // TODO: Call RAG API in M3
    // Temporary mock response
    setTimeout(() => {
      const assistantMessage = {
        role: 'assistant',
        content: `You asked: "${input}". This is a placeholder response. RAG API integration coming in M3.`
      }
      setMessages(prev => [...prev, assistantMessage])
    }, 500)
    
    setInput('')
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b px-6 py-4">
        <h1 className="text-xl font-semibold">Research Chat</h1>
        <p className="text-sm text-gray-600">Ask questions about academic papers</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-2xl px-4 py-3 rounded-lg ${
                msg.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-white border border-gray-200'
              }`}
            >
              <p className="text-sm">{msg.content}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Input */}
      <div className="bg-white border-t px-6 py-4">
        <form onSubmit={handleSend} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about research papers..."
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Send
          </button>
        </form>
        <p className="text-xs text-gray-500 mt-2">
          Placeholder - RAG API integration in M3
        </p>
      </div>
    </div>
  )
}

export default ChatPage
