<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { WorkbenchModelOut } from '@/api/generated/types';
import { workbenchApi } from './api';

const models = ref<WorkbenchModelOut[]>([]);
const loading = ref(true);

onMounted(async () => {
  try {
    const page = await workbenchApi.listModels();
    models.value = page.items;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="page">
    <header>
      <h1>Model catalog</h1>
      <p class="muted">All models configured by your platform administrators.</p>
    </header>
    <div class="surface-canvas">
      <table>
        <thead>
          <tr>
            <th>Provider</th>
            <th>Model</th>
            <th>Input ($/1M)</th>
            <th>Output ($/1M)</th>
            <th>Currency</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="m in models" :key="m.model_id">
            <td>{{ m.provider_name }}</td>
            <td class="mono">{{ m.model_name }}</td>
            <td>{{ m.input_price_per_million_tokens }}</td>
            <td>{{ m.output_price_per_million_tokens }}</td>
            <td>{{ m.currency }}</td>
          </tr>
          <tr v-if="!loading && models.length === 0">
            <td colspan="5" class="empty">No models configured.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--s-lg); }
.empty { text-align: center; color: var(--c-muted); padding: var(--s-xl); }
</style>
