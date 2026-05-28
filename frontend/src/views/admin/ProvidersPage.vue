<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { ProviderOut } from '@/api/generated/types';
import Modal from '@/components/Modal.vue';
import AdminTabs from './components/AdminTabs.vue';
import { adminApi } from './api';

const items = ref<ProviderOut[]>([]);
const loading = ref(true);
const showCreate = ref(false);
const editing = ref<ProviderOut | null>(null);
const form = ref({ provider_name: '', api_base_url: '', api_key: '', api_description: '' });
const submitting = ref(false);
const error = ref<string | null>(null);

function reset() {
  form.value = { provider_name: '', api_base_url: '', api_key: '', api_description: '' };
}

async function refresh() {
  loading.value = true;
  try {
    const p = await adminApi.listProviders();
    items.value = p.items;
  } finally {
    loading.value = false;
  }
}

function startCreate() {
  reset();
  editing.value = null;
  showCreate.value = true;
}

function startEdit(p: ProviderOut) {
  editing.value = p;
  form.value = { provider_name: p.provider_name, api_base_url: p.api_base_url, api_key: '', api_description: p.api_description ?? '' };
  showCreate.value = true;
}

async function save() {
  submitting.value = true;
  error.value = null;
  try {
    if (editing.value) {
      const body: any = {
        provider_name: form.value.provider_name,
        api_base_url: form.value.api_base_url,
        api_description: form.value.api_description,
      };
      if (form.value.api_key) body.api_key = form.value.api_key;
      await adminApi.updateProvider(editing.value.provider_id, body);
    } else {
      await adminApi.createProvider({
        provider_name: form.value.provider_name,
        api_base_url: form.value.api_base_url,
        api_key: form.value.api_key,
        api_description: form.value.api_description || null,
      });
    }
    showCreate.value = false;
    await refresh();
  } catch (e: any) {
    error.value = e.message;
  } finally {
    submitting.value = false;
  }
}

async function remove(p: ProviderOut) {
  if (!confirm(`Delete provider "${p.provider_name}"?`)) return;
  await adminApi.deleteProvider(p.provider_id);
  await refresh();
}

onMounted(refresh);
</script>

<template>
  <div class="page">
    <AdminTabs />
    <header class="page-head">
      <div>
        <h1>Providers</h1>
        <p class="muted">External LLM API providers whose credentials the gateway holds centrally.</p>
      </div>
      <button class="btn primary" @click="startCreate">Add provider</button>
    </header>

    <div class="surface-canvas">
      <table>
        <thead>
          <tr><th>Name</th><th>Base URL</th><th>Key mask</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="p in items" :key="p.provider_id">
            <td>{{ p.provider_name }}</td>
            <td class="mono">{{ p.api_base_url }}</td>
            <td class="mono">{{ p.api_key_mask }}</td>
            <td><span class="badge ok">{{ p.status }}</span></td>
            <td class="row-actions">
              <button class="btn ghost sm" @click="startEdit(p)">Edit</button>
              <button class="btn ghost sm danger" @click="remove(p)">Delete</button>
            </td>
          </tr>
          <tr v-if="!loading && items.length === 0">
            <td colspan="5" class="empty">No providers configured. Add one to enable the gateway.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :open="showCreate" :title="editing ? 'Edit provider' : 'New provider'" @close="showCreate = false">
      <div class="form-row">
        <label>Provider name</label>
        <input v-model="form.provider_name" placeholder="OpenAI, Anthropic, …" />
      </div>
      <div class="form-row">
        <label>API base URL</label>
        <input v-model="form.api_base_url" placeholder="https://api.openai.com or mock://local" />
        <small class="muted">Use <span class="mono">mock://local</span> in dev for synthetic provider responses.</small>
      </div>
      <div class="form-row">
        <label>API key {{ editing ? '(leave blank to keep current)' : '' }}</label>
        <input v-model="form.api_key" type="password" :placeholder="editing ? '••••••••' : 'sk-…'" />
      </div>
      <div class="form-row">
        <label>Description</label>
        <textarea v-model="form.api_description" />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <template #footer>
        <button class="btn ghost" @click="showCreate = false">Cancel</button>
        <button class="btn primary" :disabled="submitting" @click="save">
          {{ submitting ? 'Saving…' : (editing ? 'Save changes' : 'Create provider') }}
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
