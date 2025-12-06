import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import authService from '../services/authService'

function Register() {
  const [email, setEmail] = useState('')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const navigate = useNavigate()

  const handleRegister = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)
    
    try {
      const result = await authService.register(email, username, password)
      
      if (result.success) {
        setSuccess(result.message)
        // Redirect to login after 2 seconds
        setTimeout(() => {
          navigate('/login', { 
            state: { 
              message: result.requiresVerification 
                ? 'Please verify your email before logging in.' 
                : 'Registration successful! You can now login.'
            } 
          })
        }, 2000)
      } else {
        setError(result.message)
      }
    } catch (err) {
      console.error('Registration failed:', err)
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
            {/* The sliding background for the active tab */}
            <motion.div 
              className="absolute right-1 top-1 bottom-1 w-[calc(50%-4px)] bg-slate-500 rounded-full shadow-sm z-0"
              layoutId="activeTab"
            />
            <button 
              onClick={() => navigate('/login')}
              className="flex-1 py-2 text-sm font-medium rounded-full z-10 text-slate-500 relative transition-colors hover:text-slate-700"
            >
              Login
            </button>
            <button 
              className="flex-1 py-2 text-sm font-medium rounded-full z-10 text-white relative transition-colors"
            >
              Register
            </button>
          </div>
        </div>

        <p className="text-center text-gray-500 text-sm mb-8 px-4">
          Create an account to access your intelligent research assistant and manage your documents.
        </p>
        
        {/* Success message */}
        {success && (
          <motion.div 
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mb-4 p-3 bg-green-50 border border-green-200 rounded-2xl text-sm text-green-800"
          >
            {success}
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
        
        <form onSubmit={handleRegister} className="space-y-6">
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
              User name
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-all text-gray-700 placeholder-gray-400"
              placeholder="Enter your User name"
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
          
          <div className="pt-4">
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
              {loading ? 'Creating Account...' : 'Register'}
            </motion.button>
          </div>
        </form>
      </motion.div>
    </div>
  )
}

export default Register
