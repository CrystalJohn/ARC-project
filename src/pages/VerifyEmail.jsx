import { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { confirmSignUp, resendSignUpCode } from 'aws-amplify/auth'

function VerifyEmail() {
  const [code, setCode] = useState(['', '', '', '', '', ''])
  const [loading, setLoading] = useState(false)
  const [resending, setResending] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [countdown, setCountdown] = useState(0)
  const inputRefs = useRef([])
  const navigate = useNavigate()
  const location = useLocation()

  const email = location.state?.email || ''
  const displayName = location.state?.displayName || ''

  const API_URL = import.meta.env.VITE_API_URL

  useEffect(() => {
    if (!email) {
      navigate('/register')
    }
  }, [email, navigate])

  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000)
      return () => clearTimeout(timer)
    }
  }, [countdown])

  const handleChange = (index, value) => {
    if (!/^\d*$/.test(value)) return

    const newCode = [...code]
    newCode[index] = value.slice(-1)
    setCode(newCode)

    // Auto-focus next input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (e) => {
    e.preventDefault()
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (pastedData) {
      const newCode = pastedData.split('').concat(Array(6).fill('')).slice(0, 6)
      setCode(newCode)
      inputRefs.current[Math.min(pastedData.length, 5)]?.focus()
    }
  }

  const handleVerify = async (e) => {
    e.preventDefault()
    const verificationCode = code.join('')

    if (verificationCode.length !== 6) {
      setError('Please enter the 6-digit code')
      return
    }

    setLoading(true)
    setError('')

    try {
      await confirmSignUp({
        username: email,
        confirmationCode: verificationCode,
      })

      // TODO: Enable welcome email feature when SES is configured
      // try {
      //   await fetch(`${API_URL}/api/auth/send-welcome-email`, {
      //     method: 'POST',
      //     headers: { 'Content-Type': 'application/json' },
      //     body: JSON.stringify({
      //       email: email,
      //       display_name: displayName || email.split('@')[0],
      //     }),
      //   })
      // } catch (emailErr) {
      //   console.warn('Welcome email could not be sent:', emailErr)
      // }

      setSuccess('Email verified successfully!')
      setTimeout(() => {
        navigate('/login', {
          state: { message: 'Email verified! You can now login.' },
        })
      }, 2000)
    } catch (err) {
      console.error('Verification error:', err)
      if (err.name === 'CodeMismatchException') {
        setError('Invalid verification code. Please try again.')
      } else if (err.name === 'ExpiredCodeException') {
        setError('Code has expired. Please request a new one.')
      } else {
        setError(err.message || 'Verification failed. Please try again.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleResendCode = async () => {
    if (countdown > 0) return

    setResending(true)
    setError('')

    try {
      await resendSignUpCode({ username: email })
      setSuccess('New verification code sent to your email!')
      setCountdown(60)
      setTimeout(() => setSuccess(''), 3000)
    } catch (err) {
      console.error('Resend error:', err)
      setError('Failed to resend code. Please try again.')
    } finally {
      setResending(false)
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
        <h1 className="text-2xl font-semibold text-center mb-4 text-gray-800">Verify Your Email</h1>

        <p className="text-center text-gray-500 text-sm mb-8">
          We've sent a 6-digit verification code to
          <br />
          <span className="font-medium text-gray-700">{email}</span>
        </p>

        {/* Success message */}
        {success && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mb-4 p-3 bg-green-50 border border-green-200 rounded-2xl text-sm text-green-800 text-center"
          >
            {success}
          </motion.div>
        )}

        {/* Error message */}
        {error && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            className="mb-4 p-3 bg-red-50 border border-red-200 rounded-2xl text-sm text-red-800 text-center"
          >
            {error}
          </motion.div>
        )}

        <form onSubmit={handleVerify} className="space-y-6">
          {/* Code Input */}
          <div className="flex justify-center gap-2">
            {code.map((digit, index) => (
              <input
                key={index}
                ref={(el) => (inputRefs.current[index] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onPaste={handlePaste}
                className="w-12 h-14 text-center text-xl font-semibold border-2 border-gray-300 rounded-xl focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-all"
                autoFocus={index === 0}
              />
            ))}
          </div>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            type="submit"
            disabled={loading || code.join('').length !== 6}
            className={`w-full py-3 rounded-full font-medium transition-colors shadow-sm ${
              loading || code.join('').length !== 6
                ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                : 'bg-blue-500 hover:bg-blue-600 text-white'
            }`}
          >
            {loading ? 'Verifying...' : 'Verify Email'}
          </motion.button>
        </form>

        {/* Resend Code */}
        <div className="mt-6 text-center">
          <p className="text-sm text-gray-500">
            Didn't receive the code?{' '}
            {countdown > 0 ? (
              <span className="text-gray-400">Resend in {countdown}s</span>
            ) : (
              <button
                onClick={handleResendCode}
                disabled={resending}
                className="text-blue-500 hover:text-blue-600 font-medium"
              >
                {resending ? 'Sending...' : 'Resend Code'}
              </button>
            )}
          </p>
        </div>

        {/* Back to Login */}
        <div className="mt-4 text-center">
          <button
            onClick={() => navigate('/login')}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            ← Back to Login
          </button>
        </div>
      </motion.div>
    </div>
  )
}

export default VerifyEmail
