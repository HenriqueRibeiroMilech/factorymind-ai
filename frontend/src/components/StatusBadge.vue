<script setup>
import { statuses } from "../api";
defineProps({ status: String });
</script>
<template>
  <span class="status-badge" :class="statuses[status]?.tone"
    ><span class="status-dot"></span
    >{{ statuses[status]?.label || status }}</span
  >
</template>
