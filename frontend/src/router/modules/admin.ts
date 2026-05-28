import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/admin',
    redirect: '/admin/providers',
  },
  {
    path: '/admin/providers',
    component: () => import('@/views/admin/ProvidersPage.vue'),
    meta: { permissions: ['platform.provider.read'] },
  },
  {
    path: '/admin/models',
    component: () => import('@/views/admin/ModelsPage.vue'),
    meta: { permissions: ['platform.model.read'] },
  },
  {
    path: '/admin/openapis',
    component: () => import('@/views/admin/OpenApisPage.vue'),
    meta: { permissions: ['platform.openapi.read'] },
  },
  {
    path: '/admin/users',
    component: () => import('@/views/admin/UsersPage.vue'),
    meta: { permissions: ['platform.user.read'] },
  },
  {
    path: '/admin/roles',
    component: () => import('@/views/admin/RolesPage.vue'),
    meta: { permissions: ['platform.role.read'] },
  },
  {
    path: '/admin/api-keys',
    component: () => import('@/views/admin/ApiKeysPage.vue'),
    meta: { permissions: ['platform.api_key.read_all'] },
  },
  {
    path: '/admin/quota-policy',
    component: () => import('@/views/admin/QuotaPolicyPage.vue'),
    meta: { permissions: ['platform.quota_policy.read'] },
  },
];

export default routes;
