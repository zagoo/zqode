<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import type { RoleOut } from '@/api/generated/types';
import Modal from '@/components/Modal.vue';
import AdminTabs from './components/AdminTabs.vue';
import { adminApi } from './api';

const roles = ref<RoleOut[]>([]);
const allPermissions = ref<string[]>([]);
const loading = ref(true);
const show = ref(false);
const editing = ref<RoleOut | null>(null);
const form = ref({
  role_name: '',
  default_cost_limit_amount: '100',
  api_key_validity_days: 90,
  permissions: [] as string[],
});
const submitting = ref(false);
const error = ref<string | null>(null);

const grouped = computed(() => {
  const groups: Record<string, string[]> = {};
  for (const p of allPermissions.value) {
    const ns = p.split('.')[0];
    (groups[ns] ||= []).push(p);
  }
  return groups;
});

async function refresh() {
  loading.value = true;
  try {
    const [list, perms] = await Promise.all([adminApi.listRoles(), adminApi.listPermissionActions()]);
    roles.value = list.items;
    allPermissions.value = perms;
  } finally {
    loading.value = false;
  }
}

function startCreate() {
  editing.value = null;
  form.value = { role_name: '', default_cost_limit_amount: '100', api_key_validity_days: 90, permissions: [] };
  show.value = true;
}

function startEdit(r: RoleOut) {
  editing.value = r;
  form.value = {
    role_name: r.role_name,
    default_cost_limit_amount: r.default_cost_limit_amount,
    api_key_validity_days: r.api_key_validity_days,
    permissions: [...r.permissions],
  };
  show.value = true;
}

async function save() {
  submitting.value = true;
  error.value = null;
  try {
    if (editing.value) {
      await adminApi.updateRole(editing.value.role_id, {
        role_name: form.value.role_name,
        default_cost_limit_amount: form.value.default_cost_limit_amount,
        api_key_validity_days: form.value.api_key_validity_days,
        permissions: form.value.permissions,
      });
    } else {
      await adminApi.createRole({
        role_name: form.value.role_name,
        default_cost_limit_amount: form.value.default_cost_limit_amount,
        api_key_validity_days: form.value.api_key_validity_days,
        permissions: form.value.permissions,
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

async function remove(r: RoleOut) {
  if (!confirm(`Delete role "${r.role_name}"?`)) return;
  try {
    await adminApi.deleteRole(r.role_id);
    await refresh();
  } catch (e: any) {
    alert(e.message);
  }
}

onMounted(refresh);
</script>

<template>
  <div class="page">
    <AdminTabs />
    <header class="page-head">
      <div>
        <h1>Roles</h1>
        <p class="muted">Bundle permissions, default cost limits, and API key validity policies.</p>
      </div>
      <button class="btn primary" @click="startCreate">Add role</button>
    </header>

    <div class="surface-canvas">
      <table>
        <thead>
          <tr><th>Role</th><th>Permissions</th><th>Default limit</th><th>Validity (days)</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="r in roles" :key="r.role_id">
            <td>{{ r.role_name }}</td>
            <td class="muted">{{ r.permissions.length }} actions</td>
            <td>{{ r.default_cost_limit_amount }}</td>
            <td>{{ r.api_key_validity_days }}</td>
            <td class="row-actions">
              <button class="btn ghost sm" @click="startEdit(r)">Edit</button>
              <button class="btn ghost sm danger" @click="remove(r)">Delete</button>
            </td>
          </tr>
          <tr v-if="!loading && roles.length === 0">
            <td colspan="5" class="empty">No roles yet.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :open="show" :title="editing ? 'Edit role' : 'New role'" @close="show = false">
      <div class="form-row">
        <label>Role name</label>
        <input v-model="form.role_name" />
      </div>
      <div class="row-grid">
        <div class="form-row">
          <label>Default cost limit</label>
          <input v-model="form.default_cost_limit_amount" />
        </div>
        <div class="form-row">
          <label>API key validity (days)</label>
          <input v-model.number="form.api_key_validity_days" type="number" min="1" />
        </div>
      </div>
      <div class="permissions">
        <label class="perm-label">Permissions</label>
        <div v-for="(perms, ns) in grouped" :key="ns" class="perm-group">
          <div class="perm-ns">{{ ns }}</div>
          <label v-for="p in perms" :key="p" class="perm">
            <input type="checkbox" :value="p" v-model="form.permissions" />
            <span class="mono">{{ p }}</span>
          </label>
        </div>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <template #footer>
        <button class="btn ghost" @click="show = false">Cancel</button>
        <button class="btn primary" :disabled="submitting" @click="save">
          {{ submitting ? 'Saving…' : (editing ? 'Save changes' : 'Create role') }}
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
.permissions { display: flex; flex-direction: column; gap: var(--s-sm); margin-top: var(--s-md); }
.perm-label { font-size: 13px; color: var(--c-muted); }
.perm-group { background: var(--c-surface-soft); border-radius: var(--r-md); padding: 12px; display: flex; flex-wrap: wrap; gap: 6px 16px; }
.perm-ns { width: 100%; font-size: 11px; color: var(--c-muted); text-transform: uppercase; letter-spacing: 0.06em; }
.perm { display: flex; align-items: center; gap: 6px; font-size: 13px; cursor: pointer; }
</style>
