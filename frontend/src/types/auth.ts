export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
  full_name: string
  role: 'teacher' | 'school_admin'
  is_active: boolean
  is_verified: boolean
  subscription_plan: 'free' | 'premium' | 'school'
  subscription_status: string
  school_name?: string
  subject_areas?: string
  bio?: string
  created_at: string
  last_login?: string
  quiz_count_current_month: number
  can_create_quiz: boolean
  subscription_active: boolean
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  password: string
  first_name: string
  last_name: string
  role?: 'teacher' | 'school_admin'
  school_name?: string
  subject_areas?: string
}

export interface LoginResponse {
  message: string
  user: User
  access_token: string
  refresh_token: string
}

export interface RegisterResponse {
  message: string
  user: User
  access_token: string
  refresh_token: string
}

export interface RefreshTokenResponse {
  access_token: string
}
