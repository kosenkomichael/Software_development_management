import type { AuthorizedRequest } from './material-api'
export interface PublicMaterialItem { id: string; title: string; author: string; published_at: string; size_bytes: number; has_quiz: boolean }
export interface PublicMaterialDetail extends PublicMaterialItem { filename: string; content_type: string; note_content: string; quiz_id: string | null }
export function createPublicMaterialApi(request: AuthorizedRequest) {
  return {
    list: (page = 1, signal?: AbortSignal) => request<{ items: PublicMaterialItem[]; total: number }>(`/public-materials?page=${page}`, { signal }),
    get: (id: string, signal?: AbortSignal) => request<PublicMaterialDetail>(`/public-materials/${encodeURIComponent(id)}`, { signal }),
    image: (id: string, order: number, signal?: AbortSignal) => request<Blob>(`/public-materials/${encodeURIComponent(id)}/images/${order}`, { signal, responseType: 'blob' }),
    download: (id: string, signal?: AbortSignal) => request<Blob>(`/public-materials/${encodeURIComponent(id)}/download`, { signal, responseType: 'blob' }),
    import: (id: string, signal?: AbortSignal) => request<{ material_id: string; imported: boolean }>(`/public-materials/${encodeURIComponent(id)}/import`, { method: 'POST', signal }),
    publication: (id: string, signal?: AbortSignal) => request<{ is_public: boolean; title: string; has_quiz: boolean }>(`/materials/${encodeURIComponent(id)}/publication`, { signal }),
    publish: (id: string, value: { is_public: boolean; title: string }) => request<{ is_public: boolean; title: string; has_quiz: boolean }>(`/materials/${encodeURIComponent(id)}/publication`, { method: 'PATCH', body: JSON.stringify(value) }),
  }
}
