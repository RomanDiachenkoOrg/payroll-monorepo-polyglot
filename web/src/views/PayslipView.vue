<script setup>
import Button from "primevue/button";
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { downloadFile, http } from "@/api/http";
import PageHeader from "@/components/PageHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { useApiCall } from "@/composables/useApiCall";
import { money, period, shortDate } from "@/utils/format";

const route = useRoute();
const { run } = useApiCall();
const p = ref(null);
const error = ref("");

onMounted(async () => {
  try {
    p.value = await http.get(`/api/payslips/${route.params.id}`);
  } catch (e) {
    error.value = e.message;
  }
});

function printPage() {
  window.print();
}

function exportCsv() {
  run(() => downloadFile(`/api/payslips/${p.value.id}/csv`, `payslip-${p.value.id}.csv`));
}
</script>

<template>
  <p v-if="error" class="error">{{ error }}</p>
  <template v-if="p">
    <PageHeader :title="`Payslip - ${p.employeeName}`" :subtitle="period(p.periodStart, p.periodEnd)">
      <Button label="Download CSV" icon="pi pi-download" severity="secondary" outlined @click="exportCsv" />
      <Button label="Print" icon="pi pi-print" severity="secondary" outlined @click="printPage" />
    </PageHeader>
    <section class="panel" style="max-width: 720px">
      <dl class="dl">
        <dt>Employee</dt><dd>{{ p.employeeName }}</dd>
        <dt>Department</dt><dd>{{ p.departmentName }}</dd>
        <dt>Pay date</dt><dd>{{ shortDate(p.payDate) }}</dd>
        <dt>Pay run</dt><dd><StatusTag :status="p.payRunStatus" /></dd>
        <template v-if="p.payType === 'HOURLY'">
          <dt>Hours</dt><dd>{{ p.regularHours }} regular, {{ p.overtimeHours }} overtime</dd>
        </template>
      </dl>
      <table class="payslip-table" style="margin-top: 16px">
        <tbody>
          <tr><td>Gross pay</td><td class="num">{{ money(p.gross) }}</td></tr>
          <tr><td>Income tax</td><td class="num">-{{ money(p.tax) }}</td></tr>
          <tr><td>Social contribution (5%)</td><td class="num">-{{ money(p.social) }}</td></tr>
          <tr><td>Pension (3%)</td><td class="num">-{{ money(p.pension) }}</td></tr>
          <tr><td>Other deductions</td><td class="num">-{{ money(p.other) }}</td></tr>
          <tr class="total"><td>Net pay</td><td class="num">{{ money(p.net) }}</td></tr>
        </tbody>
      </table>
    </section>
  </template>
</template>
