<script setup lang="ts">
defineProps<{ title?: string; description?: string; tone?: 'cream' | 'canvas' | 'dark' }>();
</script>

<template>
  <article class="content-card" :data-tone="tone || 'cream'">
    <header v-if="title || $slots.header" class="head">
      <slot name="header">
        <h3>{{ title }}</h3>
        <p v-if="description" class="muted">{{ description }}</p>
      </slot>
    </header>
    <div class="body"><slot /></div>
    <footer v-if="$slots.footer" class="foot"><slot name="footer" /></footer>
  </article>
</template>

<style scoped>
.content-card {
  border-radius: var(--r-lg);
  padding: var(--s-xl);
  display: flex;
  flex-direction: column;
  gap: var(--s-md);
}
.content-card[data-tone='cream'] { background: var(--c-surface-card); color: var(--c-ink); }
.content-card[data-tone='canvas'] { background: var(--c-canvas); border: 1px solid var(--c-hairline); color: var(--c-ink); }
.content-card[data-tone='dark'] { background: var(--c-surface-dark); color: var(--c-on-dark); }
.head { display: flex; flex-direction: column; gap: 6px; }
.foot { margin-top: var(--s-sm); display: flex; gap: var(--s-sm); }
</style>
