<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, RouterLink } from 'vue-router';
import { useAuthStore } from '@/store/auth';

const route = useRoute();
const auth = useAuthStore();

type Tab = { to: string; label: string; permission: string };
const tabs: Tab[] = [
  { to: '/admin/providers', label: 'Providers', permission: 'platform.provider.read' },
  { to: '/admin/models', label: 'Models', permission: 'platform.model.read' },
  { to: '/admin/openapis', label: 'Gateway endpoints', permission: 'platform.openapi.read' },
  { to: '/admin/users', label: 'Users', permission: 'platform.user.read' },
  { to: '/admin/roles', label: 'Roles', permission: 'platform.role.read' },
  { to: '/admin/api-keys', label: 'API keys', permission: 'platform.api_key.read_all' },
  { to: '/admin/quota-policy', label: 'Quota policy', permission: 'platform.quota_policy.read' },
];
const visible = computed(() => tabs.filter((t) => auth.hasPermission(t.permission)));
</script>

<template>
  <nav class="tabs">
    <RouterLink
      v-for="t in visible"
      :key="t.to"
      :to="t.to"
      :class="['tab', { active: route.path.startsWith(t.to) }]"
    >
      {{ t.label }}
    </RouterLink>
  </nav>
</template>

<style scoped>
.tabs { display: flex; gap: 4px; flex-wrap: wrap; margin-bottom: var(--s-lg); }
.tab {
  padding: 8px 14px;
  border-radius: var(--r-md);
  color: var(--c-muted);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
}
.tab:hover { background: var(--c-surface-soft); color: var(--c-ink); }
.tab.active { background: var(--c-surface-card); color: var(--c-ink); }
</style>
