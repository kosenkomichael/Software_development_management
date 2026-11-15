import type { AuthorizedRequest } from './material-api'
export interface PublicMaterialItem { visibility: Visibility; id: string; title: string; author: string; published_at: string; size_bytes: number; has_quiz: boolean }
export interface PublicMaterialDetail extends PublicMaterialItem { filename: string; content_type: string; note_content: string; quiz_id: string | null }
export interface SharingGroup { id: string; name: string; emails: string[] }
export type Visibility = 'public' | 'link' | 'groups'
export interface PublicationState { is_public: boolean; title: string; has_quiz: boolean; visibility: Visibility; group_ids: string[]; share_token: string | null }
export function createPublicMaterialApi(request: AuthorizedRequest) {
  return {
    list: (page = 1, signal?: AbortSignal) => request<{ items: PublicMaterialItem[]; total: number }>(`/public-materials?page=${page}`, { signal }),
    get: (id: string, signal?: AbortSignal, share?: string) => request<PublicMaterialDetail>(`/public-materials/${encodeURIComponent(id)}`, { signal, headers: share ? { 'X-Material-Share': share } : undefined }),
    image: (id: string, order: number, signal?: AbortSignal) => request<Blob>(`/public-materials/${encodeURIComponent(id)}/images/${order}`, { signal, responseType: 'blob' }),
    download: (id: string, signal?: AbortSignal) => request<Blob>(`/public-materials/${encodeURIComponent(id)}/download`, { signal, responseType: 'blob' }),
    import: (id: string, signal?: AbortSignal) => request<{ material_id: string; imported: boolean }>(`/public-materials/${encodeURIComponent(id)}/import`, { method: 'POST', signal }),
    groups: (signal?: AbortSignal) => request<SharingGroup[]>('/sharing-groups', { signal }),
    saveGroup: (value: { name: string; emails: string[] }, id?: string) => request<SharingGroup>(`/sharing-groups${id ? `/${encodeURIComponent(id)}` : ''}`, { method: id ? 'PUT' : 'POST', body: JSON.stringify(value) }),
    deleteGroup: (id: string) => request<void>(`/sharing-groups/${encodeURIComponent(id)}`, { method: 'DELETE' }),
    publication: (id: string, signal?: AbortSignal) => request<PublicationState>(`/materials/${encodeURIComponent(id)}/publication`, { signal }),
    publish: (id: string, value: { is_public: boolean; title: string; visibility?: Visibility; group_ids?: string[]; rotate_link?: boolean }) => request<PublicationState>(`/materials/${encodeURIComponent(id)}/publication`, { method: 'PATCH', body: JSON.stringify(value) }),
  }
}
