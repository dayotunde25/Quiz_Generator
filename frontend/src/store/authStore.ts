import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { authApi } from '../services/api/authApi'
import type { User, LoginCredentials, RegisterData } from '../types/auth'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

interface AuthActions {
  login: (credentials: LoginCredentials) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  refreshAccessToken: () => Promise<void>
  clearError: () => void
  setUser: (user: User) => void
  initializeAuth: () => void
}

type AuthStore = AuthState & AuthActions

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Actions
      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await authApi.login(credentials)
          
          set({
            user: response.user,
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.response?.data?.message || 'Login failed',
          })
          throw error
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true, error: null })
        
        try {
          const response = await authApi.register(data)
          
          set({
            user: response.user,
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.response?.data?.message || 'Registration failed',
          })
          throw error
        }
      },

      logout: () => {
        const { accessToken } = get()
        
        // Call logout API if we have a token
        if (accessToken) {
          authApi.logout().catch(console.error)
        }
        
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        })
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get()
        
        if (!refreshToken) {
          throw new Error('No refresh token available')
        }
        
        try {
          const response = await authApi.refreshToken(refreshToken)
          
          set({
            accessToken: response.access_token,
          })
        } catch (error) {
          // If refresh fails, logout the user
          get().logout()
          throw error
        }
      },

      clearError: () => {
        set({ error: null })
      },

      setUser: (user: User) => {
        set({ user })
      },

      initializeAuth: () => {
        const { accessToken, refreshToken } = get()
        
        if (accessToken && refreshToken) {
          set({ isAuthenticated: true })
          
          // Fetch current user data
          authApi.getCurrentUser()
            .then((user) => {
              set({ user })
            })
            .catch(() => {
              // If fetching user fails, logout
              get().logout()
            })
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        user: state.user,
      }),
    }
  )
)
