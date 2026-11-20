<script setup lang="ts">
import { BookOpen, ClipboardList } from 'lucide-vue-next'

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
    <h2 class="title-2">Пример результата</h2>
    <div class="result-example__preview">
      <div class="result-example__mock">
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
              <span class="result-example__chapter-number">{{ index + 1 }}.</span>
              <span>{{ chapter.title }}</span>
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
              набор сигналов, применяет к ним веса, суммирует и пропускает через функцию активации.
            </p>
            <div class="result-example__definition">
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
            <strong class="text-2">Тест</strong>
          </header>
          <div class="result-example__sheet">
            <p class="text-4 muted">Выберите один ответ</p>
            <h4 class="text-3">Какая функция активации чаще всего используется в скрытых слоях?</h4>
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
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.result-example__preview {
  display: block;
  width: 100%;
  margin-top: 40px;
  padding: 0;

  border: 2px solid var(--color-panel-border);
  border-radius: var(--radius-panel);

  background: var(--color-panel);
  color: var(--color-text-primary);

  text-align: left;
  overflow: hidden;
}
.result-example__mock {
  display: flex;
  align-items: stretch;
  gap: 24px;
  padding: 32px;
}

.result-example__toc {
  flex: 0 0 25%;
  min-width: 0;

  padding: 8px 20px 8px 0;

  border: 0;
  border-right: 1px solid var(--color-panel-border);
  background: transparent;
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
  gap: 4px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.result-example__toc-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  min-height: 46px;
  padding: 12px;
  border-radius: 12px;
  color: var(--color-text-primary);
  line-height: 1.5;
}
.result-example__chapter-number {
  flex-shrink: 0;
}
.result-example__toc-item--active {
  color: var(--color-yellow);
  background: linear-gradient(
    90deg,
    color-mix(in srgb, var(--color-orange) 42%, transparent),
    color-mix(in srgb, var(--color-orange) 16%, transparent)
  );
}
.result-example__card {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 16px;
  min-width: 0;
}
.result-example__card--notes {
  flex: 1.3;
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
  flex-shrink: 0;

  width: 64px;
  height: 64px;

  border-radius: 18px;
  color: var(--color-white);
}

.result-example__card--notes .result-example__card-icon {
  background-color: var(--color-green);
}

.result-example__card--quiz .result-example__card-icon {
  background-color: var(--color-orange);
}

.result-example__card-icon svg {
  width: 32px;
  height: 32px;
}

.result-example__sheet {
  flex: 1;
  min-width: 0;
  padding: 24px;

  border: 1px solid var(--color-panel-border);
  border-radius: var(--radius-card);

  background: var(--color-background);
  color: var(--color-text-primary);
}
.result-example__card--notes .result-example__sheet {
  line-height: 1.8;
}
.result-example__sheet h4 {
  margin: 0 0 16px;
  font-weight: var(--font-weight-semibold);
  line-height: 1.4;
}

.result-example__sheet p {
  margin: 0 0 16px;
  line-height: 1.6;
  color: var(--color-text-secondary);
}

.result-example__sheet p strong {
  color: var(--color-text-primary);
}

.result-example__definition p {
  margin: 0;
  color: var(--color-text-primary);
}
.result-example__card--notes .result-example__sheet h4 {
  margin-top: 2px;
}
.result-example__definition {
  display: flex;
  align-items: flex-start;
  gap: 10px;
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
  gap: 14px;
  margin: 24px 0;
  padding: 0;
  list-style: none;
}

.result-example__options li {
  display: flex;
  align-items: center;
  gap: 12px;
  color: var(--color-text-secondary);
}

.result-example__radio {
  width: 18px;
  height: 18px;
  flex-shrink: 0;

  border: 2px solid var(--color-text-secondary);
  border-radius: 50%;
}
.result-example__option--picked {
  color: var(--color-text-primary) !important;
  font-weight: var(--font-weight-semibold);
}

.result-example__option--picked .result-example__radio {
  border-color: var(--color-orange);
  background: radial-gradient(circle, var(--color-orange) 0 45%, transparent 50%);
}
.result-example__option--picked .result-example__radio::before {
  content: '';
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-dark);
}
.result-example__next {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 50px;
  padding: 12px 16px;
  border-radius: var(--border-radius-sm);
  background: var(--color-yellow);
  color: var(--color-background);
}
@media (max-width: 1100px) {
  .result-example__mock {
    flex-wrap: wrap;
  }

  .result-example__toc {
    flex: 1 1 100%;
    border-right: 0;
    border-bottom: 1px solid var(--color-panel-border);
    padding: 0 0 20px;
  }

  .result-example__card,
  .result-example__card--notes {
    flex: 1 1 calc(50% - 12px);
  }
}

@media (max-width: 768px) {
  .result-example__mock {
    flex-direction: column;
    gap: 24px;
    padding: 20px;
  }

  .result-example__toc,
  .result-example__card,
  .result-example__card--notes {
    flex: 1 1 auto;
    width: 100%;
  }

  .result-example__sheet {
    padding: 20px;
  }
  .result-example__card-icon {
    width: 48px;
    height: 48px;
    border-radius: 14px;
  }

  .result-example__card-icon svg {
    width: 24px;
    height: 24px;
  }
}
</style>
