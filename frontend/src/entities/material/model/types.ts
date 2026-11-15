export type MaterialStatus = 'uploaded' | 'processing' | 'done' | 'failed'
export interface Material {
  id: string
  source_author?: string | null
  is_favorite?: boolean
  original_filename: string
  content_type: string
  size_bytes: number
  status: MaterialStatus
  created_at: string
  download_url?: string | null
}
export interface MaterialList {
  items: Material[]
  total: number
}
export interface Note {
  id: string
  material_id: string
  content: string
  created_at: string
}
export interface NoteStatus {
  material_id: string
  status: MaterialStatus
  note_id: string | null
}
export interface QuizAnswer {
  id: string
  text: string
}
export interface QuizQuestion {
  id: string
  text: string
  question_type: 'single' | 'multiple'
  order: number
  answers: QuizAnswer[]
}
export interface Quiz {
  title?: string | null
  id: string
  material_id: string
  status: 'processing' | 'done' | 'failed'
  questions: QuizQuestion[]
}
export interface QuizStatus {
  material_id: string
  status: 'processing' | 'done' | 'failed'
  quiz_id: string | null
}
export interface SubmittedAnswer {
  question_id: string
  selected_ids: string[]
}
export interface QuizResult {
  duration_ms?: number | null
  attempt_id?: string | null
  score: number
  total: number
  correct: number
  results: {
    question_id: string
    is_correct: boolean
    correct_ids: string[]
    explanation?: string | null
  }[]
}
export const materialStatusLabel: Record<MaterialStatus, string> = {
  uploaded: 'В очереди',
  processing: 'Обработка',
  done: 'Готово',
  failed: 'Ошибка обработки',
}
export function formatSize(bytes: number) {
  return bytes < 1024 * 1024
    ? `${(bytes / 1024).toFixed(0)} КБ`
    : `${(bytes / 1024 / 1024).toFixed(1)} МБ`
}

export interface QuizAttemptSummary {
  duration_ms?: number | null
  id: string
  quiz_id: string | null
  created_at: string
  score: number
  total: number
  correct: number
}
export interface QuizAttemptList {
  items: QuizAttemptSummary[]
  total: number
}
export interface QuizAttemptDetail extends QuizAttemptSummary {
  quiz: Quiz
  answers: SubmittedAnswer[]
  result: QuizResult
}

export function formatTrainingTime(milliseconds: number) {
  const ms = Math.max(0, Math.floor(milliseconds))
  return `${String(Math.floor(ms / 60000)).padStart(2, '0')}:${String(Math.floor(ms / 1000) % 60).padStart(2, '0')}`
}
