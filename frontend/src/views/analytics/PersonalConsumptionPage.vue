<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';
import type { PersonalConsumption } from '@/api/generated/types';
import SegmentedControl from '@/components/SegmentedControl.vue';
import AnalyticsTabs from './components/AnalyticsTabs.vue';
import { analyticsApi } from './api';

const data = ref<PersonalConsumption | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);
const periodType = ref<'DAY' | 'WEEK' | 'MONTH' | 'CURRENT_ACCUMULATED'>('CURRENT_ACCUMULATED');

async function load() {
  loading.value = true;
  error.value = null;
  try {
    data.value = await analyticsApi.personal({ period_type: periodType.value, granularity: 'DAY' });
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

watch(periodType, load);
onMounted(load);

const ratioLabel = computed(() => {
  if (!data.value) return '–';
  return `${(data.value.quota_usage_ratio * 100).toFixed(1)}%`;
});
</script>

<template>
  <div class="page">
    <AnalyticsTabs />
    <header class="page-head">
      <div>
        <h1>Personal consumption</h1>
        <p class="muted">Tokens and cost across your own gateway usage.</p>
      </div>
      <SegmentedControl
        v-model="periodType"
        :options="[
          { value: 'DAY', label: 'Today' },
          { value: 'WEEK', label: 'This week' },
          { value: 'MONTH', label: 'This month' },
          { value: 'CURRENT_ACCUMULATED', label: 'Period total' },
        ]"
      />
    </header>

    <div v-if="error" class="error">{{ error }}</div>

    <div v-if="data" class="cards">
      <article class="card">
        <p class="caption">Total tokens</p>
        <p class="metric">{{ data.total_tokens.toLocaleString() }}</p>
        <p class="muted">{{ data.total_input_tokens.toLocaleString() }} in · {{ data.total_output_tokens.toLocaleString() }} out</p>
      </article>
      <article class="card">
        <p class="caption">Total cost</p>
        <p class="metric">{{ data.total_cost }} <span class="curr">{{ data.currency }}</span></p>
      </article>
      <article class="card">
        <p class="caption">Period consumed</p>
        <p class="metric">{{ data.current_period_consumed }} / {{ data.current_period_limit }}</p>
        <div class="meter"><div class="meter-fill" :style="{ width: Math.min(100, data.quota_usage_ratio * 100) + '%' }" /></div>
        <p class="muted">{{ ratioLabel }} of period quota</p>
      </article>
    </div>

    <section v-if="data" class="card">
      <h3>Trend</h3>
      <table v-if="data.trend.length">
        <thead><tr><th>Day</th><th>Input</th><th>Output</th><th>Total</th><th>Cost</th></tr></thead>
        <tbody>
          <tr v-for="t in data.trend" :key="t.period">
            <td>{{ t.period }}</td>
            <td>{{ t.input_tokens.toLocaleString() }}</td>
            <td>{{ t.output_tokens.toLocaleString() }}</td>
            <td>{{ t.total_tokens.toLocaleString() }}</td>
            <td>{{ t.total_cost }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="muted">No usage in this period yet.</p>
    </section>

    <section v-if="data" class="card">
      <h3>By model</h3>
      <table v-if="data.by_model.length">
        <thead><tr><th>Model</th><th>Tokens</th><th>Cost</th></tr></thead>
        <tbody>
          <tr v-for="m in data.by_model" :key="m.model_id">
            <td class="mono">{{ m.model_name }}</td>
            <td>{{ m.total_tokens.toLocaleString() }}</td>
            <td>{{ m.total_cost }}</td>
          </tr>
        </tbody>
      </table>
      <p v-else class="muted">No model usage in this period.</p>
    </section>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--s-lg); }
.page-head { display: flex; justify-content: space-between; align-items: flex-end; gap: var(--s-md); flex-wrap: wrap; }
.cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: var(--s-lg); }
@media (max-width: 800px) { .cards { grid-template-columns: 1fr; } }
.caption { color: var(--c-muted); font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; margin: 0; }
.metric { font-family: var(--f-display); font-size: 32px; line-height: 1.1; margin: 6px 0; letter-spacing: -0.3px; }
.curr { font-size: 14px; color: var(--c-muted); }
.meter { width: 100%; height: 6px; background: var(--c-canvas); border: 1px solid var(--c-hairline); border-radius: var(--r-pill); margin-top: 8px; overflow: hidden; }
.meter-fill { height: 100%; background: var(--c-primary); }
.error { color: var(--c-error); }
</style>
