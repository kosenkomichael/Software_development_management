<script setup lang="ts">
import { useRouter } from 'vue-router'
import { BookOpen, ClipboardList, Info, Sparkles } from 'lucide-vue-next'

const router = useRouter()
function showExample(index = 0) {
  void router.push({ name: 'demo', query: index ? { tab: 'quiz' } : {} })
}
const chapters = [
  { title: 'Формальный нейрон', active: true },
  { title: 'Функции активации' },
  { title: 'Обучение сети' },
  { title: 'Функции потерь' },
  { title: 'Регуляризация' },
  { title: 'Примеры и применение' },
]
const options = ['Линейная', 'ReLU', 'Сигмоида', 'tanh']
</script>

<template>
  <section class="result-example__example">
    <h2 class="title-1">Пример результата</h2>
    <button
      class="result-example__preview"
      type="button"
      aria-label="Открыть пример конспекта и теста"
      @click="showExample()"
    >
      <div class="result-example__mock" aria-hidden="true">
        <div class="result-example__toc">
          <h3 class="text-1">Основы нейронных сетей</h3>
          <p class="text-4 muted">Лекция №4 · 28 страниц</p>
          <ul>
            <li
              v-for="(chapter, index) in chapters"
              :key="chapter.title"
              class="text-4 result-example__toc-item"
              :class="{ 'result-example__toc-item--active': chapter.active }"
            >
              <Sparkles v-if="chapter.active" :size="16" />
              <span>{{ index + 1 }}. {{ chapter.title }}</span>
            </li>
          </ul>
        </div>
        <div class="result-example__card result-example__card--notes">
          <header class="result-example__card-head">
            <span class="result-example__card-icon"><BookOpen :size="22" /></span>
            <strong class="text-2">Конспект</strong>
          </header>
          <div class="result-example__sheet">
            <h4 class="text-2">1. Формальный нейрон</h4>
            <p class="text-3">
              <strong>Формальный нейрон</strong> — математическая модель, которая принимает на вход
              набор сигналов, применяет к ним веса, суммирует и пропускает через функцию
              активации.
            </p>
            <div class="result-example__definition">
              <span class="result-example__definition-icon"><Info :size="18" /></span>
              <p class="text-3">
                <strong>Ключевое определение</strong><br />
                Нейрон — базовая вычислительная единица искусственной нейронной сети.
              </p>
            </div>
          </div>
        </div>
        <div class="result-example__card result-example__card--quiz">
          <header class="result-example__card-head">
            <span class="result-example__card-icon"><ClipboardList :size="22" /></span>
            <strong class="text-2">Тест · 10 вопросов</strong>
          </header>
          <div class="result-example__sheet">
            <p class="text-3">Вопрос 1 из 10</p>
            <h4 class="text-3">
              Какая функция активации чаще всего используется в скрытых слоях?
            </h4>
            <ul class="result-example__options">
              <li
                v-for="option in options"
                :key="option"
                class="text-3"
                :class="{ 'result-example__option--picked': option === 'ReLU' }"
              >
                <span class="result-example__radio" aria-hidden="true" />
                {{ option }}
              </li>
            </ul>
            <span class="result-example__next text-3">Следующий вопрос →</span>
          </div>
        </div>
      </div>
    </button>
  </section>
</template>

<style scoped>
.result-example__preview {
  display: block;
  width: 100%;
  margin-top: 80px;
  padding: 0;
  border: 0;
  border-radius: var(--radius-panel);
  background: var(--color-panel);
  overflow: hidden;
}
.result-example__mock {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(0, 1.5fr) minmax(0, 1.15fr);
  gap: 24px;
  padding: 32px;
}
.result-example__toc {
  padding: 20px;
  border: 1px solid var(--color-panel-border);
  border-radius: var(--radius-card);
  background: var(--color-background);
}
.result-example__toc h3 {
  margin: 0;
  font-weight: var(--font-weight-semibold);
  color: var(--color-text-primary);
}
.result-example__toc p {
  margin: 6px 0 18px;
}
.result-example__toc ul {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.result-example__toc-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--border-radius-sm);
  color: var(--color-text-secondary);
}
.result-example__toc-item--active {
  background: var(--color-active);
  color: var(--color-yellow);
}
.result-example__card {
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}
.result-example__card-head {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--color-text-primary);
}
.result-example__card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: var(--border-radius-sm);
  background: var(--color-orange);
  color: var(--color-text-primary);
}
.result-example__sheet {
  flex: 1;
  padding: 20px;
  border-radius: var(--radius-card);
  background: var(--color-yellow);
  color: var(--color-dark);
}
.result-example__sheet h4 {
  margin: 0 0 10px;
  font-weight: var(--font-weight-semibold);
}
.result-example__sheet p {
  margin: 0 0 10px;
}
.result-example__card--notes .result-example__sheet h4 {
  margin-top: 2px;
}
.result-example__definition {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: var(--border-radius-sm);
  background: color-mix(in srgb, var(--color-orange) 35%, var(--color-yellow));
}
.result-example__definition p {
  margin: 0;
}
.result-example__definition-icon {
  display: flex;
  flex-shrink: 0;
  margin-top: 2px;
}
.result-example__options {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 14px 0 18px;
  padding: 0;
  list-style: none;
}
.result-example__options li {
  display: flex;
  align-items: center;
  gap: 10px;
}
.result-example__radio {
  width: 16px;
  height: 16px;
  border: 1.5px solid color-mix(in srgb, var(--color-dark) 45%, transparent);
  border-radius: 50%;
}
.result-example__option--picked {
  font-weight: var(--font-weight-semibold);
}
.result-example__option--picked .result-example__radio {
  border-color: var(--color-orange);
  background: radial-gradient(circle, var(--color-orange) 0 45%, transparent 50%);
}
.result-example__next {
  display: inline-block;
  padding: 10px 16px;
  border-radius: var(--border-radius-sm);
  background: var(--color-orange);
  color: var(--color-text-primary);
}
@media (max-width: 900px) {
  .result-example__mock {
    grid-template-columns: 1fr;
    padding: 20px;
  }
}
</style>
