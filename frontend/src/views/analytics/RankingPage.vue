<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { RankingResponse } from '@/api/generated/types';
import AnalyticsTabs from './components/AnalyticsTabs.vue';
import { analyticsApi } from './api';

const data = ref<RankingResponse | null>(null);
const loading = ref(true);

onMounted(async () => {
  try {
    data.value = await analyticsApi.ranking();
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page">
    <AnalyticsTabs />
    <header>
      <h1>Consumption ranking</h1>
      <p class="muted">Top 30% of users — names anonymised, your row marked.</p>
    </header>

    <div class="surface-canvas">
      <table>
        <thead><tr><th>Rank</th><th>User</th><th>Tokens</th><th>Cost</th></tr></thead>
        <tbody>
          <tr v-for="e in data?.entries ?? []" :key="e.rank" :class="{ me: e.is_current_user }">
            <td>#{{ e.rank }}</td>
            <td>
              <span class="badge" :class="{ coral: e.is_current_user }">{{ e.display_name }}</span>
            </td>
            <td>{{ e.total_tokens.toLocaleString() }}</td>
            <td>{{ e.total_cost }}</td>
          </tr>
          <tr v-if="!loading && (!data || data.entries.length === 0)">
            <td colspan="4" class="empty">No usage recorded yet.</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p v-if="data" class="muted small">{{ data.total_users }} users with usage in this period.</p>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--s-md); }
.empty { text-align: center; padding: var(--s-xl); color: var(--c-muted); }
.me td { background: var(--c-surface-card); }
.small { font-size: 12px; }
</style>
