import { createContext, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { endpoints } from '../../api/endpoints'

export type AppRole = 'viewer' | 'operator' | 'admin'
type AuthStatus = 'anonymous' | 'authenticating' | 'authenticated'

type AuthContextValue = {
  role: AppRole | null
  token: string
  status: AuthStatus
  error: string | null
  loginWithToken: (token: string) => Promise<boolean>
  logout: () => void
  canOperate: boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState(() => window.localStorage.getItem('platform_token') ?? '')
  const [role, setRole] = useState<AppRole | null>(null)
  const [status, setStatus] = useState<AuthStatus>(() => (token ? 'authenticating' : 'anonymous'))
  const [error, setError] = useState<string | null>(null)

  const resolveRoleByToken = async (accessToken: string): Promise<AppRole> => {
    const response = await fetch(endpoints.authLogin, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ token: accessToken }),
    })
    const payload = (await response.json()) as {
      data?: { role?: string }
      error?: { message?: string; detail?: string }
      detail?: string
    }

    if (!response.ok) {
      const message = payload.error?.message ?? payload.detail ?? 'Invalid token'
      throw new Error(message)
    }

    const resolvedRole = payload.data?.role
    if (resolvedRole !== 'viewer' && resolvedRole !== 'operator' && resolvedRole !== 'admin') {
      throw new Error('Unsupported role from login endpoint')
    }
    return resolvedRole
  }

  const resolveRoleBySession = async (accessToken: string): Promise<AppRole> => {
    const response = await fetch(endpoints.authSession, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    })
    const payload = (await response.json()) as {
      data?: { role?: string }
      error?: { message?: string; detail?: string }
      detail?: string
    }

    if (!response.ok) {
      const message = payload.error?.message ?? payload.detail ?? 'Session is invalid'
      throw new Error(message)
    }

    const resolvedRole = payload.data?.role
    if (resolvedRole !== 'viewer' && resolvedRole !== 'operator' && resolvedRole !== 'admin') {
      throw new Error('Unsupported role from session endpoint')
    }
    return resolvedRole
  }

  const loginWithToken = async (nextToken: string): Promise<boolean> => {
    const trimmedToken = nextToken.trim()
    if (!trimmedToken) {
      setError('Token is required')
      return false
    }

    setStatus('authenticating')
    setError(null)
    try {
      const nextRole = await resolveRoleByToken(trimmedToken)
      setToken(trimmedToken)
      setRole(nextRole)
      setStatus('authenticated')
      window.localStorage.setItem('platform_token', trimmedToken)
      window.localStorage.setItem('platform_role', nextRole)
      return true
    } catch (authError) {
      setToken('')
      setRole(null)
      setStatus('anonymous')
      setError(authError instanceof Error ? authError.message : 'Authentication failed')
      window.localStorage.removeItem('platform_token')
      window.localStorage.removeItem('platform_role')
      return false
    }
  }

  const logout = () => {
    if (token) {
      void fetch(endpoints.authLogout, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
    }

    setToken('')
    setRole(null)
    setStatus('anonymous')
    setError(null)
    window.localStorage.removeItem('platform_token')
    window.localStorage.removeItem('platform_role')
  }

  useEffect(() => {
    if (status === 'authenticating' && token && role === null) {
      void (async () => {
        try {
          const restoredRole = await resolveRoleBySession(token)
          setRole(restoredRole)
          setStatus('authenticated')
          setError(null)
          window.localStorage.setItem('platform_role', restoredRole)
        } catch {
          const ok = await loginWithToken(token)
          if (!ok) {
            setStatus('anonymous')
          }
        }
      })()
    }
  }, [status, token, role])

  const value = useMemo<AuthContextValue>(
    () => ({
      role,
      token,
      status,
      error,
      loginWithToken,
      logout,
      canOperate: role === 'operator' || role === 'admin',
      isAdmin: role === 'admin',
    }),
    [role, token, status, error],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
