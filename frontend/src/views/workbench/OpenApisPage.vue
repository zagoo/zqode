<script setup lang="ts">
import { onMounted, ref } from "vue";
import type { WorkbenchOpenAPIOut } from "@/api/generated/types";
import { workbenchApi } from "./api";

const apis = ref<WorkbenchOpenAPIOut[]>([]);
const loading = ref(true);

function copy(text: string | null | undefined) {
    if (!text) return;
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).catch(() => fallbackCopy(text));
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text: string) {
    const textArea = document.createElement("textarea");
    textArea.value = text;
    textArea.style.position = "fixed";
    textArea.style.opacity = "0";
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    try {
        document.execCommand("copy");
    } catch (err) {
        console.error("Fallback copy failed:", err);
    }
    document.body.removeChild(textArea);
}

onMounted(async () => {
    try {
        const page = await workbenchApi.listOpenApis();
        apis.value = page.items;
    } finally {
        loading.value = false;
    }
});
</script>

<template>
    <div class="page">
        <header>
            <h1>Gateway endpoints</h1>
            <p class="muted">
                Use these endpoints with OpenAI- or Anthropic-compatible
                clients.
            </p>
        </header>
        <div class="grid">
            <article v-for="o in apis" :key="o.openapi_id" class="card">
                <header>
                    <span
                        class="badge"
                        :class="
                            o.api_type === 'OPENAI_COMPATIBLE' ? 'coral' : ''
                        "
                    >
                        {{
                            o.api_type === "OPENAI_COMPATIBLE"
                                ? "OpenAI"
                                : "Anthropic"
                        }}
                    </span>
                    <h3>{{ o.api_name }}</h3>
                </header>
                <div class="url">
                    <code class="mono">{{ o.gateway_url }}</code>
                    <button
                        class="btn ghost sm"
                        @click="copy(o.usage_description)"
                    >
                        Copy
                    </button>
                </div>
                <p v-if="o.usage_description" class="muted">
                    {{ o.usage_description }}
                </p>
            </article>
            <article v-if="!loading && apis.length === 0" class="card empty">
                No gateway endpoints configured yet.
            </article>
        </div>
    </div>
</template>

<style scoped>
.page {
    display: flex;
    flex-direction: column;
    gap: var(--s-lg);
}
.grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--s-lg);
}
@media (max-width: 720px) {
    .grid {
        grid-template-columns: 1fr;
    }
}
.card header {
    display: flex;
    flex-direction: column;
    gap: var(--s-xs);
}
.url {
    display: flex;
    align-items: center;
    gap: var(--s-xs);
}
.url code {
    flex: 1;
    overflow-x: auto;
    background: var(--c-canvas);
    padding: 6px 10px;
    border-radius: var(--r-md);
    border: 1px solid var(--c-hairline);
}
.empty {
    color: var(--c-muted);
    text-align: center;
}
</style>
