<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/store/auth';
import { authApi } from './api';

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const step = ref<'email' | 'code'>('email');
const enterpriseEmail = ref('');
const challengeId = ref<string | null>(null);
const expiresAt = ref<string | null>(null);
const password = ref('');
const error = ref<string | null>(null);
const submitting = ref(false);
const emailMask = ref('');

const emailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(enterpriseEmail.value));

async function sendChallenge() {
  error.value = null;
  submitting.value = true;
  try {
    const data = await authApi.createChallenge(enterpriseEmail.value.trim().toLowerCase());
    challengeId.value = data.challenge_id;
    expiresAt.value = data.expires_at;
    emailMask.value = data.enterprise_email_mask;
    step.value = 'code';
  } catch (e: any) {
    error.value = e.message || 'Could not send a login code.';
  } finally {
    submitting.value = false;
  }
}

async function verify() {
  if (!challengeId.value) return;
  error.value = null;
  submitting.value = true;
  try {
    const session = await authApi.verifyChallenge(
      challengeId.value,
      enterpriseEmail.value.trim().toLowerCase(),
      password.value.trim()
    );
    auth.setSession(session);
    const next = (route.query.next as string) || '/workbench';
    router.replace(next);
  } catch (e: any) {
    error.value = e.message || 'Invalid login code.';
  } finally {
    submitting.value = false;
  }
}

function back() {
  step.value = 'email';
  password.value = '';
  error.value = null;
}
</script>

<template>
  <div class="login-page">
    <section class="panel">
      <div class="brand">
        <span class="mark">✻</span>
        <span class="wordmark">ZQode Gateway</span>
      </div>
      <h1 class="display">Sign in to your enterprise gateway.</h1>
      <p class="muted lead">
        Use your enterprise email. We'll send a one-time random password.
      </p>

      <form v-if="step === 'email'" @submit.prevent="sendChallenge">
        <div class="form-row">
          <label for="email">Enterprise email</label>
          <input id="email" v-model="enterpriseEmail" type="email" placeholder="name@company.com" autocomplete="email" />
        </div>
        <button class="btn primary" type="submit" :disabled="!emailValid || submitting">
          {{ submitting ? 'Sending…' : 'Send login code' }}
        </button>
      </form>

      <form v-else @submit.prevent="verify">
        <p class="check-line">
          Code sent to <span class="mono">{{ emailMask }}</span>.
        </p>
        <div class="form-row">
          <label for="code">Random password</label>
          <input id="code" v-model="password" type="text" inputmode="numeric" placeholder="6-digit code" autocomplete="one-time-code" />
        </div>
        <div class="row">
          <button class="btn ghost" type="button" @click="back">Back</button>
          <button class="btn primary" type="submit" :disabled="!password || submitting">
            {{ submitting ? 'Verifying…' : 'Sign in' }}
          </button>
        </div>
      </form>

      <p v-if="error" class="error">{{ error }}</p>
    </section>
    <aside class="art">
      <div class="art-card">
        <div class="art-mark">✻</div>
        <h3 class="display">Centralized LLM access for your organization</h3>
        <p>
          One credential. Per-user quotas. Detailed cost analytics. Provider-agnostic.
        </p>
        <ul class="bullets">
          <li>OpenAI & Anthropic compatible</li>
          <li>Per-user cost limits and monthly reset</li>
          <li>Audit-grade usage logs</li>
        </ul>
      </div>
    </aside>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
  background: var(--c-canvas);
}
.panel {
  padding: 96px 64px;
  display: flex;
  flex-direction: column;
  gap: var(--s-md);
  max-width: 540px;
  justify-self: end;
  width: 100%;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: var(--s-lg);
}
.mark { font-size: 22px; color: var(--c-ink); }
.wordmark {
  font-family: var(--f-display);
  font-size: 20px;
  letter-spacing: -0.3px;
}
.display { font-family: var(--f-display); font-size: 40px; font-weight: 400; letter-spacing: -0.5px; line-height: 1.1; }
.lead { font-size: 16px; max-width: 420px; margin-bottom: var(--s-md); }
.row { display: flex; gap: var(--s-sm); margin-top: var(--s-sm); }
.error {
  color: var(--c-error);
  margin-top: var(--s-md);
  font-size: 14px;
}
.check-line { font-size: 14px; color: var(--c-body); margin: 0 0 var(--s-md); }
.art {
  background: var(--c-surface-dark);
  color: var(--c-on-dark);
  display: grid;
  place-items: center;
  padding: var(--s-section);
}
.art-card { max-width: 480px; display: flex; flex-direction: column; gap: var(--s-md); }
.art-mark { font-size: 32px; color: var(--c-primary); }
.art-card .display {
  font-size: 36px;
  color: var(--c-on-dark);
}
.art-card p { color: var(--c-on-dark-soft); }
.bullets { list-style: none; padding: 0; margin: 0; color: var(--c-on-dark-soft); }
.bullets li { padding: 6px 0; }
@media (max-width: 900px) {
  .login-page { grid-template-columns: 1fr; }
  .art { display: none; }
  .panel { padding: 48px 24px; justify-self: stretch; }
}
</style>
