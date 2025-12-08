import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import LoginPage from './pages/LoginPage'
import Register from './pages/Register'
import VerifyEmail from './pages/VerifyEmail'
import ChatPage from './pages/ChatPage'
import AdminPage from './pages/AdminPage'
import ProcessingHistoryPage from './pages/ProcessingHistoryPage'

function App() {
  return (
    <div className="min-h-screen">
      <Routes>
        {/* Root redirects to login */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<Register />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
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
        <Route
          path="/admin/processing-history"
          element={
            <ProtectedRoute requireAdmin={true}>
              <ProcessingHistoryPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  )
}

export default App
