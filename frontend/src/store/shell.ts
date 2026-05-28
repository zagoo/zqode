import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useShellStore = defineStore('shell', () => {
  const navCollapsed = ref(false);
  const panelOpen = ref(false);
  const panelTitle = ref('');

  function toggleNav() {
    navCollapsed.value = !navCollapsed.value;
  }
  function openPanel(title: string) {
    panelTitle.value = title;
    panelOpen.value = true;
  }
  function closePanel() {
    panelOpen.value = false;
  }
  return { navCollapsed, panelOpen, panelTitle, toggleNav, openPanel, closePanel };
});
