<script setup lang="ts">
import { onMounted, ref, watch } from 'vue';
import type { SummaryRow } from '@/api/generated/types';
import SegmentedControl from '@/components/SegmentedControl.vue';
import AnalyticsTabs from './components/AnalyticsTabs.vue';
import { analyticsApi } from './api';

const items = ref<SummaryRow[]>([]);
const loading = ref(false);
const granularity = ref<'DAY' | 'WEEK' | 'MONTH'>('DAY');

async function load() {
  loading.value = true;
  try {
    items.value = await analyticsApi.summary(granularity.value);
  } finally {
    loading.value = false;
  }
}

watch(granularity, load);
onMounted(load);
</script>

<template>
  <div class="page">
    <AnalyticsTabs />
    <header class="page-head">
      <div>
        <h1>Consumption summary</h1>
        <p class="muted">All-user totals over time.</p>
      </div>
      <SegmentedControl
        v-model="granularity"
        :options="[
          { value: 'DAY', label: 'Daily' },
          { value: 'WEEK', label: 'Weekly' },
          { value: 'MONTH', label: 'Monthly' },
        ]"
      />
    </header>

    <div class="surface-canvas">
      <table>
        <thead>
          <tr><th>Period</th><th>Requests</th><th>Input</th><th>Output</th><th>Total</th><th>Cost</th></tr>
        </thead>
        <tbody>
          <tr v-for="r in items" :key="r.period">
            <td>{{ r.period }}</td>
            <td>{{ r.request_count }}</td>
            <td>{{ r.total_input_tokens.toLocaleString() }}</td>
            <td>{{ r.total_output_tokens.toLocaleString() }}</td>
            <td>{{ r.total_tokens.toLocaleString() }}</td>
            <td>{{ r.total_cost }} {{ r.currency }}</td>
          </tr>
          <tr v-if="!loading && items.length === 0">
            <td colspan="6" class="empty">No usage in this period.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--s-md); }
.page-head { display: flex; justify-content: space-between; align-items: flex-end; gap: var(--s-md); flex-wrap: wrap; }
.empty { text-align: center; padding: var(--s-xl); color: var(--c-muted); }
</style>
