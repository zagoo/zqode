<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { AdminAPIKeyOut } from '@/api/generated/types';
import Modal from '@/components/Modal.vue';
import AdminTabs from './components/AdminTabs.vue';
import { adminApi } from './api';

const items = ref<AdminAPIKeyOut[]>([]);
const loading = ref(true);
const show = ref(false);
const extending = ref<AdminAPIKeyOut | null>(null);
const newExpiry = ref('');
const reason = ref('');
const submitting = ref(false);
const error = ref<string | null>(null);

async function refresh() {
  loading.value = true;
  try {
    const list = await adminApi.listApiKeys();
    items.value = list.items;
  } finally {
    loading.value = false;
  }
}

function startExtend(k: AdminAPIKeyOut) {
  extending.value = k;
  newExpiry.value = '';
  reason.value = '';
  show.value = true;
}

async function extend() {
  if (!extending.value || !newExpiry.value || !reason.value) return;
  submitting.value = true;
  error.value = null;
  try {
    await adminApi.extendApiKey(
      extending.value.api_key_id,
      new Date(newExpiry.value).toISOString(),
      reason.value,
    );
    show.value = false;
    await refresh();
  } catch (e: any) {
    error.value = e.message;
  } finally {
    submitting.value = false;
  }
}

onMounted(refresh);
</script>

<template>
  <div class="page">
    <AdminTabs />
    <header class="page-head">
      <div>
        <h1>API keys</h1>
        <p class="muted">Read-only view of all API keys. You may extend their expiry; key reveal, regeneration, and deletion are not permitted.</p>
      </div>
    </header>

    <div class="surface-canvas">
      <table>
        <thead>
          <tr><th>Owner</th><th>Name</th><th>Mask</th><th>Applied</th><th>Expires</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="k in items" :key="k.api_key_id">
            <td>{{ k.owner_enterprise_email }}</td>
            <td>{{ k.key_name }}</td>
            <td class="mono">{{ k.api_key_mask }}</td>
            <td>{{ new Date(k.application_date).toLocaleDateString() }}</td>
            <td>{{ new Date(k.expires_at).toLocaleDateString() }}</td>
            <td>
              <span class="badge" :class="{ ok: k.status === 'ENABLED', warn: k.status === 'DISABLED' }">{{ k.status }}</span>
            </td>
            <td class="row-actions">
              <button class="btn ghost sm" @click="startExtend(k)">Extend expiry</button>
            </td>
          </tr>
          <tr v-if="!loading && items.length === 0">
            <td colspan="7" class="empty">No API keys.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :open="show" title="Extend API key expiry" @close="show = false">
      <p v-if="extending" class="muted">
        Extending <span class="mono">{{ extending.api_key_mask }}</span> for <strong>{{ extending.owner_enterprise_email }}</strong>.
        Current expiry: {{ new Date(extending.expires_at).toLocaleString() }}.
      </p>
      <div class="form-row">
        <label>New expiry</label>
        <input v-model="newExpiry" type="datetime-local" />
      </div>
      <div class="form-row">
        <label>Reason (audit log)</label>
        <textarea v-model="reason" />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <template #footer>
        <button class="btn ghost" @click="show = false">Cancel</button>
        <button class="btn primary" :disabled="submitting || !newExpiry || !reason" @click="extend">
          {{ submitting ? 'Extending…' : 'Extend' }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--s-md); }
.page-head { display: flex; justify-content: space-between; align-items: flex-end; }
.row-actions { display: flex; gap: 6px; }
.empty { text-align: center; color: var(--c-muted); padding: var(--s-xl); }
.error { color: var(--c-error); }
</style>
