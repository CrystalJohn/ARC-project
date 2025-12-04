import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useState, useEffect } from 'react'
import authService from '../services/authService'

function Navbar() {
  const location = useLocation()
  const navigate = useNavigate()
  const [user, setUser] = useState(null)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  
  useEffect(() => {
    checkAuth()
  }, [location])

  const checkAuth = async () => {
    const authenticated = authService.isAuthenticated()
    setIsAuthenticated(authenticated)
    
    if (authenticated) {
      const currentUser = await authService.getCurrentUser()
      setUser(currentUser)
    } else {
      setUser(null)
    }
  }

  const handleLogout = async () => {
    await authService.logout()
    setUser(null)
    setIsAuthenticated(false)
    navigate('/login')
  }
  
  const isActive = (path) => {
    return location.pathname === path ? 'bg-blue-700' : ''
  }

  return (
    <nav className="bg-blue-600 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-8">
            <Link to="/" className="text-xl font-bold">
              ARC Chatbot
            </Link>
            
            <div className="flex space-x-2">
              <Link
                to="/"
                className={`px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors ${isActive('/')}`}
              >
                Home
              </Link>
              <Link
                to="/login"
                className={`px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors ${isActive('/login')}`}
              >
                Login
              </Link>
              <Link
                to="/chat"
                className={`px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors ${isActive('/chat')}`}
              >
                Chat
              </Link>
              <Link
                to="/admin"
                className={`px-3 py-2 rounded-md text-sm font-medium hover:bg-blue-700 transition-colors ${isActive('/admin')}`}
              >
                Admin
              </Link>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            {isAuthenticated && user ? (
              <>
                <span className="text-sm text-blue-100">
                  {user.email}
                  {user.groups?.includes('admin') && (
                    <span className="ml-2 px-2 py-0.5 bg-blue-800 rounded text-xs">Admin</span>
                  )}
                </span>
                <button
                  onClick={handleLogout}
                  className="px-3 py-1 bg-blue-800 hover:bg-blue-900 rounded text-sm transition-colors"
                >
                  Logout
                </button>
              </>
            ) : (
              <span className="text-sm text-blue-100">
                M3 Task #35 - Cognito Auth
              </span>
            )}
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
