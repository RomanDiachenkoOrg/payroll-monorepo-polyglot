<script setup>
import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dialog from "primevue/dialog";
import Select from "primevue/select";
import Textarea from "primevue/textarea";
import { onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { http, query } from "@/api/http";
import FormField from "@/components/FormField.vue";
import PageHeader from "@/components/PageHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import TimesheetEditor from "@/components/TimesheetEditor.vue";
import { useApiCall } from "@/composables/useApiCall";
import { useAuthStore } from "@/stores/auth";
import { shortDate } from "@/utils/format";

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();
const { busy, run } = useApiCall();
const rows = ref([]);
const loading = ref(false);
const status = ref(route.query.status ?? null);
const rejecting = ref(null);
const reason = ref("");
const reasonError = ref("");
const showEditor = ref(false);
const employees = ref([]);

const statuses = ["DRAFT", "SUBMITTED", "APPROVED", "REJECTED"].map((s) => ({ label: s.charAt(0) + s.slice(1).toLowerCase(), value: s }));

async function load() {
  loading.value = true;
  try {
    rows.value = await http.get(`/api/timesheets${query({ status: status.value })}`);
  } finally {
    loading.value = false;
  }
}

watch(status, (s) => {
  router.replace({ query: s ? { status: s } : {} });
  load();
});

onMounted(async () => {
  load();
  if (auth.isAdmin) employees.value = await http.get("/api/employees/options");
});

function canDecide(t) {
  if (t.status === "APPROVED" || t.status === "REJECTED") return false;
  if (auth.isAdmin) return true;
  return auth.isManager && t.departmentId === auth.user.departmentId && t.employeeId !== auth.user.employeeId;
}

async function approve(t) {
  await run(() => http.post(`/api/timesheets/${t.id}/approve`), { success: `Approved ${t.employeeName}, week of ${shortDate(t.weekStart)}` });
  load();
}

function openReject(t) {
  rejecting.value = t;
  reason.value = "";
  reasonError.value = "";
}

async function reject() {
  if (reason.value.trim().length < 3) {
    reasonError.value = "Please give a reason (at least 3 characters)";
    return;
  }
  const ok = await run(() => http.post(`/api/timesheets/${rejecting.value.id}/reject`, { reason: reason.value }), {
    success: "Timesheet rejected",
    onError: (e) => (reasonError.value = e.fieldErrors?.reason ?? e.message),
  });
  if (ok) {
    rejecting.value = null;
    load();
  }
}
</script>

<template>
  <PageHeader title="Timesheets" subtitle="Weekly hours of hourly staff">
    <Button v-if="auth.isAdmin" label="New timesheet" icon="pi pi-plus" @click="showEditor = true" />
  </PageHeader>
  <section class="panel">
    <div class="toolbar">
      <div class="field">
        <label for="ts-status">Status</label>
        <Select v-model="status" input-id="ts-status" :options="statuses" option-label="label" option-value="value" placeholder="All" show-clear style="min-width: 180px" />
      </div>
    </div>
    <DataTable :value="rows" :loading="loading" size="small" paginator :rows="15" data-key="id">
      <template #empty>No timesheets.</template>
      <Column header="Week of" field="weekStart" sortable><template #body="{ data }">{{ shortDate(data.weekStart) }}</template></Column>
      <Column field="employeeName" header="Employee" sortable />
      <Column field="departmentName" header="Department" sortable />
      <Column field="totalHours" header="Hours" class="num" />
      <Column header="Status"><template #body="{ data }"><StatusTag :status="data.status" /></template></Column>
      <Column header="Comment"><template #body="{ data }"><span class="muted">{{ data.rejectReason ?? data.notes ?? "" }}</span></template></Column>
      <Column header="" style="width: 1%">
        <template #body="{ data }">
          <div v-if="canDecide(data)" style="display: flex; gap: 6px">
            <Button label="Approve" size="small" :loading="busy" @click="approve(data)" />
            <Button label="Reject" size="small" severity="danger" outlined @click="openReject(data)" />
          </div>
        </template>
      </Column>
    </DataTable>
  </section>
  <Dialog :visible="!!rejecting" modal :header="`Reject timesheet of ${rejecting?.employeeName}`" :style="{ width: '460px' }" @update:visible="rejecting = null">
    <FormField label="Reason" for="reject-reason" :error="reasonError" required>
      <Textarea id="reject-reason" v-model="reason" rows="3" :invalid="!!reasonError" />
    </FormField>
    <template #footer>
      <Button label="Cancel" severity="secondary" outlined @click="rejecting = null" />
      <Button label="Reject" severity="danger" :loading="busy" @click="reject" />
    </template>
  </Dialog>
  <TimesheetEditor v-model:visible="showEditor" :employees="employees" @saved="load" />
</template>
