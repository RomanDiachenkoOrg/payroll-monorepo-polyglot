<script setup>
import Button from "primevue/button";
import Dialog from "primevue/dialog";
import InputText from "primevue/inputtext";
import Select from "primevue/select";
import Textarea from "primevue/textarea";
import { computed, ref, watch } from "vue";
import { http } from "@/api/http";
import FormField from "@/components/FormField.vue";
import { useApiCall } from "@/composables/useApiCall";
import { addDays, mondayOf } from "@/utils/format";
import { validateHours } from "@/utils/validation";

const props = defineProps({
  timesheet: { type: Object, default: null },
  employees: { type: Array, default: null },
});
const visible = defineModel("visible", { type: Boolean });
const emit = defineEmits(["saved"]);
const { busy, run } = useApiCall();

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
const weekStart = ref(mondayOf());
const hours = ref([8, 8, 8, 8, 8, 0, 0]);
const notes = ref("");
const employeeId = ref(null);
const errors = ref({});

watch(visible, (open) => {
  if (!open) return;
  errors.value = {};
  weekStart.value = props.timesheet?.weekStart ?? mondayOf();
  hours.value = [...(props.timesheet?.hours ?? [8, 8, 8, 8, 8, 0, 0])];
  notes.value = props.timesheet?.notes ?? "";
  employeeId.value = null;
});

const total = computed(() => hours.value.reduce((a, h) => a + (Number(h) || 0), 0));

async function save(submit) {
  errors.value = {};
  const hoursError = validateHours(hours.value);
  if (hoursError) errors.value.hours = hoursError;
  if (new Date(`${weekStart.value}T00:00:00Z`).getUTCDay() !== 1) errors.value.weekStart = "The week must start on a Monday";
  if (props.employees && !employeeId.value) errors.value.employeeId = "Select an employee";
  if (submit && total.value <= 0) errors.value.hours = "Enter at least one hour before submitting";
  if (Object.keys(errors.value).length) return;

  const body = { hours: hours.value.map(Number), notes: notes.value || null };
  const saved = await run(
    async () => {
      const t = props.timesheet
        ? await http.put(`/api/timesheets/${props.timesheet.id}`, body)
        : await http.post("/api/timesheets", { ...body, weekStart: weekStart.value, employeeId: employeeId.value });
      return submit ? http.post(`/api/timesheets/${t.id}/submit`) : t;
    },
    { success: submit ? "Timesheet submitted" : "Timesheet saved", onError: (e) => (errors.value = { ...e.fieldErrors, _: e.message }) },
  );
  if (saved) {
    visible.value = false;
    emit("saved", saved);
  }
}
</script>

<template>
  <Dialog v-model:visible="visible" modal :header="timesheet ? 'Edit timesheet' : 'New timesheet'" :style="{ width: '640px' }">
    <p v-if="errors._" class="error" role="alert">{{ errors._ }}</p>
    <p v-if="timesheet?.rejectReason" class="muted">Returned: {{ timesheet.rejectReason }}</p>
    <FormField v-if="employees" label="Employee" for="ts-employee" :error="errors.employeeId" required>
      <Select v-model="employeeId" input-id="ts-employee" :options="employees" option-label="name" option-value="id" filter placeholder="Select..." />
    </FormField>
    <FormField label="Week starting (Monday)" for="ts-week" :error="errors.weekStart" required>
      <InputText id="ts-week" v-model="weekStart" type="date" :disabled="!!timesheet" />
    </FormField>
    <div class="hours">
      <div v-for="(d, i) in DAYS" :key="d" class="field">
        <label :for="`ts-h${i}`">{{ d }} <span class="muted">{{ addDays(weekStart, i).slice(5) }}</span></label>
        <input :id="`ts-h${i}`" v-model="hours[i]" type="number" min="0" max="24" step="0.5" class="p-inputtext" />
      </div>
    </div>
    <small v-if="errors.hours" class="error" role="alert">{{ errors.hours }}</small>
    <p>Total: <strong>{{ total }} h</strong><span v-if="total > 40" class="muted"> ({{ total - 40 }} h overtime)</span></p>
    <FormField label="Notes" for="ts-notes"><Textarea id="ts-notes" v-model="notes" rows="2" /></FormField>
    <template #footer>
      <Button label="Cancel" severity="secondary" text @click="visible = false" />
      <Button label="Save draft" severity="secondary" outlined :loading="busy" @click="save(false)" />
      <Button label="Save and submit" :loading="busy" @click="save(true)" />
    </template>
  </Dialog>
</template>
