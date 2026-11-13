<script setup>
defineProps({ title: { type: String, required: true }, subtitle: { type: String, default: "" } });
</script>

<template>
  <div class="page-title">
    <div>
      <h1>{{ title }}</h1>
      <div v-if="subtitle" class="muted">{{ subtitle }}</div>
    </div>
    <div class="no-print" style="display: flex; gap: 8px"><slot /></div>
  </div>
</template>
