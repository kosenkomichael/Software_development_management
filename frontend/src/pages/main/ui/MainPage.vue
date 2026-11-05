<script setup lang="ts">
import {
  HeroSection,
  HowItWorksSection,
  ResultExampleSection,
  CommunitySection,
} from '@/widgets/main'
</script>

<template>
  <main class="main-page">
    <HeroSection />
    <div class="container main-page__sections">
      <HowItWorksSection />
      <ResultExampleSection />
      <CommunitySection />
    </div>
  </main>
</template>

<style scoped>
.main-page__sections {
  display: flex;
  flex-direction: column;
  gap: 72px;
  padding-top: 64px;
}

@media (max-width: 768px) {
  .main-page__sections {
    gap: 40px;
    padding-top: 32px;
  }
}
</style>
