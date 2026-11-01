import { apiRequest } from '@/shared/api'

export interface SessionUser {
  id: string
  email: string
  is_active: boolean
  first_name?: string
  last_name?: string
}

export interface Tokens {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface Credentials {
  email: string
  password: string
}

export const sessionApi = {
  register: (credentials: Credentials) =>
    apiRequest<SessionUser>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),
  login: (credentials: Credentials) =>
    apiRequest<Tokens>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    }),
  refresh: (refreshToken: string) =>
    apiRequest<Tokens>('/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),
  logout: (refreshToken: string) =>
    apiRequest<void>('/auth/logout', {
      method: 'POST',
      body: JSON.stringify({ refresh_token: refreshToken }),
    }),
}
