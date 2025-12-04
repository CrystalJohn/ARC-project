import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import ChatPage from './pages/ChatPage'
import AdminPage from './pages/AdminPage'

function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Academic Research Chatbot
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            AI-powered research assistant for academic papers
          </p>
          
          <div className="grid md:grid-cols-3 gap-6 mt-12">
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-3xl mb-3">🔍</div>
              <h3 className="font-semibold mb-2">Smart Search</h3>
              <p className="text-sm text-gray-600">
                Vector-based semantic search across 750+ papers
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-3xl mb-3">💬</div>
              <h3 className="font-semibold mb-2">RAG Chat</h3>
              <p className="text-sm text-gray-600">
                Claude 3.5 Sonnet with citations and context
              </p>
            </div>
            
            <div className="bg-white p-6 rounded-lg shadow">
              <div className="text-3xl mb-3">📄</div>
              <h3 className="font-semibold mb-3">IDP Pipeline</h3>
              <p className="text-sm text-gray-600">
                Textract OCR + embeddings + Qdrant storage
              </p>
            </div>
          </div>

          <div className="mt-12 p-6 bg-blue-50 rounded-lg">
            <h2 className="text-lg font-semibold mb-2">Project Status</h2>
            <div className="text-left max-w-2xl mx-auto space-y-2 text-sm">
              <div className="flex items-center">
                <span className="text-green-600 mr-2">✅</span>
                <span>M0: Infrastructure Setup - COMPLETED</span>
              </div>
              <div className="flex items-center">
                <span className="text-green-600 mr-2">✅</span>
                <span>M1: IDP & Ingestion Pipeline - COMPLETED</span>
              </div>
              <div className="flex items-center">
                <span className="text-green-600 mr-2">✅</span>
                <span>M2: RAG Chat API - COMPLETED</span>
              </div>
              <div className="flex items-center">
                <span className="text-yellow-600 mr-2">🚧</span>
                <span>M3: Frontend & Monitoring - IN PROGRESS</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen">
        <Navbar />
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route 
            path="/chat" 
            element={
              <ProtectedRoute>
                <ChatPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/admin" 
            element={
              <ProtectedRoute requireAdmin={true}>
                <AdminPage />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </div>
    </BrowserRouter>
  )
}

export default App