<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { ConsumptionDetailRow } from '@/api/generated/types';
import AnalyticsTabs from './components/AnalyticsTabs.vue';
import { analyticsApi } from './api';

const items = ref<ConsumptionDetailRow[]>([]);
const total = ref(0);
const loading = ref(true);
const page = ref(1);
const pageSize = 20;

async function load() {
  loading.value = true;
  try {
    const res = await analyticsApi.details({ page: page.value, page_size: pageSize });
    items.value = res.items;
    total.value = res.total;
  } finally {
    loading.value = false;
  }
}

function next() {
  if (page.value * pageSize < total.value) {
    page.value += 1;
    load();
  }
}
function prev() {
  if (page.value > 1) {
    page.value -= 1;
    load();
  }
}

onMounted(load);
</script>

<template>
  <div class="page">
    <AnalyticsTabs />
    <header>
      <h1>Consumption details</h1>
      <p class="muted">Drill into individual gateway requests.</p>
    </header>

    <div class="surface-canvas">
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>User</th>
            <th>Key</th>
            <th>Model</th>
            <th>Input</th>
            <th>Output</th>
            <th>Cost</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in items" :key="r.usage_log_id">
            <td>{{ new Date(r.time).toLocaleString() }}</td>
            <td>{{ r.user_email }}</td>
            <td class="mono">{{ r.api_key_mask }}</td>
            <td class="mono">{{ r.model_name }}</td>
            <td>{{ r.input_tokens.toLocaleString() }}</td>
            <td>{{ r.output_tokens.toLocaleString() }}</td>
            <td>{{ r.cost }} {{ r.currency }}</td>
            <td>
              <span class="badge" :class="{ ok: r.status === 'SUCCESS', err: r.status === 'FAILED' || r.status === 'COST_FAILED' }">
                {{ r.status }}
              </span>
            </td>
          </tr>
          <tr v-if="!loading && items.length === 0">
            <td colspan="8" class="empty">No requests in this period.</td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="pager">
      <button class="btn ghost" :disabled="page === 1" @click="prev">‹ Prev</button>
      <span class="muted">Page {{ page }} of {{ Math.max(1, Math.ceil(total / pageSize)) }}</span>
      <button class="btn ghost" :disabled="page * pageSize >= total" @click="next">Next ›</button>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--s-md); }
.empty { text-align: center; padding: var(--s-xl); color: var(--c-muted); }
.pager { display: flex; gap: var(--s-sm); align-items: center; }
</style>
