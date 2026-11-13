<script setup>
import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { http } from "@/api/http";
import FormField from "@/components/FormField.vue";
import PageHeader from "@/components/PageHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { useApiCall } from "@/composables/useApiCall";
import { useAuthStore } from "@/stores/auth";
import { monthRange, money, period, shortDate } from "@/utils/format";

const auth = useAuthStore();
const router = useRouter();
const { busy, run } = useApiCall();
const rows = ref([]);
const dialog = ref(false);
const form = ref({});
const errors = ref({});

async function load() {
  rows.value = await http.get("/api/payruns");
}
onMounted(load);

function openCreate() {
  const next = monthRange(1);
  form.value = { periodStart: next.start, periodEnd: next.end, payDate: next.end };
  errors.value = {};
  dialog.value = true;
}

async function create() {
  errors.value = {};
  if (!form.value.periodStart) errors.value.periodStart = "Required";
  if (!form.value.periodEnd) errors.value.periodEnd = "Required";
  else if (form.value.periodEnd < form.value.periodStart) errors.value.periodEnd = "Period end must be after the start";
  if (!form.value.payDate) errors.value.payDate = "Required";
  if (Object.keys(errors.value).length) return;
  const run_ = await run(() => http.post("/api/payruns", form.value), {
    success: "Pay run created",
    onError: (e) => (errors.value = { ...e.fieldErrors, _: e.message }),
  });
  if (run_) router.push(`/payruns/${run_.id}`);
}
</script>

<template>
  <PageHeader title="Pay runs" subtitle="Create, calculate, review, approve and pay">
    <Button v-if="auth.isAdmin" label="New pay run" icon="pi pi-plus" @click="openCreate" />
  </PageHeader>
  <section class="panel">
    <DataTable :value="rows" size="small" data-key="id" @row-click="(e) => router.push(`/payruns/${e.data.id}`)">
      <Column field="id" header="#" />
      <Column header="Period"><template #body="{ data }"><RouterLink :to="`/payruns/${data.id}`">{{ period(data.periodStart, data.periodEnd) }}</RouterLink></template></Column>
      <Column header="Pay date"><template #body="{ data }">{{ shortDate(data.payDate) }}</template></Column>
      <Column header="Status"><template #body="{ data }"><StatusTag :status="data.status" /></template></Column>
      <Column field="employeeCount" header="Employees" class="num" />
      <Column header="Gross" class="num"><template #body="{ data }">{{ money(data.totalGross) }}</template></Column>
      <Column header="Net" class="num"><template #body="{ data }">{{ money(data.totalNet) }}</template></Column>
    </DataTable>
  </section>
  <Dialog v-model:visible="dialog" modal header="New pay run" :style="{ width: '420px' }">
    <p v-if="errors._" class="error" role="alert">{{ errors._ }}</p>
    <FormField label="Period start" for="pr-start" :error="errors.periodStart" required><InputText id="pr-start" v-model="form.periodStart" type="date" /></FormField>
    <FormField label="Period end" for="pr-end" :error="errors.periodEnd" required><InputText id="pr-end" v-model="form.periodEnd" type="date" /></FormField>
    <FormField label="Pay date" for="pr-pay" :error="errors.payDate" required><InputText id="pr-pay" v-model="form.payDate" type="date" /></FormField>
    <template #footer>
      <Button label="Cancel" severity="secondary" outlined @click="dialog = false" />
      <Button label="Create" :loading="busy" @click="create" />
    </template>
  </Dialog>
</template>
