import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import { ChatProvider } from './contexts/ChatContext'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Chat from './pages/Chat'
import Documents from './pages/Documents'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <AuthProvider>
      <ChatProvider>
        <Router>
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Protected routes */}
            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route path="/" element={<Navigate to="/chat" replace />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/documents" element={<Documents />} />
              </Route>
            </Route>
          </Routes>
        </Router>
      </ChatProvider>
    </AuthProvider>
  )
}

export default App
