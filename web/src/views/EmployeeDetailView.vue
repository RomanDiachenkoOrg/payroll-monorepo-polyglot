<script setup>
import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import Dialog from "primevue/dialog";
import InputNumber from "primevue/inputnumber";
import InputText from "primevue/inputtext";
import { onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import { http } from "@/api/http";
import EmployeeForm from "@/components/EmployeeForm.vue";
import FormField from "@/components/FormField.vue";
import PageHeader from "@/components/PageHeader.vue";
import StatusTag from "@/components/StatusTag.vue";
import { useApiCall } from "@/composables/useApiCall";
import { useAuthStore } from "@/stores/auth";
import { isoToday, money, period, shortDate } from "@/utils/format";

const route = useRoute();
const auth = useAuthStore();
const { busy, run } = useApiCall();
const emp = ref(null);
const departments = ref([]);
const showEdit = ref(false);
const showRaise = ref(false);
const raise = reactive({ amount: null, effectiveDate: isoToday(), reason: "Annual review" });
const raiseErrors = ref({});

async function load() {
  emp.value = await http.get(`/api/employees/${route.params.id}`);
}

onMounted(async () => {
  departments.value = await http.get("/api/departments");
  load();
});

async function saveRaise() {
  raiseErrors.value = {};
  if (!(raise.amount > 0)) raiseErrors.value.amount = "Amount must be greater than 0";
  if (!raise.reason?.trim()) raiseErrors.value.reason = "Reason is required";
  if (Object.keys(raiseErrors.value).length) return;
  const ok = await run(() => http.post(`/api/employees/${emp.value.id}/salary`, { ...raise }), {
    success: "Salary change saved",
    onError: (e) => (raiseErrors.value = Object.keys(e.fieldErrors).length ? e.fieldErrors : { amount: e.message }),
  });
  if (ok) {
    showRaise.value = false;
    load();
  }
}
</script>

<template>
  <template v-if="emp">
    <PageHeader :title="emp.fullName" :subtitle="`${emp.title} · ${emp.departmentName}`">
      <template v-if="auth.isAdmin">
        <Button label="Add raise" icon="pi pi-arrow-up" severity="secondary" outlined @click="showRaise = true" />
        <Button label="Edit" icon="pi pi-pencil" @click="showEdit = true" />
      </template>
    </PageHeader>
    <section class="panel">
      <h2>Profile <StatusTag :status="emp.status" /></h2>
      <dl class="dl">
        <dt>Email</dt><dd>{{ emp.email }}</dd>
        <dt>Phone</dt><dd>{{ emp.phone || "-" }}</dd>
        <dt>Hire date</dt><dd>{{ shortDate(emp.hireDate) }}</dd>
        <dt>Pay</dt><dd>{{ emp.payType === "SALARIED" ? `${money(emp.annualSalary)} per year` : `${money(emp.hourlyRate)} per hour` }}</dd>
        <dt>Pension plan</dt><dd>{{ emp.pensionOptIn ? "Enrolled" : "Not enrolled" }}</dd>
        <dt>Health insurance</dt><dd>{{ money(emp.healthInsurance) }} / month</dd>
      </dl>
    </section>
    <section class="panel">
      <h2>Salary history</h2>
      <DataTable :value="emp.salaryHistory" size="small">
        <Column header="Effective"><template #body="{ data }">{{ shortDate(data.effectiveDate) }}</template></Column>
        <Column header="Amount" class="num"><template #body="{ data }">{{ data.annualSalary ? `${money(data.annualSalary)}/yr` : `${money(data.hourlyRate)}/h` }}</template></Column>
        <Column field="reason" header="Reason" />
      </DataTable>
    </section>
    <section class="panel">
      <h2>Payslips</h2>
      <DataTable :value="emp.payslips" size="small">
        <template #empty>No payslips yet.</template>
        <Column header="Period"><template #body="{ data }"><RouterLink :to="`/payslips/${data.id}`">{{ period(data.periodStart, data.periodEnd) }}</RouterLink></template></Column>
        <Column header="Pay run"><template #body="{ data }"><StatusTag :status="data.payRunStatus" /></template></Column>
        <Column header="Gross" class="num"><template #body="{ data }">{{ money(data.gross) }}</template></Column>
        <Column header="Net" class="num"><template #body="{ data }">{{ money(data.net) }}</template></Column>
      </DataTable>
    </section>
    <EmployeeForm v-model:visible="showEdit" :employee="emp" :departments="departments" @saved="load" />
    <Dialog v-model:visible="showRaise" modal header="Add salary change" :style="{ width: '420px' }">
      <form id="raise-form" novalidate @submit.prevent="saveRaise">
        <FormField :label="emp.payType === 'SALARIED' ? 'New annual salary' : 'New hourly rate'" for="raise-amount" :error="raiseErrors.amount" required>
          <InputNumber v-model="raise.amount" input-id="raise-amount" mode="currency" currency="USD" locale="en-US" />
        </FormField>
        <FormField label="Effective date" for="raise-date" :error="raiseErrors.effectiveDate" required><InputText id="raise-date" v-model="raise.effectiveDate" type="date" /></FormField>
        <FormField label="Reason" for="raise-reason" :error="raiseErrors.reason" required><InputText id="raise-reason" v-model="raise.reason" /></FormField>
      </form>
      <template #footer>
        <Button label="Cancel" severity="secondary" outlined @click="showRaise = false" />
        <Button label="Save" type="submit" form="raise-form" :loading="busy" />
      </template>
    </Dialog>
  </template>
</template>
