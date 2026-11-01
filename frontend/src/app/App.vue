<script setup lang="ts">
import { RouterView } from 'vue-router'
import { AuthModal } from '@/features/auth'
import { useSessionStore } from '@/entities/session'

void useSessionStore().initialize()
</script>

<template>
  <RouterView />
  <AuthModal />
</template>
