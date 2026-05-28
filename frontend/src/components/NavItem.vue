<script setup lang="ts">
import { computed } from "vue";
import { useRoute, RouterLink } from "vue-router";

const props = defineProps<{
    to: string;
    label: string;
    icon?: "workbench" | "analytics" | "admin";
}>();
const route = useRoute();
const active = computed(() => route.path.startsWith(props.to));
</script>

<template>
    <RouterLink :to="to" class="nav-item" :class="{ active }">
        <span class="icon" aria-hidden="true">
            <!-- Workbench: 2x2 layout grid (developer workspace) -->
            <svg
                v-if="icon === 'workbench'"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"
                stroke-linejoin="round"
            >
                <rect x="3" y="3" width="7" height="7" rx="1.5" />
                <rect x="14" y="3" width="7" height="7" rx="1.5" />
                <rect x="3" y="14" width="7" height="7" rx="1.5" />
                <rect x="14" y="14" width="7" height="7" rx="1.5" />
            </svg>
            <!-- Analytics: bar chart -->
            <svg
                v-else-if="icon === 'analytics'"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"
                stroke-linejoin="round"
            >
                <path d="M3 21h18" />
                <rect x="5" y="11" width="3.5" height="7" rx="1" />
                <rect x="10.25" y="6" width="3.5" height="12" rx="1" />
                <rect x="15.5" y="14" width="3.5" height="4" rx="1" />
            </svg>
            <!-- Admin: shield (platform governance) -->
            <svg
                v-else-if="icon === 'admin'"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="1.6"
                stroke-linecap="round"
                stroke-linejoin="round"
            >
                <path d="M12 3l7 3v5c0 4.5-3 7.6-7 9-4-1.4-7-4.5-7-9V6l7-3z" />
                <path d="M9.2 12l1.9 1.9 3.7-3.8" />
            </svg>
            <!-- Fallback when no icon is supplied -->
            <span v-else class="dot">•</span>
        </span>
        <span class="label">{{ label }}</span>
    </RouterLink>
</template>

<style scoped>
.nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px 12px;
    border-radius: var(--r-md);
    color: var(--c-body);
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;
}
.nav-item:hover {
    background: var(--c-surface-soft);
    color: var(--c-ink);
}
.nav-item.active {
    background: var(--c-surface-card);
    color: var(--c-ink);
}
.icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 16px;
    height: 16px;
    flex-shrink: 0;
    color: var(--c-muted);
}
.nav-item:hover .icon,
.nav-item.active .icon {
    color: var(--c-ink);
}
.dot {
    color: var(--c-muted-soft);
    font-size: 18px;
    line-height: 0;
}
</style>
