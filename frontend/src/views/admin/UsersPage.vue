<script setup lang="ts">
import { onMounted, ref } from 'vue';
import type { RoleOut, UserOut } from '@/api/generated/types';
import Modal from '@/components/Modal.vue';
import AdminTabs from './components/AdminTabs.vue';
import { adminApi } from './api';

const items = ref<UserOut[]>([]);
const roles = ref<RoleOut[]>([]);
const loading = ref(true);
const show = ref(false);
const editing = ref<UserOut | null>(null);
const form = ref({
  enterprise_email: '',
  role_id: '',
  cost_limit_source: 'ROLE_DEFAULT',
  custom_cost_limit_amount: '',
  account_status: 'ENABLED',
});
const submitting = ref(false);
const error = ref<string | null>(null);

async function refresh() {
  loading.value = true;
  try {
    const [u, r] = await Promise.all([adminApi.listUsers(), adminApi.listRoles()]);
    items.value = u.items;
    roles.value = r.items;
  } finally {
    loading.value = false;
  }
}

function startCreate() {
  editing.value = null;
  form.value = {
    enterprise_email: '',
    role_id: roles.value[0]?.role_id ?? '',
    cost_limit_source: 'ROLE_DEFAULT',
    custom_cost_limit_amount: '',
    account_status: 'ENABLED',
  };
  show.value = true;
}

function startEdit(u: UserOut) {
  editing.value = u;
  form.value = {
    enterprise_email: u.enterprise_email,
    role_id: u.role_id,
    cost_limit_source: u.cost_limit_source,
    custom_cost_limit_amount: u.cost_limit_source === 'USER_CUSTOM' ? u.cost_limit_amount : '',
    account_status: u.account_status,
  };
  show.value = true;
}

async function save() {
  submitting.value = true;
  error.value = null;
  try {
    if (editing.value) {
      await adminApi.updateUser(editing.value.user_id, {
        role_id: form.value.role_id,
        cost_limit_source: form.value.cost_limit_source,
        custom_cost_limit_amount: form.value.cost_limit_source === 'USER_CUSTOM' ? form.value.custom_cost_limit_amount : undefined,
        account_status: form.value.account_status,
      });
    } else {
      await adminApi.createUser({
        enterprise_email: form.value.enterprise_email,
        role_id: form.value.role_id,
        cost_limit_source: form.value.cost_limit_source,
        custom_cost_limit_amount: form.value.cost_limit_source === 'USER_CUSTOM' ? form.value.custom_cost_limit_amount : null,
        account_status: form.value.account_status,
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

async function remove(u: UserOut) {
  if (!confirm(`Disable and delete "${u.enterprise_email}"?`)) return;
  await adminApi.deleteUser(u.user_id);
  await refresh();
}

onMounted(refresh);
</script>

<template>
  <div class="page">
    <AdminTabs />
    <header class="page-head">
      <div>
        <h1>Users</h1>
        <p class="muted">Provision enterprise accounts, set roles, override cost limits.</p>
      </div>
      <button class="btn primary" :disabled="roles.length === 0" @click="startCreate">Add user</button>
    </header>

    <div class="surface-canvas">
      <table>
        <thead>
          <tr><th>Email</th><th>Role</th><th>Cost limit</th><th>Status</th><th></th></tr>
        </thead>
        <tbody>
          <tr v-for="u in items" :key="u.user_id">
            <td>{{ u.enterprise_email }}</td>
            <td>{{ u.role_name }}</td>
            <td>{{ u.cost_limit_amount }} <span class="muted">({{ u.cost_limit_source }})</span></td>
            <td>
              <span class="badge" :class="{ ok: u.account_status === 'ENABLED', err: u.account_status === 'DISABLED' }">
                {{ u.account_status }}
              </span>
            </td>
            <td class="row-actions">
              <button class="btn ghost sm" @click="startEdit(u)">Edit</button>
              <button class="btn ghost sm danger" @click="remove(u)">Delete</button>
            </td>
          </tr>
          <tr v-if="!loading && items.length === 0">
            <td colspan="5" class="empty">No users yet.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <Modal :open="show" :title="editing ? 'Edit user' : 'New user'" @close="show = false">
      <div class="form-row" v-if="!editing">
        <label>Enterprise email</label>
        <input v-model="form.enterprise_email" type="email" placeholder="name@company.com" />
      </div>
      <div class="form-row">
        <label>Role</label>
        <select v-model="form.role_id">
          <option v-for="r in roles" :key="r.role_id" :value="r.role_id">{{ r.role_name }}</option>
        </select>
      </div>
      <div class="form-row">
        <label>Cost limit source</label>
        <select v-model="form.cost_limit_source">
          <option value="ROLE_DEFAULT">Use role default</option>
          <option value="USER_CUSTOM">Custom for this user</option>
        </select>
      </div>
      <div class="form-row" v-if="form.cost_limit_source === 'USER_CUSTOM'">
        <label>Custom cost limit</label>
        <input v-model="form.custom_cost_limit_amount" placeholder="e.g. 200.00" />
      </div>
      <div class="form-row">
        <label>Status</label>
        <select v-model="form.account_status">
          <option value="ENABLED">Enabled</option>
          <option value="DISABLED">Disabled</option>
        </select>
        <small v-if="form.account_status === 'DISABLED'" class="muted">
          This user will no longer be able to log in or use existing API Keys.
        </small>
      </div>
      <p v-if="error" class="error">{{ error }}</p>
      <template #footer>
        <button class="btn ghost" @click="show = false">Cancel</button>
        <button class="btn primary" :disabled="submitting" @click="save">
          {{ submitting ? 'Saving…' : (editing ? 'Save changes' : 'Create user') }}
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
