import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/analytics',
    redirect: '/analytics/personal',
  },
  {
    path: '/analytics/personal',
    component: () => import('@/views/analytics/PersonalConsumptionPage.vue'),
    meta: { permissions: ['analytics.personal.read'] },
  },
  {
    path: '/analytics/ranking',
    component: () => import('@/views/analytics/RankingPage.vue'),
    meta: { permissions: ['analytics.ranking.read'] },
  },
  {
    path: '/analytics/details',
    component: () => import('@/views/analytics/DetailsPage.vue'),
    meta: { permissions: ['analytics.detail.read'] },
  },
  {
    path: '/analytics/summary',
    component: () => import('@/views/analytics/SummaryPage.vue'),
    meta: { permissions: ['analytics.summary.read'] },
  },
];

export default routes;
