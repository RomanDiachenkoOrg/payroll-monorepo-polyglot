<script setup>
import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import { useConfirm } from "primevue/useconfirm";
import { onMounted, ref } from "vue";
import { http } from "@/api/http";
import FormField from "@/components/FormField.vue";
import PageHeader from "@/components/PageHeader.vue";
import { useApiCall } from "@/composables/useApiCall";
import { validateDepartment } from "@/utils/validation";

const confirm = useConfirm();
const { busy, run } = useApiCall();
const rows = ref([]);
const dialog = ref(false);
const form = ref({});
const errors = ref({});

async function load() {
  rows.value = await http.get("/api/departments");
}
onMounted(load);

function open(d = null) {
  form.value = d ? { ...d } : { name: "", code: "", managerName: "" };
  errors.value = {};
  dialog.value = true;
}

async function save() {
  errors.value = validateDepartment(form.value);
  if (Object.keys(errors.value).length) return;
  const body = { name: form.value.name, code: form.value.code, managerName: form.value.managerName || null };
  const ok = await run(() => (form.value.id ? http.put(`/api/departments/${form.value.id}`, body) : http.post("/api/departments", body)), {
    success: "Department saved",
    onError: (e) => (errors.value = Object.keys(e.fieldErrors).length ? e.fieldErrors : { name: e.message }),
  });
  if (ok) {
    dialog.value = false;
    load();
  }
}

function remove(d) {
  confirm.require({
    header: "Delete department",
    message: `Delete the ${d.name} department? This cannot be undone.`,
    icon: "pi pi-exclamation-triangle",
    rejectProps: { label: "Cancel", severity: "secondary", outlined: true },
    acceptProps: { label: "Delete", severity: "danger" },
    accept: () => run(() => http.del(`/api/departments/${d.id}`), { success: `${d.name} deleted` }).then(load),
  });
}
</script>

<template>
  <PageHeader title="Departments"><Button label="New department" icon="pi pi-plus" @click="open()" /></PageHeader>
  <section class="panel">
    <DataTable :value="rows" size="small" data-key="id">
      <Column field="name" header="Name" sortable />
      <Column field="code" header="Code" />
      <Column field="managerName" header="Manager" />
      <Column field="activeEmployees" header="Active employees" class="num" />
      <Column field="totalEmployees" header="Total" class="num" />
      <Column header="" style="width: 1%">
        <template #body="{ data }">
          <div style="display: flex; gap: 4px">
            <Button icon="pi pi-pencil" text size="small" :aria-label="`Edit ${data.name}`" @click="open(data)" />
            <Button icon="pi pi-trash" text size="small" severity="danger" :aria-label="`Delete ${data.name}`" @click="remove(data)" />
          </div>
        </template>
      </Column>
    </DataTable>
  </section>
  <Dialog v-model:visible="dialog" modal :header="form.id ? 'Edit department' : 'New department'" :style="{ width: '420px' }">
    <form id="dept-form" novalidate @submit.prevent="save">
      <FormField label="Name" for="dept-name" :error="errors.name" required><InputText id="dept-name" v-model="form.name" :invalid="!!errors.name" /></FormField>
      <FormField label="Code" for="dept-code" :error="errors.code" required><InputText id="dept-code" v-model="form.code" :invalid="!!errors.code" /></FormField>
      <FormField label="Manager" for="dept-manager"><InputText id="dept-manager" v-model="form.managerName" /></FormField>
    </form>
    <template #footer>
      <Button label="Cancel" severity="secondary" outlined @click="dialog = false" />
      <Button label="Save" type="submit" form="dept-form" :loading="busy" />
    </template>
  </Dialog>
</template>
