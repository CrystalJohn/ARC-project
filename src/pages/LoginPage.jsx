import { useState, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import authService from '../services/authService'

function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const location = useLocation()

  // Get message from navigation state (e.g., session expired, need to register)
  const stateMessage = location.state?.message
  const showRegisterHint = location.state?.showRegisterHint

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
      
      // Check if user needs to confirm email
      if (err.message?.includes('CONFIRM_SIGN_UP') || err.message?.includes('not confirmed')) {
        navigate('/verify-email', { state: { email } })
        return
      }
      
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="absolute inset-0 flex items-center justify-center bg-white">
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md px-8"
      >
        <h1 className="text-2xl font-semibold text-center mb-8 text-gray-800">Welcome to ARC-Chatbot</h1>
        
        {/* Toggle Switch */}
        <div className="flex justify-center mb-8">
          <div className="bg-blue-50 p-1 rounded-full flex w-64 relative">
            <motion.div 
              className="absolute left-1 top-1 bottom-1 w-[calc(50%-4px)] bg-slate-500 rounded-full shadow-sm z-0"
              layoutId="activeTab"
              transition={{ type: "spring", stiffness: 300, damping: 30 }}
            />
            <button 
              className="flex-1 py-2 text-sm font-medium rounded-full z-10 text-white relative transition-colors"
            >
              Login
            </button>
            <button 
              onClick={() => navigate('/register')}
              className="flex-1 py-2 text-sm font-medium rounded-full z-10 text-slate-500 relative transition-colors hover:text-slate-700"
            >
              Register
            </button>
          </div>
        </div>

        <p className="text-center text-gray-500 text-sm mb-8 px-4">
          Sign in to access your intelligent research assistant and manage your documents.
        </p>
        
        {/* State message (e.g., session expired, need to register) */}
        {stateMessage && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-2xl text-sm text-blue-800"
          >
            <p>{stateMessage}</p>
            {showRegisterHint && (
              <p className="mt-2">
                Don't have an account?{' '}
                <button 
                  onClick={() => navigate('/register')}
                  className="font-semibold text-blue-600 hover:text-blue-800 underline"
                >
                  Register here
                </button>
              </p>
            )}
          </motion.div>
        )}

        {/* Error message */}
        {error && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mb-4 p-3 bg-red-50 border border-red-200 rounded-2xl text-sm text-red-800"
          >
            {error}
          </motion.div>
        )}
        
        <form onSubmit={handleLogin} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2 ml-1">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-all text-gray-700 placeholder-gray-400"
              placeholder="Enter your Email Address"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2 ml-1">
              Password
            </label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-all text-gray-700 placeholder-gray-400 pr-12"
                placeholder="Enter your Password"
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 focus:outline-none"
              >
                {showPassword ? (
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7c.44 0 .87-.03 1.28-.09"/><line x1="2" y1="2" x2="22" y2="22"/></svg>
                ) : (
                  <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                )}
              </button>
            </div>
          </div>

          <div className="flex items-center justify-between px-1">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 text-slate-600 focus:ring-slate-500 border-gray-300 rounded"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-600">
                Remember me
              </label>
            </div>

            <div className="text-sm">
              <a href="#" className="font-medium text-gray-600 hover:text-gray-900">
                Forgot Password?
              </a>
            </div>
          </div>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={loading}
            className={`w-full py-3 rounded-full text-slate-700 font-medium transition-colors shadow-sm ${
              loading
                ? 'bg-blue-100 cursor-not-allowed'
                : 'bg-blue-100 hover:bg-blue-200'
            }`}
          >
            {loading ? 'Signing in...' : 'Login'}
          </motion.button>
        </form>
      </motion.div>
    </div>
  )
}

export default LoginPage