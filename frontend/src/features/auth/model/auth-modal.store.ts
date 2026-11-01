import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useAuthModalStore = defineStore('auth-modal', () => {
  const isOpen = ref(false)
  const mode = ref<'login' | 'register'>('login')
  const email = ref('')
  const notice = ref('')
  const redirectTo = ref('')
  function open(nextMode: 'login' | 'register' = 'login') {
    mode.value = nextMode
    email.value = ''
    notice.value = ''
    isOpen.value = true
  }
  function close() {
    isOpen.value = false
  }
  function registered(registeredEmail: string) {
    email.value = registeredEmail
    notice.value = 'Аккаунт создан. Войдите с вашим email и паролем.'
    mode.value = 'login'
  }
  return { isOpen, mode, email, notice, redirectTo, open, close, registered }
})
