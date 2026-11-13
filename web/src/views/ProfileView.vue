<script setup>
import Button from "primevue/button";
import Checkbox from "primevue/checkbox";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import InputText from "primevue/inputtext";
import { onMounted, ref } from "vue";
import { http } from "@/api/http";
import FormField from "@/components/FormField.vue";
import PageHeader from "@/components/PageHeader.vue";
import { useApiCall } from "@/composables/useApiCall";
import { money, shortDate } from "@/utils/format";

const { busy, run } = useApiCall();
const p = ref(null);
const phone = ref("");
const pension = ref(false);
const phoneError = ref("");

async function load() {
  p.value = await http.get("/api/me/profile");
  phone.value = p.value.phone ?? "";
  pension.value = p.value.pensionOptIn;
}
onMounted(load);

async function save() {
  phoneError.value = phone.value && !/^[+\d\s()-]{5,40}$/.test(phone.value) ? "Enter a valid phone number" : "";
  if (phoneError.value) return;
  await run(() => http.put("/api/me/profile", { phone: phone.value || null, pensionOptIn: pension.value }), { success: "Profile updated" });
  load();
}
</script>

<template>
  <template v-if="p">
    <PageHeader :title="p.fullName" :subtitle="`${p.title} · ${p.departmentName}`" />
    <section class="panel">
      <h2>Employment</h2>
      <dl class="dl">
        <dt>Email</dt><dd>{{ p.email }}</dd>
        <dt>Hire date</dt><dd>{{ shortDate(p.hireDate) }}</dd>
        <dt>Pay</dt><dd>{{ p.payType === "SALARIED" ? `${money(p.annualSalary)} per year` : `${money(p.hourlyRate)} per hour` }}</dd>
      </dl>
    </section>
    <section class="panel" style="max-width: 520px">
      <h2>Contact and pension</h2>
      <form novalidate @submit.prevent="save">
        <FormField label="Phone" for="profile-phone" :error="phoneError"><InputText id="profile-phone" v-model="phone" /></FormField>
        <div style="display: flex; gap: 8px; align-items: center; margin-bottom: 12px">
          <Checkbox v-model="pension" input-id="profile-pension" binary />
          <label for="profile-pension">Contribute 3% of gross pay to the pension plan</label>
        </div>
        <Button type="submit" label="Save" :loading="busy" />
      </form>
    </section>
    <section class="panel">
      <h2>Salary history</h2>
      <DataTable :value="p.salaryHistory" size="small">
        <Column header="Effective"><template #body="{ data }">{{ shortDate(data.effectiveDate) }}</template></Column>
        <Column header="Amount" class="num"><template #body="{ data }">{{ data.annualSalary ? `${money(data.annualSalary)}/yr` : `${money(data.hourlyRate)}/h` }}</template></Column>
        <Column field="reason" header="Reason" />
      </DataTable>
    </section>
  </template>
</template>
