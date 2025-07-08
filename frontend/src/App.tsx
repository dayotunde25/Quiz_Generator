import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import { LoadingSpinner } from './components/ui/LoadingSpinner'

// Layout components
import { AuthLayout } from './components/layout/AuthLayout'
import { DashboardLayout } from './components/layout/DashboardLayout'
import { PublicLayout } from './components/layout/PublicLayout'

// Auth pages
import { LoginPage } from './pages/auth/LoginPage'
import { RegisterPage } from './pages/auth/RegisterPage'
import { ForgotPasswordPage } from './pages/auth/ForgotPasswordPage'
import { ResetPasswordPage } from './pages/auth/ResetPasswordPage'

// Dashboard pages
import { DashboardPage } from './pages/dashboard/DashboardPage'
import { QuizzesPage } from './pages/dashboard/QuizzesPage'
import { CreateQuizPage } from './pages/dashboard/CreateQuizPage'
import { EditQuizPage } from './pages/dashboard/EditQuizPage'
import { QuizDetailPage } from './pages/dashboard/QuizDetailPage'
import { FilesPage } from './pages/dashboard/FilesPage'
import { ProfilePage } from './pages/dashboard/ProfilePage'
import { SubscriptionPage } from './pages/dashboard/SubscriptionPage'
import { AnalyticsPage } from './pages/dashboard/AnalyticsPage'

// Public pages
import { LandingPage } from './pages/public/LandingPage'
import { PricingPage } from './pages/public/PricingPage'
import { AboutPage } from './pages/public/AboutPage'
import { ContactPage } from './pages/public/ContactPage'
import { SharedQuizPage } from './pages/public/SharedQuizPage'

// Error pages
import { NotFoundPage } from './pages/error/NotFoundPage'
import { ErrorBoundary } from './components/error/ErrorBoundary'

// Protected route component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth/login" replace />
  }

  return <>{children}</>
}

// Public route component (redirect if authenticated)
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuthStore()

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
}

function App() {
  const { initializeAuth } = useAuthStore()

  React.useEffect(() => {
    initializeAuth()
  }, [initializeAuth])

  return (
    <ErrorBoundary>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<PublicLayout />}>
            <Route index element={<LandingPage />} />
            <Route path="pricing" element={<PricingPage />} />
            <Route path="about" element={<AboutPage />} />
            <Route path="contact" element={<ContactPage />} />
            <Route path="quiz/:shareToken" element={<SharedQuizPage />} />
          </Route>

          {/* Auth routes */}
          <Route path="/auth" element={<AuthLayout />}>
            <Route
              path="login"
              element={
                <PublicRoute>
                  <LoginPage />
                </PublicRoute>
              }
            />
            <Route
              path="register"
              element={
                <PublicRoute>
                  <RegisterPage />
                </PublicRoute>
              }
            />
            <Route
              path="forgot-password"
              element={
                <PublicRoute>
                  <ForgotPasswordPage />
                </PublicRoute>
              }
            />
            <Route
              path="reset-password"
              element={
                <PublicRoute>
                  <ResetPasswordPage />
                </PublicRoute>
              }
            />
          </Route>

          {/* Dashboard routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="quizzes" element={<QuizzesPage />} />
            <Route path="quizzes/create" element={<CreateQuizPage />} />
            <Route path="quizzes/:id" element={<QuizDetailPage />} />
            <Route path="quizzes/:id/edit" element={<EditQuizPage />} />
            <Route path="files" element={<FilesPage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="subscription" element={<SubscriptionPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
          </Route>

          {/* 404 page */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
    </ErrorBoundary>
  )
}

export default App
