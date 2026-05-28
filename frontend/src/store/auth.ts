import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import type { LoginSessionResponse, UserContext } from '@/api/generated/types';

const STORAGE = {
  access: 'zqode_access_token',
  refresh: 'zqode_refresh_token',
};

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string | null>(localStorage.getItem(STORAGE.access));
  const refreshToken = ref<string | null>(localStorage.getItem(STORAGE.refresh));
  const user = ref<UserContext | null>(null);
  const permissions = ref<string[]>([]);

  const isAuthenticated = computed(() => Boolean(accessToken.value && user.value));

  function persist() {
    if (accessToken.value) localStorage.setItem(STORAGE.access, accessToken.value);
    else localStorage.removeItem(STORAGE.access);
    if (refreshToken.value) localStorage.setItem(STORAGE.refresh, refreshToken.value);
    else localStorage.removeItem(STORAGE.refresh);
  }

  function setSession(session: LoginSessionResponse) {
    accessToken.value = session.access_token;
    refreshToken.value = session.refresh_token;
    user.value = session.user;
    permissions.value = session.permissions;
    persist();
  }

  function setAccessToken(token: string) {
    accessToken.value = token;
    persist();
  }

  function clear() {
    accessToken.value = null;
    refreshToken.value = null;
    user.value = null;
    permissions.value = [];
    persist();
  }

  async function fetchMe() {
    const { http } = await import('@/api/http');
    const data = await http.get<LoginSessionResponse>('/api/v1/auth/me');
    user.value = data.user;
    permissions.value = data.permissions;
  }

  function hasPermission(action: string) {
    return permissions.value.includes(action);
  }

  function hasAnyPermission(actions: string[]) {
    return actions.some((a) => permissions.value.includes(a));
  }

  return {
    accessToken,
    refreshToken,
    user,
    permissions,
    isAuthenticated,
    setSession,
    setAccessToken,
    clear,
    fetchMe,
    hasPermission,
    hasAnyPermission,
  };
});
