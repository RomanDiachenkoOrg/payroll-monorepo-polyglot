<script setup>
import Tag from "primevue/tag";
import { statusLabel, statusSeverity } from "@/utils/format";

defineProps({ status: { type: String, required: true } });
</script>

<template>
  <Tag :value="statusLabel(status)" :severity="statusSeverity(status)" />
</template>
