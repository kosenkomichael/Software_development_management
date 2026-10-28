<script setup lang="ts">
import { RouterView } from 'vue-router'

import { AppHeader } from '@/widgets/header'
import { AppFooter } from '@/widgets/footer'
</script>

<template>
  <div class="main-layout">
    <AppHeader />

    <div class="main-layout__content">
      <RouterView />
    </div>

    <AppFooter />
  </div>
</template>

<style scoped>
.main-layout {
  display: flex;
  flex-direction: column;

  min-height: 100vh;
  width: 100%;
  background-image: url('../../shared/assets/images/background.svg');
  background-size: cover;
  background-position: center top;
  background-repeat: no-repeat;
}

.main-layout__content {
  flex: 1;
}
</style>
