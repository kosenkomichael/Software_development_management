import { Marked, Renderer, type Token } from 'marked'
import DOMPurify from 'dompurify'

export interface NoteHeading {
  id: string
  title: string
  depth: number
}
interface RenderOptions {
  prefix: string
  materialId?: string
  imageUrls: Record<number, string>
  imageErrors: Record<number, string>
}

function escapeHtml(value: string) {
  return value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}
function plainText(tokens: Token[]): string {
  return tokens
    .map((token) =>
      'tokens' in token && Array.isArray(token.tokens)
        ? plainText(token.tokens)
        : 'text' in token
          ? String(token.text)
          : token.raw
    )
    .join('')
}

export function renderNoteMarkdown(source: string, options: RenderOptions) {
  const headings: NoteHeading[] = []
  const imageOrders = new Set<number>()
  const slugs = new Map<string, number>()
  const renderer = new Renderer()
  renderer.heading = function ({ tokens, depth }) {
    const title = plainText(tokens)
    const slug =
      title
        .toLowerCase()
        .replace(/[^\p{L}\p{N}\s-]/gu, '')
        .trim()
        .replace(/\s+/g, '-') || 'section'
    const occurrence = slugs.get(slug) ?? 0
    slugs.set(slug, occurrence + 1)
    const id = `${options.prefix}-${slug}${occurrence ? `-${occurrence}` : ''}`
    if (depth <= 2) headings.push({ id, title, depth })
    const tag = `h${Math.min(depth + 1, 6)}`
    return `<${tag} id="${escapeHtml(id)}">${this.parser.parseInline(tokens)}</${tag}>\n`
  }
  renderer.image = function (token) {
    const internal = token.href.match(/^\/api\/v1\/materials\/([^/]+)\/images\/(\d+)$/)
    if (internal && internal[1] === options.materialId) {
      const order = Number(internal[2])
      imageOrders.add(order)
      const url = options.imageUrls[order]
      const alt = escapeHtml(token.text || `Рисунок ${order}`)
      return url
        ? `<img src="${escapeHtml(url)}" alt="${alt}" loading="lazy" />`
        : `<span class="note-image-status" role="status">${escapeHtml(options.imageErrors[order] || 'Загружаем рисунок…')}</span>`
    }
    return Renderer.prototype.image.call(this, token)
  }
  renderer.link = function (token) {
    const href = token.href.startsWith('#')
      ? `#${options.prefix}-${token.href.slice(1)}`
      : token.href
    const external = !href.startsWith('#')
    return `<a href="${escapeHtml(href)}"${external ? ' target="_blank" rel="noopener noreferrer"' : ''}>${this.parser.parseInline(token.tokens)}</a>`
  }
  renderer.table = function (token) {
    return `<div class="note-table">${Renderer.prototype.table.call(this, token)}</div>`
  }
  renderer.checkbox = ({ checked }) =>
    `<span class="note-checkbox" aria-label="${checked ? 'Выполнено' : 'Не выполнено'}">${checked ? '☑' : '☐'}</span> `
  const parser = new Marked({ gfm: true, breaks: false, async: false, renderer })
  let rendered = parser.parse(source, { async: false })
  if (!headings.length) {
    const id = `${options.prefix}-intro`
    headings.push({ id, title: 'Конспект', depth: 1 })
    rendered = `<section id="${id}">${rendered}</section>`
  }
  const html = DOMPurify.sanitize(rendered, {
    ADD_ATTR: ['target'],
    FORBID_TAGS: [
      'script',
      'style',
      'iframe',
      'form',
      'input',
      'button',
      'textarea',
      'select',
      'object',
      'embed',
    ],
    FORBID_ATTR: ['style'],
    ALLOWED_URI_REGEXP:
      /^(?:(?:(?:f|ht)tps?|mailto|tel|blob):|[^a-z]|[a-z+.\-]+(?:[^a-z+.\-:]|$))/i,
  })
  return { html, headings, imageOrders: [...imageOrders] }
}
