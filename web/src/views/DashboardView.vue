<script setup>
import DataTable from "primevue/datatable";
import Column from "primevue/column";
import { computed, onMounted, ref } from "vue";
import { http } from "@/api/http";
import PageHeader from "@/components/PageHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { money, period, shortDate } from "@/utils/format";

const data = ref(null);
const error = ref("");

onMounted(async () => {
  try {
    data.value = await http.get("/api/dashboard");
  } catch (e) {
    error.value = e.message;
  }
});

const maxCost = computed(() => Math.max(1, ...(data.value?.costByDepartment ?? []).map((d) => d.gross)));
</script>

<template>
  <PageHeader title="Dashboard" subtitle="Current payroll cycle at a glance" />
  <p v-if="error" class="error">{{ error }}</p>
  <template v-if="data">
    <div class="stats">
      <div class="stat"><div class="label">Active employees</div><div class="value">{{ data.activeHeadcount }}</div><div class="muted">{{ data.headcount }} on record</div></div>
      <div class="stat"><div class="label">Last payroll (gross)</div><div class="value">{{ money(data.lastPayrollGross) }}</div><div class="muted">{{ data.lastPayrollPeriod }}</div></div>
      <div class="stat">
        <div class="label">Pending timesheets</div>
        <div class="value"><RouterLink :to="{ path: '/timesheets', query: { status: 'SUBMITTED' } }">{{ data.pendingTimesheets }}</RouterLink></div>
      </div>
      <div class="stat"><div class="label">Next pay date</div><div class="value">{{ shortDate(data.nextPayDate) }}</div></div>
    </div>
    <div class="grid-2">
      <section class="panel">
        <h2>Last payroll by department</h2>
        <div class="bars" role="list">
          <div v-for="d in data.costByDepartment" :key="d.department" class="row" role="listitem">
            <span>{{ d.department }}</span>
            <span class="track"><span class="bar" :style="{ width: `${(d.gross / maxCost) * 100}%`, display: 'block' }" /></span>
            <span class="num">{{ money(d.gross) }}</span>
          </div>
        </div>
      </section>
      <section class="panel">
        <h2>Recent pay runs</h2>
        <DataTable :value="data.recentPayRuns" size="small">
          <Column header="Period">
            <template #body="{ data: r }"><RouterLink :to="`/payruns/${r.id}`">{{ period(r.periodStart, r.periodEnd) }}</RouterLink></template>
          </Column>
          <Column header="Status"><template #body="{ data: r }"><StatusTag :status="r.status" /></template></Column>
          <Column header="Net" class="num"><template #body="{ data: r }">{{ money(r.totalNet) }}</template></Column>
        </DataTable>
      </section>
    </div>
  </template>
</template>
