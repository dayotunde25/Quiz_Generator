import { api } from './client'
import type { 
  User, 
  LoginCredentials, 
  RegisterData, 
  LoginResponse, 
  RegisterResponse,
  RefreshTokenResponse 
} from '../../types/auth'

export const authApi = {
  // Login user
  login: (credentials: LoginCredentials): Promise<LoginResponse> =>
    api.post('/auth/login', credentials),

  // Register new user
  register: (data: RegisterData): Promise<RegisterResponse> =>
    api.post('/auth/register', data),

  // Logout user
  logout: (): Promise<void> =>
    api.post('/auth/logout'),

  // Refresh access token
  refreshToken: (refreshToken: string): Promise<RefreshTokenResponse> =>
    api.post('/auth/refresh', {}, {
      headers: {
        Authorization: `Bearer ${refreshToken}`,
      },
    }),

  // Get current user
  getCurrentUser: (): Promise<User> =>
    api.get('/auth/me').then(response => response.user),

  // Forgot password
  forgotPassword: (email: string): Promise<{ message: string }> =>
    api.post('/auth/forgot-password', { email }),

  // Reset password
  resetPassword: (token: string, password: string): Promise<{ message: string }> =>
    api.post('/auth/reset-password', { token, password }),

  // Verify email
  verifyEmail: (token: string): Promise<{ message: string }> =>
    api.post('/auth/verify-email', { token }),

  // Resend verification email
  resendVerification: (email: string): Promise<{ message: string }> =>
    api.post('/auth/resend-verification', { email }),
}
