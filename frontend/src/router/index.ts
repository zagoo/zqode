import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router';
import { useAuthStore } from '@/store/auth';

const moduleRoutes = import.meta.glob<{ default: RouteRecordRaw[] }>('./modules/*.ts', { eager: true });

const routes: RouteRecordRaw[] = [];
for (const mod of Object.values(moduleRoutes)) {
  routes.push(...mod.default);
}

routes.push({ path: '/', redirect: '/workbench' });
routes.push({ path: '/:pathMatch(.*)*', redirect: '/workbench' });

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to) => {
  const auth = useAuthStore();
  if (to.meta.public) return true;
  if (!auth.accessToken) {
    return { path: '/login', query: { next: to.fullPath } };
  }
  if (!auth.user) {
    try {
      await auth.fetchMe();
    } catch {
      auth.clear();
      return { path: '/login', query: { next: to.fullPath } };
    }
  }
  const required = (to.meta.permissions as string[] | undefined) ?? [];
  if (required.length && !required.every((p) => auth.hasPermission(p))) {
    return { path: '/workbench' };
  }
  return true;
});

export default router;
