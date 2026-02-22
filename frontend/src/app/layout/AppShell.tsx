import { useState } from 'react'
import type { FormEvent } from 'react'
import { NavLink } from 'react-router-dom'
import type { ReactNode } from 'react'
import { useAuth } from '../providers/AuthProvider'

type AppShellProps = {
  children: ReactNode
}

type NavItem = {
  to: string
  label: string
}

const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard' },
  { to: '/products', label: 'Products' },
  { to: '/datalake', label: 'Data Lake' },
  { to: '/governance', label: 'Governance' },
  { to: '/platform-ops', label: 'Platform Ops' },
  { to: '/settings', label: 'Settings' },
]

export function AppShell({ children }: AppShellProps) {
  const { role, status, error, loginWithToken, logout } = useAuth()
  const [tokenInput, setTokenInput] = useState('')

  const handleLogin = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const ok = await loginWithToken(tokenInput)
    if (ok) {
      setTokenInput('')
    }
  }

  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <h2>Data Platform</h2>
        <div className="login-panel">
          <p className="login-title">Authentication</p>
          {status === 'authenticated' && role ? (
            <>
              <p className="login-status">Role: {role}</p>
              <button type="button" onClick={logout}>
                Sign out
              </button>
            </>
          ) : (
            <form onSubmit={handleLogin}>
              <input
                type="password"
                value={tokenInput}
                onChange={(event) => setTokenInput(event.target.value)}
                placeholder="Enter bearer token"
              />
              <button type="submit" disabled={status === 'authenticating'}>
                {status === 'authenticating' ? 'Signing in...' : 'Sign in'}
              </button>
            </form>
          )}
          <p className="token-hint">Use: viewer-token / operator-token / admin-token</p>
          {error ? <p className="login-error">{error}</p> : null}
        </div>
        <nav>
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `app-nav-link${isActive ? ' app-nav-link-active' : ''}`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="app-main">{children}</main>
    </div>
  )
}
