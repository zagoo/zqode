<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { ModelOut, ProviderOut } from '@/api/generated/types';
import Modal from '@/components/Modal.vue';
import AdminTabs from './components/AdminTabs.vue';
import { adminApi } from './api';

const items = ref<ModelOut[]>([]);
const providers = ref<ProviderOut[]>([]);
const loading = ref(true);
const show = ref(false);
const editing = ref<ModelOut | null>(null);
const form = ref({
  provider_id: '',
  model_name: '',
  input_price_per_million_tokens: '',
  output_price_per_million_tokens: '',
  currency: 'USD',
});
const submitting = ref(false);
const error = ref<string | null>(null);

async function refresh() {
  loading.value = true;
  try {
    const [p, mlist] = await Promise.all([adminApi.listProviders(), adminApi.listModels()]);
    providers.value = p.items;
    items.value = mlist.items;
  } finally {
    loading.value = false;
  }
}

function startCreate() {
  editing.value = null;
  form.value = {
    provider_id: providers.value[0]?.provider_id ?? '',
    model_name: '',
    input_price_per_million_tokens: '3',
    output_price_per_million_tokens: '15',
    currency: 'USD',
  };
  show.value = true;
}

function startEdit(m: ModelOut) {
  editing.value = m;
  form.value = {
    provider_id: m.provider_id,
    model_name: m.model_name,
    input_price_per_million_tokens: m.input_price_per_million_tokens,
    output_price_per_million_tokens: m.output_price_per_million_tokens,
    currency: m.currency,
  };
  show.value = true;
}

async function save() {
  submitting.value = true;
  error.value = null;
  try {
    if (editing.value) {
      await adminApi.updateModel(editing.value.model_id, {
        model_name: form.value.model_name,
        input_price_per_million_tokens: form.value.input_price_per_million_tokens,
        output_price_per_million_tokens: form.value.output_price_per_million_tokens,
        currency: form.value.currency,
      });
    } else {
      await adminApi.createModel({
        provider_id: form.value.provider_id,
        model_name: form.value.model_name,
        input_price_per_million_tokens: form.value.input_price_per_million_tokens,
        output_price_per_million_tokens: form.value.output_price_per_million_tokens,
        currency: form.value.currency,
      });
    }
    show.value = false;
    await refresh();
  } catch (e: any) {
    error.value = e.message;
  } finally {
    submitting.value = false;
  }
}

async function remove(m: ModelOut) {
  if (!confirm(`Delete model "${m.model_name}"?`)) return;
  await adminApi.deleteModel(m.model_id);
  await refresh();
}

onMounted(refresh);
</script>

<template>
  <div class="page">
    <AdminTabs />
    <header class="page-head">
      <div>
        <h1>Models</h1>
        <p class="muted">Per-million-token pricing drives runtime cost calculation.</p>
      </div>
      <button class="btn primary" :disabled="providers.length === 0" @click="startCreate">Add model</button>
    </header>

    <div class="surface-canvas">
      <table>
        <thead>
          <tr><th>Provider</th><th>Model</th><th>Input $/1M</th><th>Output $/1M</th><th>Currency</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="m in items" :key="m.model_id">
            <td>{{ m.provider_name }}</td>
            <td class="mono">{{ m.model_name }}</td>
            <td>{{ m.input_price_per_million_tokens }}</td>
            <td>{{ m.output_price_per_million_tokens }}</td>
            <td>{{ m.currency }}</td>
            <td class="row-actions">
              <button class="btn ghost sm" @click="startEdit(m)">Edit</button>
              <button class="btn ghost sm danger" @click="remove(m)">Delete</button>
            </td>
          </tr>
          <tr v-if="!loading && items.length === 0">
            <td colspan="6" class="empty">No models configured.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :open="show" :title="editing ? 'Edit model' : 'New model'" @close="show = false">
      <div class="form-row" v-if="!editing">
        <label>Provider</label>
        <select v-model="form.provider_id">
          <option v-for="p in providers" :key="p.provider_id" :value="p.provider_id">{{ p.provider_name }}</option>
        </select>
      </div>
      <div class="form-row">
        <label>Model name</label>
        <input v-model="form.model_name" placeholder="gpt-4o, claude-opus-4-7, …" />
      </div>
      <div class="row-grid">
        <div class="form-row">
          <label>Input $/1M</label>
          <input v-model="form.input_price_per_million_tokens" />
        </div>
        <div class="form-row">
          <label>Output $/1M</label>
          <input v-model="form.output_price_per_million_tokens" />
        </div>
      </div>
      <div class="form-row">
        <label>Currency</label>
        <input v-model="form.currency" maxlength="3" />
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <template #footer>
        <button class="btn ghost" @click="show = false">Cancel</button>
        <button class="btn primary" :disabled="submitting" @click="save">
          {{ submitting ? 'Saving…' : (editing ? 'Save changes' : 'Create model') }}
        </button>
      </template>
    </Modal>
  </div>
</template>

<style scoped>
.page { display: flex; flex-direction: column; gap: var(--s-md); }
.page-head { display: flex; justify-content: space-between; align-items: flex-end; }
.row-actions { display: flex; gap: 6px; }
.row-grid { display: grid; grid-template-columns: 1fr 1fr; gap: var(--s-md); }
.empty { text-align: center; color: var(--c-muted); padding: var(--s-xl); }
.error { color: var(--c-error); }
</style>
