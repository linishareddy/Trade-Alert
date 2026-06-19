import request from '@/lib/api/client'
import type { LoginRequest, TokenResponse, User } from '@/types'

export function login(credentials: LoginRequest) {
  return request<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(credentials),
  })
}

export function me() {
  return request<User>('/auth/me')
}
