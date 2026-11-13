<script setup>
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import { computed, onMounted, ref } from "vue";
import { http } from "@/api/http";
import PageHeader from "@/components/PageHeader.vue";
import { money, period, shortDate } from "@/utils/format";

const rows = ref([]);
const mail = ref([]);
onMounted(async () => {
  [rows.value, mail.value] = await Promise.all([http.get("/api/me/payslips"), http.get("/api/me/mailbox")]);
});

const ytd = computed(() => {
  const year = String(new Date().getFullYear());
  return rows.value.filter((p) => p.payDate.startsWith(year)).reduce((a, p) => ({ gross: a.gross + p.gross, net: a.net + p.net }), { gross: 0, net: 0 });
});
</script>

<template>
  <PageHeader title="My payslips" :subtitle="`Year to date: gross ${money(ytd.gross)}, net ${money(ytd.net)}`" />
  <section class="panel">
    <DataTable :value="rows" size="small" data-key="id">
      <template #empty>No payslips yet. They appear here once a pay run is approved.</template>
      <Column header="Period"><template #body="{ data }"><RouterLink :to="`/payslips/${data.id}`">{{ period(data.periodStart, data.periodEnd) }}</RouterLink></template></Column>
      <Column header="Pay date"><template #body="{ data }">{{ shortDate(data.payDate) }}</template></Column>
      <Column header="Gross" class="num"><template #body="{ data }">{{ money(data.gross) }}</template></Column>
      <Column header="Deductions" class="num"><template #body="{ data }">{{ money(data.gross - data.net) }}</template></Column>
      <Column header="Net pay" class="num"><template #body="{ data }"><strong>{{ money(data.net) }}</strong></template></Column>
    </DataTable>
  </section>
  <section v-if="mail.length" class="panel">
    <h2>Notifications</h2>
    <ul>
      <li v-for="m in mail" :key="m.id">{{ m.subject }} <span class="muted">({{ shortDate(m.createdAt) }})</span></li>
    </ul>
  </section>
</template>
