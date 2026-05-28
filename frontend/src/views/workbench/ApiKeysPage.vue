<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { APIKeyOut, APIKeyCreateResponse } from '@/api/generated/types';
import Modal from '@/components/Modal.vue';
import { workbenchApi } from './api';

const keys = ref<APIKeyOut[]>([]);
const loading = ref(false);
const error = ref<string | null>(null);

const showCreate = ref(false);
const newName = ref('');
const newExpiry = ref('');
const creating = ref(false);

const showSecret = ref<APIKeyCreateResponse | null>(null);

async function refresh() {
  loading.value = true;
  try {
    const page = await workbenchApi.listKeys();
    keys.value = page.items;
  } catch (e: any) {
    error.value = e.message;
  } finally {
    loading.value = false;
  }
}

async function create() {
  if (!newName.value || !newExpiry.value) return;
  creating.value = true;
  error.value = null;
  try {
    const isoExpiry = new Date(newExpiry.value).toISOString();
    const res = await workbenchApi.createKey(newName.value, isoExpiry);
    showCreate.value = false;
    showSecret.value = res;
    newName.value = '';
    newExpiry.value = '';
    await refresh();
  } catch (e: any) {
    error.value = e.message;
  } finally {
    creating.value = false;
  }
}

async function toggleStatus(k: APIKeyOut) {
  await workbenchApi.setStatus(k.api_key_id, k.status === 'ENABLED' ? 'DISABLED' : 'ENABLED');
  await refresh();
}

async function deleteKey(k: APIKeyOut) {
  if (!confirm(`Delete API key "${k.key_name}"? This cannot be undone.`)) return;
  await workbenchApi.deleteKey(k.api_key_id);
  await refresh();
}

function copy(text: string) {
  navigator.clipboard.writeText(text).catch(() => {});
}

onMounted(refresh);
</script>

<template>
  <div class="page">
    <header class="page-head">
      <div>
        <h1>API Keys</h1>
        <p class="muted">Create and manage credentials your IDE, plugin, or CLI tool uses to call the gateway.</p>
      </div>
      <button class="btn primary" @click="showCreate = true">New API key</button>
    </header>

    <div v-if="error" class="error">{{ error }}</div>

    <div class="surface-canvas table-wrap">
      <table>
        <thead>
          <tr>
            <th>Name</th>
            <th>Mask</th>
            <th>Created</th>
            <th>Expires</th>
            <th>Status</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="k in keys" :key="k.api_key_id">
            <td>{{ k.key_name }}</td>
            <td class="mono">{{ k.api_key_mask }}</td>
            <td>{{ new Date(k.application_date).toLocaleDateString() }}</td>
            <td>{{ new Date(k.expires_at).toLocaleDateString() }}</td>
            <td>
              <span class="badge" :class="{ ok: k.status === 'ENABLED', warn: k.status === 'DISABLED' }">
                {{ k.status }}
              </span>
            </td>
            <td class="row-actions">
              <button class="btn ghost sm" @click="toggleStatus(k)">
                {{ k.status === 'ENABLED' ? 'Disable' : 'Enable' }}
              </button>
              <button class="btn ghost sm danger" @click="deleteKey(k)">Delete</button>
            </td>
          </tr>
          <tr v-if="!loading && keys.length === 0">
            <td colspan="6" class="empty">No API keys yet. Create one to get started.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :open="showCreate" title="Create API key" @close="showCreate = false">
      <div class="form-row">
        <label for="name">Key name</label>
        <input id="name" v-model="newName" placeholder="e.g. VS Code Key" />
      </div>
      <div class="form-row">
        <label for="exp">Expires at</label>
        <input id="exp" v-model="newExpiry" type="date" />
        <small class="muted">Cannot exceed your role's validity policy.</small>
      </div>
      <template #footer>
        <button class="btn ghost" @click="showCreate = false">Cancel</button>
        <button class="btn primary" :disabled="!newName || !newExpiry || creating" @click="create">
          {{ creating ? 'Creating…' : 'Create key' }}
        </button>
      </template>
    </Modal>

    <Modal :open="!!showSecret" title="API key created" @close="showSecret = null">
      <p>Copy this secret now. It will only be shown once.</p>
      <pre class="secret mono">{{ showSecret?.api_key_secret }}</pre>
      <button v-if="showSecret?.api_key_secret" class="btn" @click="copy(showSecret!.api_key_secret!)">
        Copy to clipboard
      </button>
      <template #footer>
        <button class="btn primary" @click="showSecret = null">I have saved it</button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--s-lg); }
.page-head { display: flex; align-items: flex-end; justify-content: space-between; }
.table-wrap { padding: 0; overflow: hidden; }
.row-actions { display: flex; gap: 6px; }
.empty { text-align: center; color: var(--c-muted); padding: var(--s-xl); }
.secret {
  background: var(--c-surface-dark);
  color: var(--c-on-dark);
  padding: var(--s-md);
  border-radius: var(--r-md);
  overflow-x: auto;
  font-size: 13px;
}
.error { color: var(--c-error); }
</style>
