<script setup lang="ts">
const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="footer">
    <div class="container footer__container">
      <p class="text-4 footer__copyright">© {{ currentYear }} StudyAI. Все права защищены.</p>

      <p class="text-4 footer__description">Платформа для эффективного обучения</p>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  width: 100%;
  padding-block: 32px;

  border-top: 1px solid var(--color-border);
}

.footer__container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
}

.footer__copyright,
.footer__description {
  color: var(--color-text-secondary);
}
</style>
