export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(/\/$/, '')
export interface ApiRequestOptions extends RequestInit {
  responseType?: 'json' | 'blob'
}

export async function apiRequest<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const { responseType, ...requestOptions } = options
  const headers = new Headers(options.headers)
  if (typeof options.body === 'string' && !headers.has('Content-Type'))
    headers.set('Content-Type', 'application/json')
  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, {
      ...requestOptions,
      headers,
      signal: options.signal ?? AbortSignal.timeout(15000),
    })
  } catch {
    if (options.signal?.aborted) throw new DOMException('Запрос отменён', 'AbortError')
    throw new ApiError(
      0,
      'Не удалось связаться с сервером. Проверьте соединение и попробуйте ещё раз.'
    )
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const messages: Record<string, string> = {
      'Invalid credentials': 'Неверный email или пароль.',
      'Email already registered': 'Этот email уже зарегистрирован.',
      'Account is disabled': 'Аккаунт отключён.',
      'Material not found': 'Материал не найден или недоступен.',
      'Notes not ready yet': 'Конспект ещё не готов. Обновите статус немного позже.',
      'Quiz not found': 'Тест ещё не создан.',
      'Quiz is not ready yet': 'Тест ещё обрабатывается.',
      'Generate notes first': 'Сначала дождитесь готовности конспекта.',
      'Generation already in progress': 'Обработка уже запущена.',
      'Unsupported file type. Allowed: PDF, DOCX, PPTX': 'Поддерживаются файлы PDF, DOCX и PPTX.',
      'File exceeds maximum allowed size of 50 MB': 'Максимальный размер файла — 50 МБ.',
    }
    const message = typeof body?.detail === 'string' ? messages[body.detail] : undefined
    throw new ApiError(
      response.status,
      message ??
        (response.status === 422
          ? path.startsWith('/auth/')
            ? 'Проверьте email и пароль. Пароль должен содержать от 8 до 128 символов.'
            : 'Проверьте введённые данные.'
          : response.status === 429
            ? 'Слишком много попыток. Повторите позже.'
            : response.status === 401
              ? 'Сессия истекла. Войдите снова.'
              : 'Не удалось выполнить запрос. Попробуйте ещё раз.')
    )
  }
  if (responseType === 'blob') return (await response.blob()) as T
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
}
