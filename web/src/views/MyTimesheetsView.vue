<script setup>
import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import { useConfirm } from "primevue/useconfirm";
import { onMounted, ref } from "vue";
import { http } from "@/api/http";
import PageHeader from "@/components/PageHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import TimesheetEditor from "@/components/TimesheetEditor.vue";
import { useApiCall } from "@/composables/useApiCall";
import { shortDate } from "@/utils/format";

const confirm = useConfirm();
const { run } = useApiCall();
const rows = ref([]);
const editing = ref(null);
const showEditor = ref(false);

async function load() {
  rows.value = await http.get("/api/timesheets?mine=true");
}
onMounted(load);

function edit(t = null) {
  editing.value = t;
  showEditor.value = true;
}

function submit(t) {
  confirm.require({
    header: "Submit timesheet",
    message: `Submit ${t.totalHours} hours for the week of ${shortDate(t.weekStart)}? You cannot change it afterwards.`,
    rejectProps: { label: "Cancel", severity: "secondary", outlined: true },
    acceptProps: { label: "Submit" },
    accept: () => run(() => http.post(`/api/timesheets/${t.id}/submit`), { success: "Timesheet submitted" }).then(load),
  });
}
</script>

<template>
  <PageHeader title="My timesheets"><Button label="New timesheet" icon="pi pi-plus" @click="edit()" /></PageHeader>
  <section class="panel">
    <DataTable :value="rows" size="small" data-key="id">
      <template #empty>You have no timesheets yet.</template>
      <Column header="Week of"><template #body="{ data }">{{ shortDate(data.weekStart) }}</template></Column>
      <Column field="totalHours" header="Hours" class="num" />
      <Column header="Status"><template #body="{ data }"><StatusTag :status="data.status" /></template></Column>
      <Column header="Comment"><template #body="{ data }"><span class="muted">{{ data.rejectReason ?? data.notes ?? "" }}</span></template></Column>
      <Column header="" style="width: 1%">
        <template #body="{ data }">
          <div v-if="data.status === 'DRAFT' || data.status === 'REJECTED'" style="display: flex; gap: 6px">
            <Button label="Edit" size="small" text @click="edit(data)" />
            <Button label="Submit" size="small" @click="submit(data)" />
          </div>
        </template>
      </Column>
    </DataTable>
  </section>
  <TimesheetEditor v-model:visible="showEditor" :timesheet="editing" @saved="load" />
</template>
