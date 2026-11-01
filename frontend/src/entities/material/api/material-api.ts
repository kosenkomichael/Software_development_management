import type {
  Material,
  MaterialList,
  Note,
  NoteStatus,
  Quiz,
  QuizResult,
  QuizStatus,
  SubmittedAnswer,
} from '../model/types'
import type { ApiRequestOptions } from '@/shared/api'

export type AuthorizedRequest = <T>(path: string, options?: ApiRequestOptions) => Promise<T>
export function createMaterialApi(request: AuthorizedRequest) {
  const path = (id: string) => `/materials/${encodeURIComponent(id)}`
  return {
    list: (page = 1) => request<MaterialList>(`/materials/?page=${page}&page_size=100`),
    get: (id: string, signal?: AbortSignal) => request<Material>(path(id), { signal }),
    upload: (file: File, signal?: AbortSignal) => {
      const body = new FormData()
      body.append('file', file)
      return request<Material>('/materials/upload', { method: 'POST', body, signal })
    },
    notes: (id: string, signal?: AbortSignal) => request<Note>(`${path(id)}/notes`, { signal }),
    notesStatus: (id: string, signal?: AbortSignal) =>
      request<NoteStatus>(`${path(id)}/notes/status`, { signal }),
    image: (id: string, order: number, signal?: AbortSignal) =>
      request<Blob>(`${path(id)}/images/${order}`, { signal, responseType: 'blob' }),
    regenerate: (id: string) => request(`${path(id)}/notes/regenerate`, { method: 'POST' }),
    quizStatus: (id: string, signal?: AbortSignal) =>
      request<QuizStatus>(`${path(id)}/quiz/status`, { signal }),
    quiz: (id: string, signal?: AbortSignal) => request<Quiz>(`${path(id)}/quiz`, { signal }),
    generateQuiz: (id: string, signal?: AbortSignal) =>
      request<QuizStatus>(`${path(id)}/quiz/generate`, { method: 'POST', signal }),
    submit: (id: string, answers: SubmittedAnswer[]) =>
      request<QuizResult>(`${path(id)}/quiz/submit`, {
        method: 'POST',
        body: JSON.stringify({ answers }),
      }),
  }
}
