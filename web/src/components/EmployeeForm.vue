<script setup>
import Button from "primevue/button";
import Checkbox from "primevue/checkbox";
import Dialog from "primevue/dialog";
import InputNumber from "primevue/inputnumber";
import InputText from "primevue/inputtext";
import Select from "primevue/select";
import { ref, watch } from "vue";
import { http } from "@/api/http";
import FormField from "@/components/FormField.vue";
import { useApiCall } from "@/composables/useApiCall";
import { isoToday } from "@/utils/format";
import { validateEmployee } from "@/utils/validation";

const props = defineProps({ employee: { type: Object, default: null }, departments: { type: Array, default: () => [] } });
const visible = defineModel("visible", { type: Boolean });
const emit = defineEmits(["saved"]);
const { busy, run } = useApiCall();

const form = ref({});
const errors = ref({});
const formError = ref("");

const payTypes = [
  { label: "Salaried (monthly)", value: "SALARIED" },
  { label: "Hourly", value: "HOURLY" },
];

watch(visible, (open) => {
  if (!open) return;
  const e = props.employee;
  errors.value = {};
  formError.value = "";
  form.value = {
    firstName: e?.firstName ?? "",
    lastName: e?.lastName ?? "",
    email: e?.email ?? "",
    phone: e?.phone ?? "",
    title: e?.title ?? "",
    departmentId: e?.departmentId ?? null,
    payType: e?.payType ?? "SALARIED",
    annualSalary: e?.annualSalary ?? null,
    hourlyRate: e?.hourlyRate ?? null,
    pensionOptIn: e?.pensionOptIn ?? false,
    healthInsurance: e?.healthInsurance ?? 0,
    hireDate: e?.hireDate ?? isoToday(),
  };
});

async function save() {
  errors.value = validateEmployee(form.value);
  if (Object.keys(errors.value).length) return;
  const body = { ...form.value, phone: form.value.phone || null };
  const saved = await run(
    () => (props.employee ? http.put(`/api/employees/${props.employee.id}`, body) : http.post("/api/employees", body)),
    {
      success: "Employee saved",
      onError: (err) => {
        errors.value = err.fieldErrors ?? {};
        formError.value = err.message;
      },
    },
  );
  if (saved) {
    visible.value = false;
    emit("saved", saved);
  }
}
</script>

<template>
  <Dialog v-model:visible="visible" modal :header="employee ? `Edit ${employee.fullName}` : 'New employee'" :style="{ width: '680px' }">
    <form id="employee-form" novalidate @submit.prevent="save">
      <p v-if="formError && !Object.keys(errors).length" class="error" role="alert">{{ formError }}</p>
      <div class="form-grid">
        <FormField label="First name" for="firstName" :error="errors.firstName" required><InputText id="firstName" v-model="form.firstName" :invalid="!!errors.firstName" /></FormField>
        <FormField label="Last name" for="lastName" :error="errors.lastName" required><InputText id="lastName" v-model="form.lastName" :invalid="!!errors.lastName" /></FormField>
        <FormField label="Email" for="email" :error="errors.email" required><InputText id="email" v-model="form.email" type="email" :invalid="!!errors.email" /></FormField>
        <FormField label="Phone" for="phone" :error="errors.phone"><InputText id="phone" v-model="form.phone" /></FormField>
        <FormField label="Job title" for="title" :error="errors.title" required><InputText id="title" v-model="form.title" :invalid="!!errors.title" /></FormField>
        <FormField label="Department" for="departmentId" :error="errors.departmentId" required>
          <Select v-model="form.departmentId" input-id="departmentId" :options="departments" option-label="name" option-value="id" placeholder="Select..." :invalid="!!errors.departmentId" />
        </FormField>
        <FormField label="Pay type" for="payType" required>
          <Select v-model="form.payType" input-id="payType" :options="payTypes" option-label="label" option-value="value" />
        </FormField>
        <FormField v-if="form.payType === 'SALARIED'" label="Annual salary (USD)" for="annualSalary" :error="errors.annualSalary" required>
          <InputNumber v-model="form.annualSalary" input-id="annualSalary" mode="currency" currency="USD" locale="en-US" :invalid="!!errors.annualSalary" />
        </FormField>
        <FormField v-else label="Hourly rate (USD)" for="hourlyRate" :error="errors.hourlyRate" required>
          <InputNumber v-model="form.hourlyRate" input-id="hourlyRate" mode="currency" currency="USD" locale="en-US" :invalid="!!errors.hourlyRate" />
        </FormField>
        <FormField label="Hire date" for="hireDate" :error="errors.hireDate" required><InputText id="hireDate" v-model="form.hireDate" type="date" :invalid="!!errors.hireDate" /></FormField>
        <FormField label="Health insurance (monthly)" for="healthInsurance" :error="errors.healthInsurance">
          <InputNumber v-model="form.healthInsurance" input-id="healthInsurance" mode="currency" currency="USD" locale="en-US" :min="0" />
        </FormField>
      </div>
      <div style="display: flex; gap: 8px; align-items: center">
        <Checkbox v-model="form.pensionOptIn" input-id="pensionOptIn" binary />
        <label for="pensionOptIn">Enrolled in the pension plan (3%)</label>
      </div>
    </form>
    <template #footer>
      <Button label="Cancel" severity="secondary" outlined @click="visible = false" />
      <Button label="Save" type="submit" form="employee-form" :loading="busy" />
    </template>
  </Dialog>
</template>
