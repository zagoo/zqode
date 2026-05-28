<script setup lang="ts">
import { computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import { useShellStore } from '@/store/shell';
import NavItem from '@/components/NavItem.vue';
import ToolbarIconButton from '@/components/ToolbarIconButton.vue';

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();
const shell = useShellStore();

type NavEntry = { label: string; to: string; permissions?: string[] };

const primaryNav = computed<NavEntry[]>(() => [
  { label: 'Workbench', to: '/workbench', permissions: ['workbench.api_key.read_own'] },
  { label: 'Analytics', to: '/analytics', permissions: ['analytics.personal.read'] },
  { label: 'Admin', to: '/admin', permissions: ['platform.user.read'] },
]);

const visibleNav = computed(() =>
  primaryNav.value.filter((n) => !n.permissions || auth.hasAnyPermission(n.permissions))
);

async function logout() {
  try {
    const { http } = await import('@/api/http');
    await http.post('/api/v1/auth/logout');
  } catch {
    /* ignore */
  }
  auth.clear();
  router.replace('/login');
}

const pageTitle = computed(() => {
  const path = route.path;
  if (path.startsWith('/workbench')) return 'Workbench';
  if (path.startsWith('/analytics')) return 'Analytics';
  if (path.startsWith('/admin')) return 'Administration';
  return '';
});
</script>

<template>
  <div class="shell" :class="{ collapsed: shell.navCollapsed }">
    <aside class="nav">
      <div class="nav-header">
        <span class="brand-mark">✻</span>
        <span class="brand">ZQode Gateway</span>
      </div>
      <nav class="nav-primary">
        <NavItem
          v-for="item in visibleNav"
          :key="item.to"
          :to="item.to"
          :label="item.label"
        />
      </nav>
      <div class="spacer" />
      <div class="nav-footer">
        <div class="identity">
          <div class="avatar">{{ auth.user?.enterprise_email?.[0]?.toUpperCase() ?? '?' }}</div>
          <div class="identity-text">
            <div class="email">{{ auth.user?.enterprise_email }}</div>
            <div class="role muted">{{ auth.user?.role_name }}</div>
          </div>
        </div>
        <button class="btn ghost sm" @click="logout">Sign out</button>
      </div>
    </aside>

    <main class="content">
      <header class="toolbar">
        <div class="toolbar-left">
          <ToolbarIconButton :label="shell.navCollapsed ? 'Expand' : 'Collapse'" @click="shell.toggleNav()">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
              <path d="M4 6h16M4 12h16M4 18h16" stroke-linecap="round" />
            </svg>
          </ToolbarIconButton>
          <h2 class="title">{{ pageTitle }}</h2>
        </div>
        <div class="toolbar-right">
          <slot name="content-toolbar" />
        </div>
      </header>
      <section class="content-body">
        <slot />
      </section>
    </main>
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: var(--shell-nav-w) 1fr;
  height: 100vh;
  background: var(--c-canvas);
}
.shell.collapsed {
  grid-template-columns: 64px 1fr;
}
.nav {
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--c-hairline);
  padding: var(--s-md) var(--s-sm);
  gap: var(--s-md);
  background: var(--c-canvas);
  overflow: hidden;
}
.nav-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 12px;
}
.brand-mark {
  color: var(--c-ink);
  font-size: 20px;
  line-height: 1;
}
.brand {
  font-family: var(--f-display);
  font-size: 18px;
  letter-spacing: -0.3px;
  color: var(--c-ink);
  white-space: nowrap;
}
.shell.collapsed .brand { display: none; }
.nav-primary {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.spacer { flex: 1; }
.nav-footer {
  display: flex;
  flex-direction: column;
  gap: var(--s-sm);
  border-top: 1px solid var(--c-hairline-soft);
  padding: var(--s-sm) 8px;
}
.identity {
  display: flex;
  align-items: center;
  gap: 10px;
}
.avatar {
  width: 32px;
  height: 32px;
  border-radius: var(--r-pill);
  background: var(--c-surface-card);
  color: var(--c-ink);
  display: grid;
  place-items: center;
  font-weight: 500;
  font-size: 13px;
}
.identity-text { min-width: 0; }
.email {
  font-size: 13px;
  color: var(--c-ink);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 170px;
}
.role { font-size: 12px; }
.shell.collapsed .identity-text { display: none; }

.content {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}
.toolbar {
  height: var(--shell-toolbar-h);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 var(--s-lg);
  border-bottom: 1px solid var(--c-hairline);
  flex-shrink: 0;
  background: var(--c-canvas);
}
.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--s-sm);
}
.title {
  font-family: var(--f-body);
  font-size: 16px;
  font-weight: 500;
  color: var(--c-ink);
}
.content-body {
  flex: 1;
  overflow: auto;
  padding: var(--s-xl);
  background: var(--c-canvas);
}
</style>
