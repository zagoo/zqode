<script setup lang="ts">
defineProps<{ label?: string }>();
</script>

<template>
  <button type="button" :title="label" class="icon-btn">
    <slot />
  </button>
</template>

<style scoped>
.icon-btn {
  display: inline-grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: var(--r-md);
  border: 1px solid transparent;
  background: transparent;
  color: var(--c-ink);
  cursor: pointer;
}
.icon-btn:hover { background: var(--c-surface-soft); }
</style>
