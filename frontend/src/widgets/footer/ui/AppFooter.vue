<script setup lang="ts">
import { useRouter } from 'vue-router'
import { ArrowRight } from 'lucide-vue-next'
import { BaseButton } from '@/shared/ui/button'
import { designAssets } from '@/shared/assets'

const router = useRouter()
</script>

<template>
  <footer class="container footer">
    <section
      class="surface footer__cta"
      :style="{ backgroundImage: `url(${designAssets.ctaBackground})` }"
    >
      <div>
        <p class="text-1 accent">Начни уже сегодня</p>
        <h2 class="title-1">Не переписывай лекции<br />Работай с ними</h2>
      </div>
      <div class="footer__cta-action">
        <p class="text-1">Загрузи первый материал и получи готовый тест с конспектом!</p>
        <BaseButton size="small" @click="router.push('/materials/new')"
          >Начать бесплатно<template #icon-right><ArrowRight /></template
        ></BaseButton>
      </div>
    </section>
  </footer>
</template>

<style scoped>
.footer {
  padding-top: 72px;
  padding-bottom: 80px;
}
.footer__cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 80px;
  min-height: 296px;
  padding: 44px 76px;
  background-size: cover;
  background-position: center;
  border-radius: var(--radius-panel);
}
.footer__cta h2 {
  margin-top: 32px;
  line-height: 1.1;
}
.footer__cta-action {
  display: flex;
  flex-direction: column;
  gap: 24px;
  flex: 0 1 493px;
}
.footer__cta-action .base-button {
  align-self: flex-start;
  min-width: 345px;
}

@media (max-width: 900px) {
  .footer {
    padding-block: 40px;
  }
  .footer__cta {
    flex-direction: column;
    align-items: stretch;
    gap: 24px;
    min-height: 0;
    padding: 32px 20px;
  }
  .footer__cta br {
    display: none;
  }
  .footer__cta-action {
    flex: 1 1 auto;
    align-items: stretch;
  }
  .footer__cta-action .base-button {
    min-width: 0;
    align-self: stretch;
  }
}
</style>
