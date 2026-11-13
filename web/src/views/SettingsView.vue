<script setup>
import Button from "primevue/button";
import Column from "primevue/column";
import DataTable from "primevue/datatable";
import InputText from "primevue/inputtext";
import Select from "primevue/select";
import Tab from "primevue/tab";
import TabList from "primevue/tablist";
import TabPanel from "primevue/tabpanel";
import TabPanels from "primevue/tabpanels";
import Tabs from "primevue/tabs";
import { onMounted, reactive, ref, watch } from "vue";
import { http, query } from "@/api/http";
import FormField from "@/components/FormField.vue";
import { useApiCall } from "@/composables/useApiCall";
import { dateTime } from "@/utils/format";

const { busy, run } = useApiCall();
const brackets = ref([]);
const rates = reactive({ social: 0, pension: 0 });
const taxError = ref("");
const users = ref([]);
const audit = ref({ items: [], total: 0 });
const facets = ref({ entities: [], actions: [] });
const auditFilter = reactive({ entity: null, action: null, q: "", page: 1, pageSize: 25 });

async function loadTax() {
  const t = await http.get("/api/settings/tax");
  brackets.value = t.brackets.map((b) => ({ lower: b.lower, upper: b.upper ?? "", rate: +(b.rate * 100).toFixed(2) }));
  rates.social = +(t.socialRate * 100).toFixed(2);
  rates.pension = +(t.pensionRate * 100).toFixed(2);
}

async function saveTax() {
  taxError.value = "";
  const body = {
    brackets: brackets.value.map((b) => ({ lower: Number(b.lower), upper: b.upper === "" || b.upper === null ? null : Number(b.upper), rate: Number(b.rate) / 100 })),
    socialRate: Number(rates.social) / 100,
    pensionRate: Number(rates.pension) / 100,
  };
  const ok = await run(() => http.put("/api/settings/tax", body), { success: "Tax settings saved", onError: (e) => (taxError.value = e.fieldErrors?.brackets ?? e.message) });
  if (ok) loadTax();
}

async function loadAudit() {
  audit.value = await http.get(`/api/audit${query(auditFilter)}`);
}

let timer;
watch(
  () => [auditFilter.entity, auditFilter.action, auditFilter.q],
  () => {
    clearTimeout(timer);
    timer = setTimeout(() => {
      auditFilter.page = 1;
      loadAudit();
    }, 250);
  },
);

onMounted(async () => {
  loadTax();
  loadAudit();
  [users.value, facets.value] = await Promise.all([http.get("/api/users"), http.get("/api/audit/facets")]);
});

function onAuditPage(e) {
  auditFilter.page = e.page + 1;
  loadAudit();
}
</script>

<template>
  <h1>Settings</h1>
  <Tabs value="tax">
    <TabList>
      <Tab value="tax">Tax &amp; rates</Tab>
      <Tab value="users">Users</Tab>
      <Tab value="audit">Audit log</Tab>
    </TabList>
    <TabPanels>
      <TabPanel value="tax">
        <p class="muted">Monthly income tax brackets. Changes apply to the next calculation.</p>
        <p v-if="taxError" class="error" role="alert">{{ taxError }}</p>
        <table class="payslip-table" style="max-width: 640px">
          <thead><tr><th>From (USD)</th><th>To (USD)</th><th>Rate (%)</th><th /></tr></thead>
          <tbody>
            <tr v-for="(b, i) in brackets" :key="i">
              <td><InputText v-model="b.lower" type="number" :aria-label="`Bracket ${i + 1} from`" /></td>
              <td><InputText v-model="b.upper" type="number" placeholder="no limit" :aria-label="`Bracket ${i + 1} to`" /></td>
              <td><InputText v-model="b.rate" type="number" :aria-label="`Bracket ${i + 1} rate`" /></td>
              <td><Button icon="pi pi-trash" text severity="danger" :disabled="brackets.length === 1" :aria-label="`Remove bracket ${i + 1}`" @click="brackets.splice(i, 1)" /></td>
            </tr>
          </tbody>
        </table>
        <Button label="Add bracket" icon="pi pi-plus" text @click="brackets.push({ lower: brackets.at(-1)?.upper ?? 0, upper: '', rate: 0 })" />
        <div class="form-grid" style="max-width: 420px; margin-top: 12px">
          <FormField label="Social contribution (%)" for="social-rate"><InputText id="social-rate" v-model="rates.social" type="number" /></FormField>
          <FormField label="Pension (%)" for="pension-rate"><InputText id="pension-rate" v-model="rates.pension" type="number" /></FormField>
        </div>
        <Button label="Save settings" :loading="busy" @click="saveTax" />
      </TabPanel>
      <TabPanel value="users">
        <DataTable :value="users" size="small">
          <Column field="name" header="Name" />
          <Column field="email" header="Email" />
          <Column field="role" header="Role" />
          <Column field="department" header="Department" />
          <Column header="Last login"><template #body="{ data }">{{ dateTime(data.lastLoginAt) }}</template></Column>
          <Column header="Active"><template #body="{ data }">{{ data.active ? "Yes" : "No" }}</template></Column>
        </DataTable>
      </TabPanel>
      <TabPanel value="audit">
        <div class="toolbar">
          <div class="field"><label for="audit-entity">Entity</label><Select v-model="auditFilter.entity" input-id="audit-entity" :options="facets.entities" placeholder="All" show-clear /></div>
          <div class="field"><label for="audit-action">Action</label><Select v-model="auditFilter.action" input-id="audit-action" :options="facets.actions" placeholder="All" show-clear /></div>
          <div class="field"><label for="audit-q">Search</label><InputText id="audit-q" v-model="auditFilter.q" placeholder="User or details" /></div>
        </div>
        <DataTable :value="audit.items" lazy paginator :rows="auditFilter.pageSize" :total-records="audit.total" size="small" @page="onAuditPage">
          <Column header="When"><template #body="{ data }">{{ dateTime(data.createdAt) }}</template></Column>
          <Column field="userEmail" header="User" />
          <Column field="action" header="Action" />
          <Column header="Entity"><template #body="{ data }">{{ data.entity }}{{ data.entityId ? ` #${data.entityId}` : "" }}</template></Column>
          <Column field="details" header="Details" />
        </DataTable>
      </TabPanel>
    </TabPanels>
  </Tabs>
</template>
