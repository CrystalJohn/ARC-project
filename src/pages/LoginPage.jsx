import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import authService from '../services/authService'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const location = useLocation()

  // Get message from navigation state (e.g., session expired)
  const stateMessage = location.state?.message

  // Check if user is already logged in and redirect based on role
  useEffect(() => {
    const checkAuth = async () => {
      if (authService.isAuthenticated()) {
        const user = await authService.getCurrentUser()
        if (user) {
          // User is already logged in, redirect based on role
          const isAdmin = user.groups?.includes('admin')
          if (isAdmin) {
            navigate('/admin', { replace: true })
          } else {
            navigate('/chat', { replace: true })
          }
        }
      }
    }
    checkAuth()
  }, [navigate])

  const handleLogin = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      // Logout any existing session first
      await authService.logout()
      
      // Then login with new credentials
      const result = await authService.login(email, password)
      console.log('Login successful:', result)
      
      // Redirect based on user role
      const isAdmin = result.groups?.includes('admin')
      if (isAdmin) {
        navigate('/admin', { replace: true })
      } else {
        navigate('/chat', { replace: true })
      }
    } catch (err) {
      console.error('Login failed:', err)
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold mb-6 text-center">Academic Research Chatbot</h1>
        <h2 className="text-xl mb-4 text-center text-gray-600">Login</h2>
        
        {/* State message (e.g., session expired) */}
        {stateMessage && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-md text-sm text-blue-800">
            {stateMessage}
          </div>
        )}

        {/* Error message */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md text-sm text-red-800">
            {error}
          </div>
        )}
        
        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="researcher@example.com"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="••••••••"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className={`w-full py-2 rounded-md transition-colors ${
              loading
                ? 'bg-gray-400 cursor-not-allowed'
                : 'bg-blue-600 hover:bg-blue-700 text-white'
            }`}
          >
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>
        
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-600">
            Test Credentials:
          </p>
          <p className="text-xs text-gray-500 mt-1">
            Admin: admin@arc.com / Researcher: researcher@arc.com
          </p>
          <p className="text-xs text-gray-400 mt-2">
            ✅ Cognito integration active (M3 Task #35)
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
