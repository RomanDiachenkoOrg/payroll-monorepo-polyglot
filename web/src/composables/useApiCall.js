import { useToast } from "primevue/usetoast";
import { ref } from "vue";

/** Runs an async API action, tracking busy state and showing a toast on failure. */
export function useApiCall() {
  const toast = useToast();
  const busy = ref(false);

  async function run(fn, { success, onError } = {}) {
    busy.value = true;
    try {
      const result = await fn();
      if (success) toast.add({ severity: "success", summary: success, life: 3000 });
      return result;
    } catch (err) {
      if (onError) onError(err);
      else toast.add({ severity: "error", summary: "Error", detail: err.message, life: 5000 });
      return undefined;
    } finally {
      busy.value = false;
    }
  }

  return { busy, run, toast };
}
