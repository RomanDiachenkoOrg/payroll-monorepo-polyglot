<script setup>
defineProps({
  label: { type: String, required: true },
  for: { type: String, required: true },
  error: { type: String, default: "" },
  required: Boolean,
});
</script>

<template>
  <div class="field">
    <label :for="$props.for">{{ label }}<span v-if="required" aria-hidden="true" style="color: #b91c1c"> *</span></label>
    <slot />
    <small v-if="error" class="error" role="alert">{{ error }}</small>
  </div>
</template>
