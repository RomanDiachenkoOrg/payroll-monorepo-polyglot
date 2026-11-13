<script setup>
import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import InputText from "primevue/inputtext";
import { onMounted, ref } from "vue";
import { downloadFile, http, query } from "@/api/http";
import FormField from "@/components/FormField.vue";
import PageHeader from "@/components/PageHeader.vue";
import { useApiCall } from "@/composables/useApiCall";
import { monthRange, money } from "@/utils/format";

const { busy, run } = useApiCall();
const from = ref(monthRange(-2).start);
const to = ref(monthRange(-1).end);
const rows = ref([]);
const totals = ref(null);
const error = ref("");

async function load() {
  error.value = "";
  if (!from.value || !to.value || to.value < from.value) {
    error.value = "The start date must be before the end date.";
    return;
  }
  const res = await run(() => http.get(`/reports/department-cost${query({ from: from.value, to: to.value })}`));
  if (res) {
    rows.value = res.rows;
    totals.value = res.totals;
  }
}
onMounted(load);

function exportCsv() {
  run(() => downloadFile(`/reports/department-cost.csv${query({ from: from.value, to: to.value })}`, "payroll-cost.csv"));
}
</script>

<template>
  <PageHeader title="Reports" subtitle="Payroll cost by department (approved and paid pay runs)" />
  <section class="panel">
    <form class="toolbar" novalidate @submit.prevent="load">
      <FormField label="From" for="report-from"><InputText id="report-from" v-model="from" type="date" /></FormField>
      <FormField label="To" for="report-to"><InputText id="report-to" v-model="to" type="date" /></FormField>
      <div class="field"><Button type="submit" label="Run report" :loading="busy" /></div>
      <div class="field"><Button label="Export CSV" icon="pi pi-download" severity="secondary" outlined :disabled="!rows.length" @click="exportCsv" /></div>
    </form>
    <p v-if="error" class="error" role="alert">{{ error }}</p>
    <DataTable :value="rows" size="small" data-key="departmentId">
      <template #empty>No approved or paid payroll in this period.</template>
      <Column field="department" header="Department" />
      <Column field="employees" header="Employees" class="num" />
      <Column header="Gross" class="num"><template #body="{ data }">{{ money(data.gross) }}</template></Column>
      <Column header="Income tax" class="num"><template #body="{ data }">{{ money(data.tax) }}</template></Column>
      <Column header="Social" class="num"><template #body="{ data }">{{ money(data.social) }}</template></Column>
      <Column header="Pension" class="num"><template #body="{ data }">{{ money(data.pension) }}</template></Column>
      <Column header="Other" class="num"><template #body="{ data }">{{ money(data.other) }}</template></Column>
      <Column header="Net" class="num"><template #body="{ data }">{{ money(data.net) }}</template></Column>
    </DataTable>
    <p v-if="rows.length && totals"><strong>Total:</strong> gross {{ money(totals.gross) }}, net {{ money(totals.net) }}</p>
  </section>
</template>
