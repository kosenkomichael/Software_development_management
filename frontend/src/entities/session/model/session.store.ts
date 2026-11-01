import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { apiRequest, ApiError, type ApiRequestOptions } from '@/shared/api'
import { sessionApi, type Credentials, type SessionUser, type Tokens } from '../api/session-api'

const storageKey = 'studyai.session'

export const useSessionStore = defineStore('session', () => {
  const user = ref<SessionUser | null>(null)
  const isPending = ref(false)
  const isInitializing = ref(true)
  const sessionError = ref('')
  const isAuthenticated = computed(() => user.value !== null)
  let tokens: Tokens | null = null
  let rememberSession = false
  let refreshPromise: Promise<void> | null = null
  let initializePromise: Promise<void> | null = null
  let revision = 0

  function persist() {
    try {
      localStorage.removeItem(storageKey)
      sessionStorage.removeItem(storageKey)
      if (tokens) {
        const storage = rememberSession ? localStorage : sessionStorage
        storage.setItem(storageKey, JSON.stringify(tokens))
      }
    } catch {
      /* The current session still works when browser storage is unavailable. */
    }
  }

  function clear() {
    revision++
    tokens = null
    user.value = null
    persist()
  }

  function refresh() {
    if (refreshPromise) return refreshPromise
    const refreshToken = tokens?.refresh_token
    if (!refreshToken) return Promise.reject(new ApiError(401, 'Войдите в аккаунт.'))
    const currentRevision = revision
    refreshPromise = sessionApi
      .refresh(refreshToken)
      .then((result) => {
        if (currentRevision !== revision) throw new ApiError(401, 'Сессия завершена.')
        tokens = result
        persist()
      })
      .catch((error: unknown) => {
        if (
          currentRevision === revision &&
          error instanceof ApiError &&
          [401, 403].includes(error.status)
        )
          clear()
        throw error
      })
      .finally(() => {
        refreshPromise = null
      })
    return refreshPromise
  }

  async function request<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
    const currentRevision = revision
    const accessToken = tokens?.access_token
    if (!accessToken) throw new ApiError(401, 'Войдите в аккаунт.')
    const send = (token: string) => {
      const headers = new Headers(options.headers)
      headers.set('Authorization', `Bearer ${token}`)
      return apiRequest<T>(path, { ...options, headers })
    }
    try {
      return await send(accessToken)
    } catch (error) {
      if (!(error instanceof ApiError) || error.status !== 401) throw error
      if (currentRevision !== revision) throw error
      if (tokens?.access_token === accessToken) await refresh()
      if (!tokens || currentRevision !== revision) throw error
      try {
        return await send(tokens.access_token)
      } catch (retryError) {
        if (
          currentRevision === revision &&
          retryError instanceof ApiError &&
          retryError.status === 401
        )
          clear()
        throw retryError
      }
    }
  }

  async function login(credentials: Credentials, remember: boolean) {
    if (isPending.value || isInitializing.value)
      throw new Error('Дождитесь завершения текущего запроса.')
    isPending.value = true
    sessionError.value = ''
    try {
      const result = await sessionApi.login(credentials)
      revision++
      tokens = result
      rememberSession = remember
      persist()
      user.value = await request<SessionUser>('/auth/me')
    } finally {
      isPending.value = false
    }
  }

  async function register(credentials: Credentials) {
    if (isPending.value || isInitializing.value)
      throw new Error('Дождитесь завершения текущего запроса.')
    isPending.value = true
    try {
      await sessionApi.register(credentials)
    } finally {
      isPending.value = false
    }
  }

  async function logout() {
    if (isPending.value) return
    isPending.value = true
    sessionError.value = ''
    try {
      // Wait for a running rotation so the newly issued refresh token is revoked too.
      await refreshPromise?.catch(() => undefined)
      if (tokens) await sessionApi.logout(tokens.refresh_token)
    } catch {
      sessionError.value =
        'Вы вышли на этом устройстве. Завершение сессии на сервере не подтверждено: сервер недоступен.'
    } finally {
      clear()
      isPending.value = false
    }
  }

  function initialize() {
    if (initializePromise) return initializePromise
    isInitializing.value = true
    sessionError.value = ''
    initializePromise = (async () => {
      try {
        if (!tokens) {
          const persistent = localStorage.getItem(storageKey)
          const stored = persistent ?? sessionStorage.getItem(storageKey)
          if (!stored) return
          const parsed = JSON.parse(stored) as Partial<Tokens> | null
          if (
            !parsed ||
            typeof parsed.access_token !== 'string' ||
            !parsed.access_token ||
            typeof parsed.refresh_token !== 'string' ||
            !parsed.refresh_token
          ) {
            clear()
            return
          }
          tokens = {
            access_token: parsed.access_token,
            refresh_token: parsed.refresh_token,
            token_type: 'bearer',
          }
          rememberSession = persistent !== null
        }
        user.value = await request<SessionUser>('/auth/me')
      } catch (error) {
        if (error instanceof SyntaxError) clear()
        else if (error instanceof ApiError && [401, 403].includes(error.status)) clear()
        else sessionError.value = 'Не удалось восстановить сессию. Попробуйте ещё раз.'
      } finally {
        isInitializing.value = false
      }
    })().finally(() => {
      initializePromise = null
    })
    return initializePromise
  }

  return {
    user,
    isPending,
    isInitializing,
    sessionError,
    isAuthenticated,
    login,
    register,
    logout,
    initialize,
    request,
  }
})
