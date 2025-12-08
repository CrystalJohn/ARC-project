import { Amplify } from 'aws-amplify'
import { signIn, signOut, getCurrentUser, fetchAuthSession } from 'aws-amplify/auth'

// Configure Amplify with Cognito settings
const configureAmplify = () => {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: import.meta.env.VITE_COGNITO_POOL_ID || 'ap-southeast-1_8KB4JYvsX',
        userPoolClientId: import.meta.env.VITE_COGNITO_CLIENT_ID || '457qqut8jm0b6a46dttdrn6rs4',
        region: import.meta.env.VITE_AWS_REGION || 'ap-southeast-1',
      }
    }
  })
}

// Initialize Amplify
configureAmplify()

/**
 * AuthService - Handles Cognito authentication
 */
class AuthService {
  /**
   * Login with email and password
   * @param {string} email 
   * @param {string} password 
   * @returns {Promise<{user, token, groups}>}
   */
  async login(email, password) {
    try {
      const { isSignedIn, nextStep } = await signIn({
        username: email,
        password: password,
      })

      if (!isSignedIn) {
        throw new Error('Sign in incomplete. Next step: ' + nextStep.signInStep)
      }

      // Get user info and token
      const user = await getCurrentUser()
      const session = await fetchAuthSession()
      const token = session.tokens?.idToken?.toString()

      // Extract groups and display name from token payload
      const payload = session.tokens?.idToken?.payload || {}
      const groups = payload['cognito:groups'] || []
      const displayName =
        payload['preferred_username'] || payload['name'] || payload['email'] || email

      // Store token and user info in localStorage
      localStorage.setItem('auth_token', token)
      localStorage.setItem('user_email', email)
      localStorage.setItem('user_groups', JSON.stringify(groups))
      localStorage.setItem('user_display_name', displayName)

      return {
        user: {
          email: email,
          userId: user.userId,
          username: user.username,
          displayName: displayName,
        },
        token,
        groups,
      }
    } catch (error) {
      console.error('Login error:', error)
      throw new Error(this._getErrorMessage(error))
    }
  }

  /**
   * Logout current user
   */
  async logout() {
    try {
      await signOut()
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_email')
      localStorage.removeItem('user_groups')
      localStorage.removeItem('user_display_name')
    } catch (error) {
      console.error('Logout error:', error)
      // Clear local storage even if signOut fails
      localStorage.removeItem('auth_token')
      localStorage.removeItem('user_email')
      localStorage.removeItem('user_groups')
      localStorage.removeItem('user_display_name')
    }
  }

  /**
   * Get current authenticated user
   * @returns {Promise<{email, userId, username, displayName, groups}>}
   */
  async getCurrentUser() {
    try {
      const user = await getCurrentUser()
      const session = await fetchAuthSession()
      const payload = session.tokens?.idToken?.payload || {}
      const groups = payload['cognito:groups'] || []
      const email = localStorage.getItem('user_email')

      // Get display name from token or localStorage
      const displayName =
        payload['preferred_username'] ||
        payload['name'] ||
        localStorage.getItem('user_display_name') ||
        email

      return {
        email,
        userId: user.userId,
        username: displayName, // Use displayName as username for UI
        displayName: displayName,
        groups,
      }
    } catch (error) {
      return null
    }
  }

  /**
   * Get access token
   * @returns {string|null}
   */
  getAccessToken() {
    return localStorage.getItem('auth_token')
  }

  /**
   * Check if user is authenticated
   * @returns {boolean}
   */
  isAuthenticated() {
    const token = this.getAccessToken()
    if (!token) return false

    try {
      // Check if token is expired
      const payload = JSON.parse(atob(token.split('.')[1]))
      const exp = payload.exp * 1000 // Convert to milliseconds
      return Date.now() < exp
    } catch (error) {
      return false
    }
  }

  /**
   * Check if user has admin role
   * @returns {boolean}
   */
  isAdmin() {
    try {
      const groups = JSON.parse(localStorage.getItem('user_groups') || '[]')
      return groups.includes('admin')
    } catch (error) {
      return false
    }
  }

  /**
   * Register new user (Cognito sign up)
   * @param {string} email 
   * @param {string} username 
   * @param {string} password 
   * @returns {Promise<{success: boolean, message: string}>}
   */
  async register(email, username, password) {
    try {
      // Import signUp dynamically to avoid circular dependency
      const { signUp } = await import('aws-amplify/auth')
      
      const { isSignUpComplete, userId, nextStep } = await signUp({
        username: email,
        password: password,
        options: {
          userAttributes: {
            email: email,
            preferred_username: username,
          },
          autoSignIn: false, // Don't auto sign in after registration
        }
      })

      if (isSignUpComplete) {
        return {
          success: true,
          message: 'Registration successful! Please check your email to verify your account.',
          requiresVerification: false,
        }
      } else if (nextStep.signUpStep === 'CONFIRM_SIGN_UP') {
        return {
          success: true,
          message: 'Registration successful! Please check your email for verification code.',
          requiresVerification: true,
        }
      } else {
        return {
          success: false,
          message: 'Registration incomplete. Next step: ' + nextStep.signUpStep,
        }
      }
    } catch (error) {
      console.error('Registration error:', error)
      throw new Error(this._getRegistrationErrorMessage(error))
    }
  }

  /**
   * Get user-friendly registration error message
   * @private
   */
  _getRegistrationErrorMessage(error) {
    const errorCode = error.name || error.code

    switch (errorCode) {
      case 'UsernameExistsException':
        return 'This email is already registered. Please login instead.'
      case 'InvalidPasswordException':
        return 'Password must be at least 8 characters with uppercase, lowercase, number and special character.'
      case 'InvalidParameterException':
        return 'Invalid email or password format.'
      case 'TooManyRequestsException':
        return 'Too many registration attempts. Please try again later.'
      case 'NetworkError':
        return 'Network error. Please check your connection.'
      default:
        return error.message || 'Registration failed. Please try again.'
    }
  }

  /**
   * Get user-friendly error message
   * @private
   */
  _getErrorMessage(error) {
    const errorCode = error.name || error.code

    switch (errorCode) {
      case 'UserNotFoundException':
      case 'NotAuthorizedException':
        return 'Invalid email or password'
      case 'UserNotConfirmedException':
        return 'Please verify your email before logging in'
      case 'PasswordResetRequiredException':
        return 'Password reset required. Please contact admin'
      case 'TooManyRequestsException':
        return 'Too many login attempts. Please try again later'
      case 'NetworkError':
        return 'Network error. Please check your connection'
      default:
        return error.message || 'Login failed. Please try again'
    }
  }
}

// Export as named export for consistency
export const authService = new AuthService()

// Also export as default for backward compatibility
export default authService
