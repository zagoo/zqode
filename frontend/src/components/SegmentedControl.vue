<script setup lang="ts" generic="T extends string">
defineProps<{ modelValue: T; options: { value: T; label: string }[] }>();
defineEmits<{ (e: 'update:modelValue', v: T): void }>();
</script>

<template>
  <div class="seg">
    <button
      v-for="opt in options"
      :key="opt.value"
      type="button"
      :class="{ active: modelValue === opt.value }"
      @click="$emit('update:modelValue', opt.value)"
    >
      {{ opt.label }}
    </button>
  </div>
</template>

<style scoped>
.seg {
  display: inline-flex;
  padding: 3px;
  background: var(--c-surface-soft);
  border-radius: var(--r-pill);
}
button {
  border: 0;
  background: transparent;
  color: var(--c-muted);
  padding: 6px 14px;
  border-radius: var(--r-pill);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
}
button.active { background: var(--c-canvas); color: var(--c-ink); }
</style>
