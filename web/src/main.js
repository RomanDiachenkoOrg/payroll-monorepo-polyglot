import "primeicons/primeicons.css";
import "./styles.css";

import Aura from "@primevue/themes/aura";
import { createPinia } from "pinia";
import PrimeVue from "primevue/config";
import ConfirmationService from "primevue/confirmationservice";
import ToastService from "primevue/toastservice";
import { createApp } from "vue";

import App from "./App.vue";
import router from "./router";

const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(PrimeVue, { theme: { preset: Aura, options: { darkModeSelector: ".app-dark" } } });
app.use(ToastService);
app.use(ConfirmationService);
app.mount("#app");
