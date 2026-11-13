<script setup>
import Button from "primevue/button";
import InputText from "primevue/inputtext";
import Message from "primevue/message";
import Password from "primevue/password";
import { reactive, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import FormField from "@/components/FormField.vue";
import { useAuthStore } from "@/stores/auth";
import { validateLogin } from "@/utils/validation";

const auth = useAuthStore();
const router = useRouter();
const route = useRoute();
const form = reactive({ email: "", password: "" });
const errors = ref({});
const formError = ref("");
const busy = ref(false);

async function submit() {
  formError.value = "";
  errors.value = validateLogin(form);
  if (Object.keys(errors.value).length) return;
  busy.value = true;
  try {
    await auth.login(form.email.trim(), form.password);
    router.replace(route.query.redirect || auth.homeRoute);
  } catch (err) {
    formError.value = err.status === 401 ? "Invalid email or password" : "Could not sign in. Please try again.";
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="login-page">
    <form class="login-card" novalidate @submit.prevent="submit">
      <h1 style="margin-top: 0">Acme Payroll</h1>
      <p class="muted">Sign in with your work account.</p>
      <Message v-if="formError" severity="error" :closable="false" style="margin-bottom: 12px">{{ formError }}</Message>
      <FormField label="Email" for="email" :error="errors.email" required>
        <InputText id="email" v-model="form.email" type="email" autocomplete="username" :invalid="!!errors.email" />
      </FormField>
      <FormField label="Password" for="password" :error="errors.password" required>
        <Password v-model="form.password" input-id="password" :feedback="false" toggle-mask autocomplete="current-password" :invalid="!!errors.password" fluid />
      </FormField>
      <Button type="submit" label="Sign in" :loading="busy" fluid />
    </form>
  </div>
</template>
