<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, useId, watch } from 'vue'
import { BookOpen, ChevronsLeft, Download } from 'lucide-vue-next'
import { BaseButton } from '@/shared/ui/button'
import { useSessionStore } from '@/entities/session'
import { createMaterialApi } from '@/entities/material'
import { renderNoteMarkdown } from '../model/render-note-markdown'
import renderMathInElement from 'katex/contrib/auto-render'
import 'katex/dist/katex.min.css'

const props = defineProps<{
  content: string
  filename?: string
  materialId?: string
  detailed?: boolean
}>()
const api = createMaterialApi(useSessionStore().request)
const prefix = `note-${useId().replace(/[^a-zA-Z0-9-]/g, '')}`
const collapsed = ref(false)
const article = ref<HTMLElement>()
const activeId = ref('')
const images = ref<Record<number, string>>({})
const imageErrors = ref<Record<number, string>>({})
const markdown = computed(() =>
  renderNoteMarkdown(props.content, {
    prefix,
    materialId: props.materialId,
    imageUrls: images.value,
    imageErrors: imageErrors.value,
  })
)
let imageController = new AbortController()
let pendingImages = new Set<number>()
let headingNodes: HTMLElement[] = []
let observer: ResizeObserver | undefined
let frame: number | undefined

function clearImages() {
  imageController.abort()
  Object.values(images.value).forEach((url) => URL.revokeObjectURL(url))
  images.value = {}
  imageErrors.value = {}
  pendingImages = new Set()
}
watch(
  () => `${props.materialId ?? ''}\u0000${props.content}`,
  () => {
    clearImages()
    imageController = new AbortController()
    activeId.value = ''
  },
  { flush: 'sync' }
)
watch(
  [() => props.content, () => props.materialId, () => markdown.value.imageOrders.join(',')],
  async () => {
    if (!props.materialId) return
    const signal = imageController.signal
    const requests = pendingImages
    for (const order of markdown.value.imageOrders) {
      if (signal.aborted) break
      if (images.value[order] || requests.has(order)) continue
      requests.add(order)
      try {
        const blob = await api.image(props.materialId, order, signal)
        if (!signal.aborted) images.value[order] = URL.createObjectURL(blob)
      } catch {
        if (!signal.aborted) imageErrors.value[order] = 'Не удалось загрузить рисунок.'
      } finally {
        requests.delete(order)
      }
    }
  },
  { immediate: true, flush: 'post' }
)

