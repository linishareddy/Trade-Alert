const BASE = '/api/v1'

import { getToken, clearToken } from '@/lib/auth/storage'

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init?.headers as Record<string, string> | undefined),
  }
  if (token) {
    headers.Authorization = `Bearer ${token}`
  }

  const res = await fetch(`${BASE}${path}`, { ...init, headers })

  if (res.status === 401 && typeof window !== 'undefined') {
    const onLoginPage = window.location.pathname === '/login'
    if (!onLoginPage) {
      clearToken()
      window.location.href = '/login'
    }
  }

  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText)
    throw new ApiError(res.status, `API ${res.status}: ${text}`)
  }
  return res.json() as Promise<T>
}

export default request
