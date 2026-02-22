import { useAuth } from '../../app/providers/AuthProvider'
import { useEffect, useState } from 'react'
import { usePreferences, useProfile, useUpdatePreferences } from '../../features/settings/useSettings'
import type { UserPreferences } from '../../api/contracts'

const defaultForm: UserPreferences = {
  default_environment: 'dev',
  timezone: 'UTC',
  locale: 'en-US',
  notifications_enabled: true,
}

export function SettingsPage() {
  const { role, isAdmin } = useAuth()
  const profile = useProfile()
  const preferences = usePreferences()
  const updatePreferences = useUpdatePreferences()
  const [form, setForm] = useState<UserPreferences>(defaultForm)

  useEffect(() => {
    if (preferences.data) {
      setForm(preferences.data)
    }
  }, [preferences.data])

  if (profile.isLoading || preferences.isLoading) {
    return <p>Loading settings...</p>
  }

  if (profile.isError || preferences.isError) {
    return <p>Unable to load settings.</p>
  }

  const handleSubmit = () => {
    updatePreferences.mutate(form)
  }

  return (
    <section>
      <h1>Settings</h1>
      <article className="product-card section-gap">
        <h2>Profile</h2>
        <p>Subject: {profile.data?.subject ?? '-'}</p>
        <p>Role: {profile.data?.role ?? '-'}</p>
      </article>

      <article className="product-card section-gap form-stack">
        <h2>Preferences</h2>

        <label>
          Default environment
          <select
            value={form.default_environment}
            onChange={(event) =>
              setForm((previous) => ({
                ...previous,
                default_environment: event.target.value as UserPreferences['default_environment'],
              }))
            }
          >
            <option value="dev">dev</option>
            <option value="staging">staging</option>
            <option value="prod">prod</option>
          </select>
        </label>

        <label>
          Timezone
          <input
            value={form.timezone}
            onChange={(event) =>
              setForm((previous) => ({
                ...previous,
                timezone: event.target.value,
              }))
            }
          />
        </label>

        <label>
          Locale
          <input
            value={form.locale}
            onChange={(event) =>
              setForm((previous) => ({
                ...previous,
                locale: event.target.value,
              }))
            }
          />
        </label>

        <label className="checkbox-row">
          <input
            type="checkbox"
            checked={form.notifications_enabled}
            onChange={(event) =>
              setForm((previous) => ({
                ...previous,
                notifications_enabled: event.target.checked,
              }))
            }
          />
          Notifications enabled
        </label>

        <div className="actions-row">
          <button type="button" onClick={handleSubmit} disabled={!isAdmin || updatePreferences.isPending}>
            {updatePreferences.isPending ? 'Saving...' : 'Save preferences'}
          </button>
        </div>

        {updatePreferences.isSuccess ? <p>Preferences updated.</p> : null}
        {updatePreferences.isError ? <p>Unable to update preferences.</p> : null}
      </article>

      <p>Current role: {role ?? 'anonymous'}</p>
      {!isAdmin ? <p>Preferences update is restricted to admin role.</p> : null}
    </section>
  )
}
