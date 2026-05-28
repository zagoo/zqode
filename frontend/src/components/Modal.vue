<script setup lang="ts">
defineProps<{ open: boolean; title?: string }>();
defineEmits<{ (e: 'close'): void }>();
</script>

<template>
  <Transition name="fade">
    <div v-if="open" class="backdrop" @click.self="$emit('close')">
      <div class="modal">
        <header v-if="title || $slots.header">
          <slot name="header"><h3>{{ title }}</h3></slot>
          <button class="btn ghost sm" @click="$emit('close')">×</button>
        </header>
        <div class="body"><slot /></div>
        <footer v-if="$slots.footer"><slot name="footer" /></footer>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.backdrop {
  position: fixed;
  inset: 0;
  background: rgba(20,20,19,0.4);
  display: grid;
  place-items: center;
  z-index: 50;
}
.modal {
  width: min(560px, 92vw);
  background: var(--c-canvas);
  border-radius: var(--r-lg);
  border: 1px solid var(--c-hairline);
  display: flex;
  flex-direction: column;
  max-height: 80vh;
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--s-md) var(--s-lg);
  border-bottom: 1px solid var(--c-hairline-soft);
}
.body {
  padding: var(--s-lg);
  overflow: auto;
}
footer {
  padding: var(--s-md) var(--s-lg);
  border-top: 1px solid var(--c-hairline-soft);
  display: flex;
  justify-content: flex-end;
  gap: var(--s-sm);
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.15s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
