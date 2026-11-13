<script setup>
import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Message from "primevue/message";
import { useConfirm } from "primevue/useconfirm";
import { computed, onMounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { http } from "@/api/http";
import PageHeader from "@/components/PageHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { useApiCall } from "@/composables/useApiCall";
import { useAuthStore } from "@/stores/auth";
import { money, period, shortDate } from "@/utils/format";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const confirm = useConfirm();
const { busy, run } = useApiCall();
const payRun = ref(null);

async function load() {
  payRun.value = await http.get(`/api/payruns/${route.params.id}`);
}
onMounted(load);

const totalTax = computed(() => (payRun.value?.lines ?? []).reduce((a, l) => a + l.tax, 0));

const ACTIONS = {
  calculate: { header: "Calculate pay run", message: "Calculate payslips for all active employees? Existing lines are replaced.", label: "Calculate" },
  approve: { header: "Approve pay run", message: "Approve this pay run? Employees will be notified and can see their payslips.", label: "Approve" },
  pay: { header: "Mark as paid", message: "Mark this pay run as paid? It will be locked.", label: "Mark paid" },
  delete: { header: "Delete pay run", message: "Delete this pay run and its lines?", label: "Delete" },
};

function act(action) {
  const a = ACTIONS[action];
  confirm.require({
    header: a.header,
    message: a.message,
    rejectProps: { label: "Cancel", severity: "secondary", outlined: true },
    acceptProps: { label: a.label, severity: action === "delete" ? "danger" : undefined },
    accept: async () => {
      const id = payRun.value.id;
      const ok = await run(() => (action === "delete" ? http.del(`/api/payruns/${id}`) : http.post(`/api/payruns/${id}/${action}`)), { success: `${a.label} done` });
      if (ok === undefined) return;
      if (action === "delete") router.push("/payruns");
      else load();
    },
  });
}
</script>

<template>
  <template v-if="payRun">
    <PageHeader :title="`Pay run #${payRun.id}`" :subtitle="`${period(payRun.periodStart, payRun.periodEnd)} · pay date ${shortDate(payRun.payDate)}`">
      <template v-if="auth.isAdmin">
        <Button v-if="['DRAFT', 'CALCULATED'].includes(payRun.status)" label="Delete" severity="secondary" outlined :disabled="busy" @click="act('delete')" />
        <Button v-if="['DRAFT', 'CALCULATED'].includes(payRun.status)" :label="payRun.status === 'DRAFT' ? 'Calculate' : 'Recalculate'" severity="secondary" :loading="busy" @click="act('calculate')" />
        <Button v-if="payRun.status === 'CALCULATED'" label="Approve" :disabled="busy" @click="act('approve')" />
        <Button v-if="payRun.status === 'APPROVED'" label="Mark paid" :disabled="busy" @click="act('pay')" />
      </template>
    </PageHeader>
    <Message v-if="payRun.status === 'PAID'" severity="info" :closable="false" style="margin-bottom: 12px">Paid on {{ shortDate(payRun.paidAt) }}. This pay run is locked.</Message>
    <div class="stats">
      <div class="stat"><div class="label">Status</div><div class="value"><StatusTag :status="payRun.status" /></div></div>
      <div class="stat"><div class="label">Employees</div><div class="value">{{ payRun.lines.length }}</div></div>
      <div class="stat"><div class="label">Gross</div><div class="value">{{ money(payRun.totalGross) }}</div></div>
      <div class="stat"><div class="label">Income tax</div><div class="value">{{ money(totalTax) }}</div></div>
      <div class="stat"><div class="label">Net</div><div class="value">{{ money(payRun.totalNet) }}</div></div>
    </div>
    <section class="panel">
      <h2>Lines</h2>
      <DataTable :value="payRun.lines" size="small" sort-mode="single" data-key="id">
        <template #empty>Not calculated yet.</template>
        <Column field="employeeName" header="Employee" sortable><template #body="{ data }"><RouterLink :to="`/payslips/${data.id}`">{{ data.employeeName }}</RouterLink></template></Column>
        <Column field="departmentName" header="Department" sortable />
        <Column field="overtimeHours" header="OT h" class="num" />
        <Column field="gross" header="Gross" class="num" sortable><template #body="{ data }">{{ money(data.gross) }}</template></Column>
        <Column field="tax" header="Tax" class="num"><template #body="{ data }">{{ money(data.tax) }}</template></Column>
        <Column field="social" header="Social" class="num"><template #body="{ data }">{{ money(data.social) }}</template></Column>
        <Column field="pension" header="Pension" class="num"><template #body="{ data }">{{ money(data.pension) }}</template></Column>
        <Column field="other" header="Other" class="num"><template #body="{ data }">{{ money(data.other) }}</template></Column>
        <Column field="net" header="Net" class="num" sortable><template #body="{ data }"><strong>{{ money(data.net) }}</strong></template></Column>
      </DataTable>
    </section>
  </template>
</template>
