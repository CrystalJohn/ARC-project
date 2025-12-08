import { useState, useMemo } from 'react'
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

  // Password validation rules (Cognito default requirements)
  const passwordRules = useMemo(() => {
    return {
      minLength: password.length >= 8,
      hasUppercase: /[A-Z]/.test(password),
      hasLowercase: /[a-z]/.test(password),
      hasNumber: /[0-9]/.test(password),
      hasSpecial: /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password),
    }
  }, [password])

  // Calculate password strength
  const passwordStrength = useMemo(() => {
    const rules = Object.values(passwordRules)
    const passed = rules.filter(Boolean).length
    if (passed === 0) return { level: 0, label: '', color: '' }
    if (passed <= 2) return { level: 1, label: 'Weak', color: 'bg-red-500' }
    if (passed <= 3) return { level: 2, label: 'Fair', color: 'bg-orange-500' }
    if (passed <= 4) return { level: 3, label: 'Good', color: 'bg-yellow-500' }
    return { level: 4, label: 'Strong', color: 'bg-green-500' }
  }, [passwordRules])

  const isPasswordValid = Object.values(passwordRules).every(Boolean)

  const handleRegister = async (e) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!isPasswordValid) {
      setError('Please meet all password requirements')
      return
    }

    setLoading(true)

    try {
      const result = await authService.register(email, username, password)

      if (result.success) {
        setSuccess(result.message)
        setTimeout(() => {
          if (result.requiresVerification) {
            // Redirect to verify email page with displayName
            navigate('/verify-email', { state: { email, displayName: username } })
          } else {
            navigate('/login', {
              state: { message: 'Registration successful! You can now login.' },
            })
          }
        }, 1500)
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
    <div className="absolute inset-0 flex items-center justify-center bg-white overflow-y-auto py-8">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md px-8"
      >
        <h1 className="text-2xl font-semibold text-center mb-8 text-gray-800">
          Welcome to ARC-Chatbot
        </h1>

        {/* Toggle Switch */}
        <div className="flex justify-center mb-8">
          <div className="bg-blue-50 p-1 rounded-full flex w-64 relative">
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
            <button className="flex-1 py-2 text-sm font-medium rounded-full z-10 text-white relative transition-colors">
              Register
            </button>
          </div>
        </div>

        <p className="text-center text-gray-500 text-sm mb-8 px-4">
          Create an account to access your intelligent research assistant and manage your
          documents.
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

        <form onSubmit={handleRegister} className="space-y-5">
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
              Display Name
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-full focus:outline-none focus:ring-2 focus:ring-blue-200 focus:border-blue-400 transition-all text-gray-700 placeholder-gray-400"
              placeholder="Enter your Display Name"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2 ml-1">Password</label>
            <div className="relative">
              <input
                type={showPassword ? 'text' : 'password'}
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
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
                    <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68" />
                    <path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7c.44 0 .87-.03 1.28-.09" />
                    <line x1="2" y1="2" x2="22" y2="22" />
                  </svg>
                ) : (
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                )}
              </button>
            </div>

            {/* Password Strength Indicator */}
            {password && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                className="mt-3 space-y-2"
              >
                {/* Strength Bar */}
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden flex gap-1">
                    {[1, 2, 3, 4].map((level) => (
                      <div
                        key={level}
                        className={`flex-1 h-full rounded-full transition-all duration-300 ${
                          passwordStrength.level >= level ? passwordStrength.color : 'bg-gray-200'
                        }`}
                      />
                    ))}
                  </div>
                  <span
                    className={`text-xs font-medium ${
                      passwordStrength.level <= 1
                        ? 'text-red-500'
                        : passwordStrength.level === 2
                          ? 'text-orange-500'
                          : passwordStrength.level === 3
                            ? 'text-yellow-600'
                            : 'text-green-500'
                    }`}
                  >
                    {passwordStrength.label}
                  </span>
                </div>

                {/* Requirements Checklist */}
                <div className="grid grid-cols-2 gap-1 text-xs">
                  <div
                    className={`flex items-center gap-1.5 ${passwordRules.minLength ? 'text-green-600' : 'text-gray-400'}`}
                  >
                    {passwordRules.minLength ? (
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                    <span>8+ characters</span>
                  </div>
                  <div
                    className={`flex items-center gap-1.5 ${passwordRules.hasUppercase ? 'text-green-600' : 'text-gray-400'}`}
                  >
                    {passwordRules.hasUppercase ? (
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                    <span>Uppercase (A-Z)</span>
                  </div>
                  <div
                    className={`flex items-center gap-1.5 ${passwordRules.hasLowercase ? 'text-green-600' : 'text-gray-400'}`}
                  >
                    {passwordRules.hasLowercase ? (
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                    <span>Lowercase (a-z)</span>
                  </div>
                  <div
                    className={`flex items-center gap-1.5 ${passwordRules.hasNumber ? 'text-green-600' : 'text-gray-400'}`}
                  >
                    {passwordRules.hasNumber ? (
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                    <span>Number (0-9)</span>
                  </div>
                  <div
                    className={`flex items-center gap-1.5 col-span-2 ${passwordRules.hasSpecial ? 'text-green-600' : 'text-gray-400'}`}
                  >
                    {passwordRules.hasSpecial ? (
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    ) : (
                      <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                    <span>Special character (!@#$%^&*)</span>
                  </div>
                </div>
              </motion.div>
            )}
          </div>

          <div className="pt-2">
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              type="submit"
              disabled={loading || !isPasswordValid}
              className={`w-full py-3 rounded-full font-medium transition-colors shadow-sm ${
                loading || !isPasswordValid
                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                  : 'bg-blue-500 hover:bg-blue-600 text-white'
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
