import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/workbench',
    component: () => import('@/views/workbench/WorkbenchHome.vue'),
    meta: { permissions: ['workbench.api_key.read_own'] },
  },
  {
    path: '/workbench/api-keys',
    component: () => import('@/views/workbench/ApiKeysPage.vue'),
    meta: { permissions: ['workbench.api_key.read_own'] },
  },
  {
    path: '/workbench/models',
    component: () => import('@/views/workbench/ModelsPage.vue'),
    meta: { permissions: ['workbench.model.read'] },
  },
  {
    path: '/workbench/openapis',
    component: () => import('@/views/workbench/OpenApisPage.vue'),
    meta: { permissions: ['workbench.openapi.read'] },
  },
];

export default routes;
