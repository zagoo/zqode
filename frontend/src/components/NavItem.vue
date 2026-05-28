<script setup lang="ts">
import { computed } from 'vue';
import { useRoute, RouterLink } from 'vue-router';

const props = defineProps<{ to: string; label: string }>();
const route = useRoute();
const active = computed(() => route.path.startsWith(props.to));
</script>

<template>
  <RouterLink :to="to" class="nav-item" :class="{ active }">
    <span class="dot">•</span>
    <span class="label">{{ label }}</span>
  </RouterLink>
</template>

<style scoped>
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  border-radius: var(--r-md);
  color: var(--c-body);
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
}
.nav-item:hover { background: var(--c-surface-soft); color: var(--c-ink); }
.nav-item.active { background: var(--c-surface-card); color: var(--c-ink); }
.dot { color: var(--c-muted-soft); font-size: 18px; line-height: 0; }
</style>
