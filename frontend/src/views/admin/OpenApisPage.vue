<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { OpenAPIOut } from '@/api/generated/types';
import Modal from '@/components/Modal.vue';
import AdminTabs from './components/AdminTabs.vue';
import { adminApi } from './api';

const items = ref<OpenAPIOut[]>([]);
const loading = ref(true);
const show = ref(false);
const editing = ref<OpenAPIOut | null>(null);
const form = ref({ api_name: '', api_type: 'OPENAI_COMPATIBLE', gateway_url: '', usage_description: '' });
const submitting = ref(false);
const error = ref<string | null>(null);

async function refresh() {
  loading.value = true;
  try {
    const list = await adminApi.listOpenApis();
    items.value = list.items;
  } finally {
    loading.value = false;
  }
}

function startCreate() {
  editing.value = null;
  form.value = { api_name: '', api_type: 'OPENAI_COMPATIBLE', gateway_url: '', usage_description: '' };
  show.value = true;
}

function startEdit(o: OpenAPIOut) {
  editing.value = o;
  form.value = {
    api_name: o.api_name,
    api_type: o.api_type,
    gateway_url: o.gateway_url,
    usage_description: o.usage_description ?? '',
  };
  show.value = true;
}

async function save() {
  submitting.value = true;
  error.value = null;
  try {
    const body = { ...form.value, usage_description: form.value.usage_description || null };
    if (editing.value) {
      await adminApi.updateOpenApi(editing.value.openapi_id, body as any);
    } else {
      await adminApi.createOpenApi(body as any);
    }
    show.value = false;
    await refresh();
  } catch (e: any) {
    error.value = e.message;
  } finally {
    submitting.value = false;
  }
}

async function remove(o: OpenAPIOut) {
  if (!confirm(`Delete endpoint "${o.api_name}"?`)) return;
  await adminApi.deleteOpenApi(o.openapi_id);
  await refresh();
}

onMounted(refresh);
</script>

<template>
  <div class="page">
    <AdminTabs />
    <header class="page-head">
      <div>
        <h1>Gateway endpoints</h1>
        <p class="muted">Internal Enterprise OpenAPI endpoints exposed to employees.</p>
      </div>
      <button class="btn primary" @click="startCreate">Add endpoint</button>
    </header>

    <div class="surface-canvas">
      <table>
        <thead>
          <tr><th>Name</th><th>Type</th><th>Gateway URL</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="o in items" :key="o.openapi_id">
            <td>{{ o.api_name }}</td>
            <td>
              <span class="badge" :class="o.api_type === 'OPENAI_COMPATIBLE' ? 'coral' : ''">
                {{ o.api_type === 'OPENAI_COMPATIBLE' ? 'OpenAI' : 'Anthropic' }}
              </span>
            </td>
            <td class="mono">{{ o.gateway_url }}</td>
            <td class="row-actions">
              <button class="btn ghost sm" @click="startEdit(o)">Edit</button>
              <button class="btn ghost sm danger" @click="remove(o)">Delete</button>
            </td>
          </tr>
          <tr v-if="!loading && items.length === 0">
            <td colspan="4" class="empty">No endpoints configured.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :open="show" :title="editing ? 'Edit endpoint' : 'New endpoint'" @close="show = false">
      <div class="form-row">
        <label>API name</label>
        <input v-model="form.api_name" />
      </div>
      <div class="form-row">
        <label>API type</label>
        <select v-model="form.api_type">
          <option value="OPENAI_COMPATIBLE">OpenAI Compatible</option>
          <option value="ANTHROPIC_COMPATIBLE">Anthropic Compatible</option>
        </select>
      </div>
      <div class="form-row">
        <label>Gateway URL (the path employees configure in their tools)</label>
        <input v-model="form.gateway_url" placeholder="https://gateway.company.com/openai/v1/chat/completions" />
      </div>
      <div class="form-row">
        <label>Usage description</label>
        <textarea v-model="form.usage_description" />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <template #footer>
        <button class="btn ghost" @click="show = false">Cancel</button>
        <button class="btn primary" :disabled="submitting" @click="save">
          {{ submitting ? 'Saving…' : (editing ? 'Save changes' : 'Create endpoint') }}
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
