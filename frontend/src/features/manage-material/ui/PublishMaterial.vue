<script setup lang="ts">
import { computed, onBeforeUnmount, ref, useId, watch } from 'vue'
import { createPublicMaterialApi, type SharingGroup, type Visibility, type PublicationState } from '@/entities/material'
import { useSessionStore } from '@/entities/session'
import { BaseButton } from '@/shared/ui/button'
import { BaseModal } from '@/shared/ui/modal'
const props = defineProps<{ materialId: string }>()
const api = createPublicMaterialApi(useSessionStore().request)
const published = ref(false)
const title = ref('')
const visibility = ref<Visibility>('public')
const groupIds = ref<string[]>([])
const groups = ref<SharingGroup[]>([])
const saved = ref<PublicationState | null>(null)
const editing = ref(false)
const headingId = useId()
const pending = ref(false)
const groupPending = ref(false)
const error = ref('')
const groupError = ref('')
const groupEditing = ref(false)
const groupId = ref<string>()
const groupName = ref('')
const groupEmails = ref('')
const copied = ref(false)
const shareLink = computed(() => {
  const token = saved.value?.share_token
  return token ? `${window.location.origin}/community/materials/${props.materialId}#share=${encodeURIComponent(token)}` : ''
})
let controller = new AbortController()
function apply(state: PublicationState) {
  saved.value = state; published.value = state.is_public; title.value = state.title
  visibility.value = state.visibility; groupIds.value = [...state.group_ids]; copied.value = false
}
watch(() => props.materialId, async (id) => {
  controller.abort(); controller = new AbortController()
  const signal = controller.signal
  error.value = ''; pending.value = true; editing.value = false
  try { const state = await api.publication(id, signal); if (!signal.aborted) apply(state) }
  catch (reason) { if (!signal.aborted) error.value = reason instanceof Error ? reason.message : 'Не удалось получить статус доступа.' }
  finally { if (!signal.aborted) pending.value = false }
}, { immediate: true })
async function open() {
  if (saved.value) apply(saved.value)
  editing.value = true; error.value = ''; groupError.value = ''; groupEditing.value = false
  const signal = controller.signal
  try { const data = await api.groups(signal); if (!signal.aborted) groups.value = data }
  catch { if (!signal.aborted) error.value = 'Не удалось загрузить группы. Попробуйте открыть окно ещё раз.' }
}
async function save(publish = true, rotate = false) {
  if (pending.value || groupPending.value) return
  pending.value = true; error.value = ''
  const signal = controller.signal
  try {
    const state = await api.publish(props.materialId, { is_public: publish, title: title.value.trim(), visibility: visibility.value, group_ids: groupIds.value, rotate_link: rotate })
    if (!signal.aborted) {
      apply(state)
      if (!publish || state.visibility !== 'link') editing.value = false
    }
  } catch (reason) { if (!signal.aborted) error.value = reason instanceof Error ? reason.message : 'Не удалось изменить доступ.' }
  finally { if (!signal.aborted) pending.value = false }
}
function editGroup(group?: SharingGroup) {
  groupEditing.value = true; groupId.value = group?.id; groupName.value = group?.name || ''
  groupEmails.value = group?.emails.join('\n') || ''; groupError.value = ''
}
async function saveGroup() {
  if (groupPending.value || pending.value) return
  groupPending.value = true; groupError.value = ''
  const signal = controller.signal
  try {
    const group = await api.saveGroup({ name: groupName.value.trim(), emails: groupEmails.value.split(/[\s,;]+/).filter(Boolean) }, groupId.value)
    if (signal.aborted) return
    groups.value = [...groups.value.filter(g => g.id !== group.id), group]
    if (!groupIds.value.includes(group.id)) groupIds.value.push(group.id)
    groupEditing.value = false
  } catch (reason) { if (!signal.aborted) groupError.value = reason instanceof Error ? reason.message : 'Не удалось сохранить группу.' }
  finally { if (!signal.aborted) groupPending.value = false }
}
async function deleteGroup() {
  if (!groupId.value || groupPending.value || pending.value) return
  groupPending.value = true; groupError.value = ''
  const id = groupId.value
  const signal = controller.signal
  try {
    await api.deleteGroup(id)
    if (signal.aborted) return
    groups.value = groups.value.filter(g => g.id !== id); groupIds.value = groupIds.value.filter(i => i !== id)
    groupEditing.value = false
  } catch { if (!signal.aborted) groupError.value = 'Не удалось удалить группу.' }
  finally { if (!signal.aborted) groupPending.value = false }
}
async function copyLink() {
  try { await navigator.clipboard.writeText(shareLink.value); copied.value = true }
  catch { error.value = 'Не удалось скопировать. Выделите ссылку и скопируйте вручную.' }
}
onBeforeUnmount(() => controller.abort())
</script>
<template>
  <div class="publication">
    <div class="publication__actions">
      <BaseButton variant="transparent" :disabled="pending" @click="open">{{ published ? 'Настройки доступа' : 'Поделиться материалом' }}</BaseButton>
      <RouterLink v-if="published" class="text-link text-3" :to="`/community/materials/${materialId}`">Открыть материал</RouterLink>
    </div>
    <BaseModal :open="editing" :labelledby="headingId" @close="editing = false">
      <form class="publication publication__dialog" @submit.prevent="save()">
        <h2 :id="headingId" class="title-4">Доступ к материалу</h2>
        <label class="app-field text-3">Название<input v-model="title" data-modal-autofocus class="app-input" maxlength="200" required :disabled="pending" /></label>
        <label class="app-field text-3">Кто может открыть
          <select v-model="visibility" class="app-input" :disabled="pending || groupPending">
            <option value="public">Все пользователи</option>
            <option value="link">Только по ссылке</option>
            <option value="groups">Выбранные группы</option>
          </select>
        </label>
        <p class="text-3 muted">Доступ распространяется на лекцию, конспект, тест и рейтинг. Для просмотра нужен аккаунт. Получатели могут скачать материал или сохранить свою копию.</p>
        <p v-if="visibility === 'public'" class="text-3 muted">Материал появится в общей ленте сообщества.</p>
        <template v-if="visibility === 'link'">
          <p class="text-3 muted">В общей ленте его не будет. Открыть сможет любой, кому передадут ссылку. Для доступа только конкретных людей выберите группы.</p>
          <template v-if="shareLink && saved?.visibility === 'link'">
            <label class="app-field text-3">Ссылка для доступа<input :value="shareLink" class="app-input" readonly @focus="($event.target as HTMLInputElement).select()" /></label>
            <div class="publication__actions">
              <BaseButton variant="transparent" @click="copyLink">{{ copied ? 'Скопировано' : 'Скопировать ссылку' }}</BaseButton>
              <BaseButton variant="transparent" :disabled="pending || groupPending" @click="save(true, true)">Заменить ссылку</BaseButton>
            </div>
            <p class="text-3 muted">После замены старая ссылка и выданный по ней доступ перестанут работать. Сохранённые копии останутся у получателей.</p>
          </template>
          <p v-else class="text-3 muted">Ссылка появится после сохранения.</p>
        </template>
        <section v-if="visibility === 'groups'" class="publication">
          <p class="text-3 muted">Материал увидят только участники выбранных групп и вы. Email должен совпадать с адресом аккаунта.</p>
          <div v-for="group in groups" :key="group.id" class="publication__group">
            <label class="text-3"><input v-model="groupIds" type="checkbox" :value="group.id" :disabled="pending || groupPending" /> {{ group.name }} ({{ group.emails.length }})</label>
            <button type="button" class="text-link text-4" :disabled="pending || groupPending" @click="editGroup(group)">Изменить</button>
          </div>
          <BaseButton variant="transparent" :disabled="pending || groupPending" @click="editGroup()">Создать группу</BaseButton>
          <div v-if="groupEditing" class="notice publication">
            <label class="app-field text-3">Название группы<input v-model="groupName" class="app-input" maxlength="100" :disabled="groupPending" /></label>
            <label class="app-field text-3">Email участников<textarea v-model="groupEmails" class="app-input" rows="4" placeholder="По одному адресу на строку" :disabled="groupPending" /></label>
            <p class="text-4 muted">Изменения группы сразу применяются ко всем материалам, открытым для неё. При удалении группы её участники потеряют доступ через эту группу.</p>
            <div class="publication__actions">
              <BaseButton :loading="groupPending" :disabled="!groupName.trim()" @click="saveGroup">Сохранить группу</BaseButton>
              <BaseButton v-if="groupId" variant="transparent" :disabled="groupPending" @click="deleteGroup">Удалить группу</BaseButton>
              <BaseButton variant="transparent" :disabled="groupPending" @click="groupEditing = false">Отмена</BaseButton>
            </div>
          </div>
          <p v-if="groupError" class="text-3 danger" role="alert">{{ groupError }}</p>
        </section>
        <p v-if="published" class="text-3 muted">Сохранение добавит последний готовый тест. Закрытие доступа не удаляет копии и личные результаты получателей.</p>
        <div class="publication__actions">
          <BaseButton type="submit" :loading="pending" :disabled="!title.trim() || groupPending || (visibility === 'groups' && !groupIds.length)">{{ published ? 'Сохранить доступ' : 'Поделиться' }}</BaseButton>
          <BaseButton v-if="published" variant="transparent" :disabled="pending || groupPending" @click="save(false)">Закрыть доступ</BaseButton>
          <BaseButton variant="transparent" :disabled="pending || groupPending" @click="editing = false">{{ shareLink ? 'Закрыть' : 'Отмена' }}</BaseButton>
        </div>
        <p v-if="error" class="text-3 danger" role="alert">{{ error }}</p>
      </form>
    </BaseModal>
    <p v-if="error && !editing" class="text-3 danger" role="alert">{{ error }}</p>
  </div>
</template>
<style scoped>
.publication { display: flex; flex-direction: column; gap: 16px; }
.publication__dialog { width: 720px; max-width: 100%; box-sizing: border-box; padding: 40px 28px 28px; }
.publication__actions, .publication__group { display: flex; align-items: center; flex-wrap: wrap; gap: 16px; }
.publication__group { justify-content: space-between; }
.publication__group label { overflow-wrap: anywhere; min-width: 0; }
@media (max-width: 768px) {
  .publication__dialog { padding: 52px 20px 24px; }
}
</style>
