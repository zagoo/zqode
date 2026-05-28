<script setup lang="ts">
import { onMounted, ref } from "vue";
import { RouterLink } from "vue-router";
import ContentCard from "@/components/ContentCard.vue";
import { workbenchApi } from "./api";

const keyCount = ref(0);
const modelCount = ref(0);
const apiCount = ref(0);

onMounted(async () => {
    try {
        const [k, m, a] = await Promise.all([
            workbenchApi.listKeys(),
            workbenchApi.listModels(),
            workbenchApi.listOpenApis(),
        ]);
        keyCount.value = k.total;
        modelCount.value = m.total;
        apiCount.value = a.total;
    } catch {
        /* ignore */
    }
});
</script>

<template>
    <div class="home">
        <header class="head">
            <h1>Workbench</h1>
            <p class="muted">
                Apply for API keys, explore configured models and gateway
                endpoints, and monitor your usage.
            </p>
        </header>

        <div class="grid">
            <ContentCard
                title="API Keys"
                :description="`${keyCount} active in your account`"
            >
                <template #footer>
                    <RouterLink to="/workbench/api-keys" class="btn primary"
                        >Manage keys</RouterLink
                    >
                </template>
            </ContentCard>
            <ContentCard
                title="Model catalog"
                :description="`${modelCount} models available`"
            >
                <template #footer>
                    <RouterLink to="/workbench/models" class="btn primary"
                        >View models</RouterLink
                    >
                </template>
            </ContentCard>
            <ContentCard
                title="Gateway endpoints"
                :description="`${apiCount} enterprise endpoints`"
            >
                <template #footer>
                    <RouterLink to="/workbench/openapis" class="btn primary"
                        >View endpoints</RouterLink
                    >
                </template>
            </ContentCard>
            <ContentCard
                title="Usage analytics"
                description="Track your tokens and spend over time."
            >
                <template #footer>
                    <RouterLink to="/analytics" class="btn primary"
                        >Open analytics</RouterLink
                    >
                </template>
            </ContentCard>
        </div>
    </div>
</template>

<style scoped>
.home {
    display: flex;
    flex-direction: column;
    gap: var(--s-xl);
}
.head {
    display: flex;
    flex-direction: column;
    gap: 8px;
}
.grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: var(--s-lg);
}
@media (max-width: 960px) {
    .grid {
        grid-template-columns: repeat(2, 1fr);
    }
}
@media (max-width: 640px) {
    .grid {
        grid-template-columns: 1fr;
    }
}
</style>