function hasInnerScroll() {
  return !!article.value && ['auto', 'scroll'].includes(getComputedStyle(article.value).overflowY)
}
function updateActive() {
  const root = article.value
  if (!root || !root.getBoundingClientRect().width || !headingNodes.length) return
  const inner = hasInnerScroll()
  const threshold = inner ? Math.max(24, root.getBoundingClientRect().top + 24) : 36
  let current = headingNodes[0]!
  for (const heading of headingNodes) {
    if (heading.getBoundingClientRect().top <= threshold) current = heading
    else break
  }
  const atBottom = inner
    ? root.scrollTop > 0 && root.scrollTop + root.clientHeight >= root.scrollHeight - 4
    : window.scrollY > 0 &&
      window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 4
  if (atBottom) current = headingNodes[headingNodes.length - 1]!
  activeId.value = current.id
}
function onScroll() {
  if (frame !== undefined) return
  frame = requestAnimationFrame(() => {
    frame = undefined
    updateActive()
  })
}
function scrollToHeading(id: string) {
  const root = article.value
  const heading = root?.querySelector<HTMLElement>(`[id="${CSS.escape(id)}"]`)
  if (!root || !heading) return
  activeId.value = id
  const behavior = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ? 'instant'
    : 'smooth'
  if (hasInnerScroll())
    root.scrollTo({
      top:
        root.scrollTop +
        heading.getBoundingClientRect().top -
        root.getBoundingClientRect().top -
        20,
      behavior,
    })
  else window.scrollTo({ top: window.scrollY + heading.getBoundingClientRect().top - 28, behavior })
}
function onMarkdownClick(event: MouseEvent) {
  const link = (event.target as Element).closest('a')
  const href = link?.getAttribute('href')
  if (!href?.startsWith('#')) return
  const id = href.slice(1)
  if (article.value?.querySelector(`[id="${CSS.escape(id)}"]`)) {
    event.preventDefault()
    scrollToHeading(id)
  }
}
function bindHeadings() {
  if (!article.value) return
  headingNodes = markdown.value.headings
    .map((heading) => document.getElementById(heading.id))
    .filter((element): element is HTMLElement => !!element && !!article.value?.contains(element))
  observer?.disconnect()
  observer?.observe(article.value)
  onScroll()
}
watch(
  () => markdown.value.html,
  async () => {
    await nextTick()
    if (article.value)
      renderMathInElement(article.value, {
        delimiters: [
          { left: '$$', right: '$$', display: true },
          { left: '$', right: '$', display: false },
          { left: '\\(', right: '\\)', display: false },
          { left: '\\[', right: '\\]', display: true },
        ],
        throwOnError: false,
      })
    bindHeadings()
  },
  { flush: 'post', immediate: true }
)
onMounted(() => {
  if (typeof ResizeObserver !== 'undefined') observer = new ResizeObserver(onScroll)
  window.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('resize', onScroll, { passive: true })
  bindHeadings()
})
onBeforeUnmount(() => {
  clearImages()
  observer?.disconnect()
  window.removeEventListener('scroll', onScroll)
  window.removeEventListener('resize', onScroll)
  if (frame !== undefined) cancelAnimationFrame(frame)
})
function download() {
  const url = URL.createObjectURL(
    new Blob([props.content], { type: 'text/markdown;charset=utf-8' })
  )
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = `${props.filename?.replace(/\.[^.]+$/, '') || 'конспект'}.md`
  anchor.click()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
</script>

<template>
  <section
    class="surface note-reader"
    :class="{ 'note-reader--detailed': detailed, 'note-reader--collapsed': collapsed }"
  >
    <aside class="note-reader__navigation">
      <header class="note-reader__heading">
        <BookOpen v-if="!detailed && !collapsed" class="accent" :size="28" aria-hidden="true" />
        <h2 v-if="!collapsed" class="text-2">{{ detailed ? 'Содержание' : 'Конспект' }}</h2>
        <button
          class="icon-button"
          type="button"
          :aria-label="collapsed ? 'Показать содержание' : 'Свернуть содержание'"
          :aria-expanded="!collapsed"
          :aria-controls="`${prefix}-toc`"
          @click="collapsed = !collapsed"
        >
          <ChevronsLeft
            :size="20"
            :style="{ transform: collapsed ? 'rotate(180deg)' : undefined }"
          />
        </button>
      </header>
      <nav v-show="!collapsed" :id="`${prefix}-toc`" aria-label="Содержание конспекта">
        <button
          v-for="(heading, index) in markdown.headings"
          :key="heading.id"
          class="note-reader__chapter text-4"
          :class="{ 'note-reader__chapter--active': activeId === heading.id }"
          :aria-current="activeId === heading.id ? 'location' : undefined"
          type="button"
          @click="scrollToHeading(heading.id)"
        >
          <span class="note-reader__chapter-number">{{ index + 1 }}.</span
          ><span>{{ heading.title.replace(/^\d+[.)]\s*/, '') }}</span>
        </button>
      </nav>
      <BaseButton
        v-if="!collapsed"
        class="note-reader__download"
        variant="transparent"
        @click="download"
        ><template #icon-left><Download /></template>Скачать конспект</BaseButton
      >
    </aside>
    <article
      ref="article"
      class="note-reader__content"
      aria-label="Конспект"
      tabindex="0"
      @scroll.passive="onScroll"
      @load.capture="onScroll"
      @click="onMarkdownClick"
    >
      <div class="note-reader__markdown" v-html="markdown.html" />
    </article>
  </section>
