export type MaterialStatus = 'uploaded' | 'processing' | 'done' | 'failed'
export interface Material {
  id: string
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
  question_type: 'single' | 'multiple' | 'open'
  order: number
  answers: QuizAnswer[]
}
export interface Quiz {
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
  open_answer?: string
}
export interface QuizResult {
  score: number
  total: number
  correct: number
  results: {
    question_id: string
    is_correct: boolean | null
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
