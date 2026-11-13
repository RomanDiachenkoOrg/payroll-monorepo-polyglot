<script setup>
import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import InputText from "primevue/inputtext";
import Select from "primevue/select";
import { useConfirm } from "primevue/useconfirm";
import { onMounted, reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { http, query } from "@/api/http";
import EmployeeForm from "@/components/EmployeeForm.vue";
import PageHeader from "@/components/PageHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { useApiCall } from "@/composables/useApiCall";
import { useAuthStore } from "@/stores/auth";
import { money, shortDate } from "@/utils/format";

const auth = useAuthStore();
const router = useRouter();
const confirm = useConfirm();
const { run } = useApiCall();

const rows = ref([]);
const total = ref(0);
const loading = ref(false);
const departments = ref([]);
const filters = reactive({ q: "", departmentId: null, status: "ACTIVE" });
const paging = reactive({ page: 1, pageSize: 10, sortBy: "name", sortDir: "asc" });
const editing = ref(null);
const showForm = ref(false);

const statuses = [
  { label: "All", value: "ALL" },
  { label: "Active", value: "ACTIVE" },
  { label: "Inactive", value: "INACTIVE" },
];

async function load() {
  loading.value = true;
  try {
    const res = await http.get(`/api/employees${query({ ...filters, ...paging })}`);
    rows.value = res.items;
    total.value = res.total;
  } finally {
    loading.value = false;
  }
}

let timer;
watch(
  () => ({ ...filters }),
  () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      paging.page = 1;
      load();
    }, 250);
  },
);

onMounted(async () => {
  departments.value = await http.get("/api/departments");
  load();
});

function onPage(e) {
  paging.page = e.page + 1;
  paging.pageSize = e.rows;
  load();
}

function onSort(e) {
  paging.sortBy = e.sortField ?? "name";
  paging.sortDir = e.sortOrder === -1 ? "desc" : "asc";
  load();
}

function openForm(emp = null) {
  editing.value = emp;
  showForm.value = true;
}

function deactivate(emp) {
  confirm.require({
    header: "Deactivate employee",
    message: `Deactivate ${emp.fullName}? They will be excluded from pay runs and their login will be disabled.`,
    icon: "pi pi-exclamation-triangle",
    rejectProps: { label: "Cancel", severity: "secondary", outlined: true },
    acceptProps: { label: "Deactivate", severity: "danger" },
    accept: () => run(() => http.post(`/api/employees/${emp.id}/deactivate`), { success: `${emp.fullName} deactivated` }).then(load),
  });
}
</script>

<template>
  <PageHeader title="Employees" subtitle="Search, filter and maintain employee records">
    <Button v-if="auth.isAdmin" label="New employee" icon="pi pi-plus" @click="openForm()" />
  </PageHeader>
  <section class="panel">
    <div class="toolbar">
      <div class="field">
        <label for="emp-search">Search</label>
        <InputText id="emp-search" v-model="filters.q" placeholder="Name, email or title" />
      </div>
      <div class="field">
        <label for="emp-dept">Department</label>
        <Select v-model="filters.departmentId" input-id="emp-dept" :options="departments" option-label="name" option-value="id" placeholder="All departments" show-clear style="min-width: 200px" />
      </div>
      <div class="field">
        <label for="emp-status">Status</label>
        <Select v-model="filters.status" input-id="emp-status" :options="statuses" option-label="label" option-value="value" />
      </div>
    </div>
    <DataTable
      :value="rows"
      lazy
      paginator
      :rows="paging.pageSize"
      :total-records="total"
      :loading="loading"
      :rows-per-page-options="[10, 25, 50]"
      sort-field="name"
      :sort-order="1"
      data-key="id"
      size="small"
      striped-rows
      @page="onPage"
      @sort="onSort"
      @row-click="(e) => router.push(`/employees/${e.data.id}`)"
    >
      <template #empty>No employees match the filters.</template>
      <Column field="name" header="Name" sortable>
        <template #body="{ data }"><RouterLink :to="`/employees/${data.id}`">{{ data.fullName }}</RouterLink></template>
      </Column>
      <Column field="email" header="Email" sortable />
      <Column field="department" header="Department" sortable><template #body="{ data }">{{ data.departmentName }}</template></Column>
      <Column field="title" header="Title" sortable />
      <Column field="hireDate" header="Hired" sortable><template #body="{ data }">{{ shortDate(data.hireDate) }}</template></Column>
      <Column header="Pay" class="num">
        <template #body="{ data }">{{ data.payType === "SALARIED" ? `${money(data.annualSalary)}/yr` : `${money(data.hourlyRate)}/h` }}</template>
      </Column>
      <Column field="status" header="Status" sortable><template #body="{ data }"><StatusTag :status="data.status" /></template></Column>
      <Column v-if="auth.isAdmin" header="" style="width: 1%">
        <template #body="{ data }">
          <div style="display: flex; gap: 6px" @click.stop>
            <Button icon="pi pi-pencil" size="small" text :aria-label="`Edit ${data.fullName}`" @click="openForm(data)" />
            <Button v-if="data.status === 'ACTIVE'" icon="pi pi-ban" size="small" text severity="danger" :aria-label="`Deactivate ${data.fullName}`" @click="deactivate(data)" />
          </div>
        </template>
      </Column>
    </DataTable>
  </section>
  <EmployeeForm v-model:visible="showForm" :employee="editing" :departments="departments" @saved="load" />
</template>