</template>

<style scoped>
.note-reader {
  display: flex;
  align-items: stretch;
  gap: 0;
  padding: 0;
  min-height: 400px;
  border-width: 1px;
}
.note-reader__navigation {
  position: sticky;
  top: 24px;
  align-self: flex-start;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex: 0 0 28%;
  width: 28%;
  max-height: calc(100svh - 48px);
  padding: 18px 12px;
  overflow-y: auto;
}
.note-reader__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 0 6px;
}
.note-reader__heading h2 {
  flex: 1;
  font-weight: var(--font-weight-semibold);
}
.note-reader__heading .icon-button {
  width: 32px;
  height: 32px;
  border: 1px solid var(--color-panel-border);
  border-radius: var(--border-radius-sm);
  background: var(--color-panel);
}
.note-reader nav {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.note-reader__chapter {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-height: 46px;
  padding: 12px;
  border: 0;
  border-radius: 12px;
  background: transparent;
  color: var(--color-text-primary);
  text-align: left;
  line-height: 1.5;
  transition:
    background-color var(--transition-default),
    color var(--transition-default);
}
.note-reader__chapter-number {
  flex-shrink: 0;
}
.note-reader__chapter:hover {
  background: color-mix(in srgb, var(--color-orange) 12%, transparent);
}
.note-reader__chapter--active {
  color: var(--color-yellow);
  background: linear-gradient(
    90deg,
    color-mix(in srgb, var(--color-orange) 42%, transparent),
    color-mix(in srgb, var(--color-orange) 16%, transparent)
  );
}
.note-reader__download {
  margin-top: 16px;
  align-self: flex-start;
  min-height: 40px;
  padding: 10px 12px;
  font-size: var(--font-size-text-4);
}
.note-reader__content {
  flex: 1;
  min-width: 0;
  max-height: calc(100svh - 180px);
  overflow: auto;
  padding: 24px 28px;
  border-left: 1px solid var(--color-panel-border);
  border-radius: 0 var(--border-radius-md) var(--border-radius-md) 0;
}
.note-reader--detailed {
  background: linear-gradient(
    135deg,
    color-mix(in srgb, var(--color-panel) 85%, transparent),
    color-mix(in srgb, var(--color-background) 94%, transparent)
  );
}
.note-reader--collapsed .note-reader__navigation {
  flex-basis: 60px;
  width: 60px;
  padding-inline: 10px;
}
.note-reader--collapsed .note-reader__heading {
  padding-inline: 0;
}
.note-reader__markdown {
  font-size: var(--font-size-text-3);
  line-height: 1.75;
  overflow-wrap: anywhere;
}
.note-reader__markdown :deep(h2),
.note-reader__markdown :deep(h3) {
  font-size: var(--font-size-text-1);
  font-weight: var(--font-weight-semibold);
  line-height: 1.4;
  margin: 34px 0 18px;
  scroll-margin-top: 28px;
}
.note-reader__markdown :deep(h4),
.note-reader__markdown :deep(h5),
.note-reader__markdown :deep(h6) {
  font-size: var(--font-size-text-2);
  font-weight: var(--font-weight-semibold);
  line-height: 1.5;
  margin: 26px 0 12px;
  scroll-margin-top: 28px;
}
.note-reader__markdown :deep(> :first-child) {
  margin-top: 0;
}
.note-reader__markdown :deep(p) {
  margin: 0 0 16px;
}
.note-reader__markdown :deep(strong) {
  font-weight: var(--font-weight-bold);
}
.note-reader__markdown :deep(ul),
.note-reader__markdown :deep(ol) {
  margin: 12px 0 22px;
  padding-left: 26px;
}
.note-reader__markdown :deep(li) {
  padding-left: 4px;
  margin-bottom: 8px;
}
.note-reader__markdown :deep(li::marker) {
  color: var(--color-yellow);
}
.note-reader__markdown :deep(li p) {
  margin-bottom: 6px;
}
.note-reader__markdown :deep(blockquote) {
  margin: 22px 0;
  padding: 18px 22px;
  border: 1px solid color-mix(in srgb, var(--color-orange) 55%, transparent);
  border-left: 3px solid var(--color-yellow);
  border-radius: var(--radius-card);
  background: linear-gradient(
    120deg,
    color-mix(in srgb, var(--color-orange) 30%, transparent),
    color-mix(in srgb, var(--color-orange) 10%, transparent)
  );
}
.note-reader__markdown :deep(blockquote p:last-child) {
  margin-bottom: 0;
}
.note-reader__markdown :deep(a) {
  color: var(--color-yellow);
  text-underline-offset: 3px;
}
.note-reader__markdown :deep(pre) {
  margin: 20px 0;
  padding: 20px;
  border: 1px solid var(--color-panel-border);
  border-radius: var(--radius-card);
  background: var(--color-background);
  overflow-x: auto;
  line-height: 1.65;
}
.note-reader__markdown :deep(code) {
  font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
  font-size: 0.9em;
}
.note-reader__markdown :deep(:not(pre) > code) {
  padding: 3px 6px;
  border-radius: 6px;
  background: var(--color-auth-input);
  color: var(--color-yellow);
}
.note-reader__markdown :deep(.note-table) {
  overflow-x: auto;
  margin: 22px 0;
}
.note-reader__markdown :deep(table) {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-text-4);
}
.note-reader__markdown :deep(th),
.note-reader__markdown :deep(td) {
  padding: 12px 16px;
  border: 1px solid var(--color-border-muted);
  text-align: left;
}
.note-reader__markdown :deep(th) {
  background: var(--color-auth-input);
  font-weight: var(--font-weight-semibold);
}
.note-reader__markdown :deep(tr:nth-child(even)) {
  background: color-mix(in srgb, var(--color-panel) 55%, transparent);
}
.note-reader__markdown :deep(img) {
  display: block;
  max-width: 100%;
  height: auto;
  margin: 22px auto;
  border-radius: var(--border-radius-sm);
}
.note-reader__markdown :deep(hr) {
  border: 0;
  border-top: 1px solid var(--color-border-muted);
  margin: 32px 0;
}
.note-reader__markdown :deep(.note-image-status) {
  display: block;
  padding: 20px;
  border: 1px dashed var(--color-border-muted);
  border-radius: var(--radius-card);
  color: var(--color-text-secondary);
}
.note-reader__markdown :deep(.note-checkbox) {
  color: var(--color-yellow);
}
@media (max-width: 900px) {
  .note-reader {
    flex-direction: column;
    min-height: 0;
  }
  .note-reader__navigation {
    position: static;
    align-self: stretch;
    flex: none;
    width: auto;
    max-height: none;
    overflow-y: visible;
  }
  .note-reader nav {
    flex-direction: row;
    gap: 8px;
    overflow-x: auto;
    padding-bottom: 8px;
  }
  .note-reader__chapter {
    flex: 0 0 auto;
    min-height: 44px;
  }
  .note-reader--collapsed .note-reader__navigation {
    flex-basis: auto;
    width: auto;
  }
  .note-reader__content {
    max-height: none;
    overflow: visible;
    border-left: 0;
    border-top: 1px solid var(--color-panel-border);
    border-radius: 0 0 var(--border-radius-md) var(--border-radius-md);
  }
}
@media (max-width: 768px) {
  .note-reader__heading .icon-button {
    width: 44px;
    height: 44px;
  }
  .note-reader__content {
    padding: 16px 12px;
  }
  .note-reader__markdown :deep(ul),
  .note-reader__markdown :deep(ol) {
    padding-left: 18px;
  }
}
</style>
