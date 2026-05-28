<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import AppShell from '@/components/AppShell.vue';

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();

onMounted(async () => {
  if (auth.accessToken) {
    try {
      await auth.fetchMe();
    } catch {
      auth.clear();
      router.replace({ path: '/login' });
    }
  }
});

const isLoginRoute = computed(() => route.path.startsWith('/login'));
</script>

<template>
  <router-view v-if="isLoginRoute" />
  <AppShell v-else>
    <router-view />
  </AppShell>
</template>
