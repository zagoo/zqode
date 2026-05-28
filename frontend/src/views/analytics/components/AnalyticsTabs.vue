<script setup lang="ts">
import { computed } from 'vue';
import { RouterLink, useRoute } from 'vue-router';
import { useAuthStore } from '@/store/auth';

const route = useRoute();
const auth = useAuthStore();

const tabs = [
  { to: '/analytics/personal', label: 'Personal', permission: 'analytics.personal.read' },
  { to: '/analytics/ranking', label: 'Ranking', permission: 'analytics.ranking.read' },
  { to: '/analytics/details', label: 'Details', permission: 'analytics.detail.read' },
  { to: '/analytics/summary', label: 'Summary', permission: 'analytics.summary.read' },
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
.tabs { display: flex; gap: 4px; margin-bottom: var(--s-lg); }
.tab { padding: 8px 14px; border-radius: var(--r-md); color: var(--c-muted); text-decoration: none; font-size: 14px; font-weight: 500; }
.tab:hover { background: var(--c-surface-soft); color: var(--c-ink); }
.tab.active { background: var(--c-surface-card); color: var(--c-ink); }
</style>
