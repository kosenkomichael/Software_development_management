import type { AuthorizedRequest } from './material-api'
import type { Quiz, QuizResult, SubmittedAnswer, QuizAttemptDetail, QuizAttemptList } from '../model/types'
export interface LeaderboardEntry { rank: number; name: string; score: number; correct: number; total: number; duration_ms: number; is_you: boolean }
export interface PublicQuizItem { id: string; title: string; author: string; published_at: string; question_count: number }
export interface PublicAttemptItem { duration_ms?: number | null; id: string; quiz_id: string | null; title: string; created_at: string; score: number; correct: number; total: number }
export function createPublicQuizApi(request: AuthorizedRequest) {
  return {
    list: (page = 1, signal?: AbortSignal) => request<{ items: PublicQuizItem[]; total: number }>(`/public-quizzes?page=${page}`, { signal }),
    quiz: (id: string, signal?: AbortSignal) => request<Quiz>(`/public-quizzes/${encodeURIComponent(id)}`, { signal }),
    cancel: (id: string, runId: string) => request<void>(`/public-quizzes/${encodeURIComponent(id)}/cancel`, { method: 'POST', body: JSON.stringify({ run_id: runId }), keepalive: true }),
    heartbeat: (id: string, runId: string) => request<void>(`/public-quizzes/${encodeURIComponent(id)}/heartbeat`, { method: 'POST', body: JSON.stringify({ run_id: runId }) }),
    start: (id: string, signal?: AbortSignal) => request<{ run_id: string; started_at: string; server_time: string }>(`/public-quizzes/${encodeURIComponent(id)}/start`, { method: 'POST', signal }),
    leaderboard: (id: string, signal?: AbortSignal) => request<{ items: LeaderboardEntry[]; participants: number; my_entry: LeaderboardEntry | null }>(`/public-quizzes/${encodeURIComponent(id)}/leaderboard`, { signal }),
    submit: (id: string, answers: SubmittedAnswer[], runId?: string) => request<QuizResult>(`/public-quizzes/${encodeURIComponent(id)}/submit`, { method: 'POST', body: JSON.stringify({ quiz_id: id, answers, run_id: runId }) }),
    attempts: (quizId?: string, page = 1, signal?: AbortSignal) => request<QuizAttemptList & { items: PublicAttemptItem[] }>(`/public-quizzes/attempts?page=${page}${quizId ? `&quiz_id=${encodeURIComponent(quizId)}` : ''}`, { signal }),
    attempt: (id: string, signal?: AbortSignal) => request<QuizAttemptDetail>(`/public-quizzes/attempts/${encodeURIComponent(id)}`, { signal }),
    publication: (id: string, signal?: AbortSignal) => request<{ is_public: boolean; title: string }>(`/quizzes/${encodeURIComponent(id)}/publication`, { signal }),
    publish: (id: string, value: { is_public: boolean; title: string }) => request<{ is_public: boolean; title: string }>(`/quizzes/${encodeURIComponent(id)}/publication`, { method: 'PATCH', body: JSON.stringify(value) }),
  }
}
