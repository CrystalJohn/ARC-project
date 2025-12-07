import { Navigate } from 'react-router-dom'
import authService from '../services/authService'

/**
 * ProtectedRoute - Wrapper component for routes that require authentication
 * Redirects to login if user is not authenticated
 */
function ProtectedRoute({ children, requireAdmin = false }) {
  const isAuthenticated = authService.isAuthenticated()
  const isAdmin = authService.isAdmin()

  // Not authenticated - redirect to login with register prompt
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ 
      message: 'Please login or register to use the chatbot system.',
      showRegisterHint: true 
    }} />
  }

  // Requires admin but user is not admin - redirect to chat
  if (requireAdmin && !isAdmin) {
    return <Navigate to="/chat" replace state={{ message: 'Access denied. Admin role required.' }} />
  }

  // Authenticated and authorized - render children
  return children
}

export default ProtectedRoute
