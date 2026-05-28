<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { QuotaPolicyOut } from '@/api/generated/types';
import AdminTabs from './components/AdminTabs.vue';
import { adminApi } from './api';

const policy = ref<QuotaPolicyOut | null>(null);
const loading = ref(true);
const saving = ref(false);
const error = ref<string | null>(null);
const okMessage = ref<string | null>(null);

const form = ref({
  reset_mode: 'MONTHLY',
  reset_day_of_month: 1,
  reset_time: '00:00',
  timezone: 'UTC',
});

async function refresh() {
  loading.value = true;
  try {
    policy.value = await adminApi.getQuotaPolicy();
    form.value = {
      reset_mode: policy.value.reset_mode,
      reset_day_of_month: policy.value.reset_day_of_month ?? 1,
      reset_time: (policy.value.reset_time ?? '00:00').toString().slice(0, 5),
      timezone: policy.value.timezone ?? 'UTC',
    };
  } finally {
    loading.value = false;
  }
}

async function save() {
  saving.value = true;
  error.value = null;
  okMessage.value = null;
  try {
    await adminApi.updateQuotaPolicy({
      reset_mode: form.value.reset_mode,
      reset_day_of_month: form.value.reset_mode === 'MONTHLY' ? form.value.reset_day_of_month : null,
      reset_time: form.value.reset_mode === 'MONTHLY' ? `${form.value.reset_time}:00` : null,
      timezone: form.value.timezone,
    });
    okMessage.value = 'Quota reset policy saved.';
    await refresh();
  } catch (e: any) {
    error.value = e.message;
  } finally {
    saving.value = false;
  }
}

onMounted(refresh);
</script>

<template>
  <div class="page">
    <AdminTabs />
    <header>
      <h1>Quota reset policy</h1>
      <p class="muted">Determines when per-user cost limits reset.</p>
    </header>

    <div class="card limit-card">
      <div class="form-row">
        <label>Reset mode</label>
        <select v-model="form.reset_mode">
          <option value="MONTHLY">Monthly</option>
          <option value="NONE">Never reset</option>
        </select>
      </div>
      <template v-if="form.reset_mode === 'MONTHLY'">
        <div class="row-grid">
          <div class="form-row">
            <label>Day of month</label>
            <input v-model.number="form.reset_day_of_month" type="number" min="1" max="28" />
          </div>
          <div class="form-row">
            <label>Reset time</label>
            <input v-model="form.reset_time" type="time" />
          </div>
        </div>
        <div class="form-row">
          <label>Timezone</label>
          <input v-model="form.timezone" placeholder="UTC" />
        </div>
      </template>
      <div class="actions">
        <button class="btn primary" :disabled="saving" @click="save">{{ saving ? 'Saving…' : 'Save policy' }}</button>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="okMessage" class="ok">{{ okMessage }}</p>
    </div>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--s-md); }
.limit-card { max-width: 540px; }
.row-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--s-md); }
.actions { margin-top: var(--s-md); }
.error { color: var(--c-error); }
.ok { color: var(--c-success); }
</style>
