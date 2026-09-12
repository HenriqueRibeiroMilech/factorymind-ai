<script setup>
defineProps({ name: String, size: { type: [Number, String], default: 20 } });
const paths = {
  plus: "M12 5v14M5 12h14",
  arrow: "M4 12h16m-6-6 6 6-6 6",
  back: "M20 12H4m6-6-6 6 6 6",
  history: "M3 12a9 9 0 1 0 3-6.7L3 8m0-5v5h5m4-1v5l3 2",
  help: "M9.1 9a3 3 0 0 1 5.8 1c0 2-3 2-3 4m0 3h.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0",
  close: "m6 6 12 12M6 18 18 6",
  check: "m5 12 4 4L19 6",
  file: "M14 3H5v18h14V8l-5-5v5h5M8 12h8m-8 4h6",
  machine: "M3 20V9l6-4v6l6-4v13M19 20V3h3v17M1 20h22M6 15h1m3 0h1",
  quality: "m12 3 8 4v5c0 5-8 9-8 9s-8-4-8-9V7l8-4Zm-4 9 3 3 5-6",
  flow: "M4 4h6v6H4V4Zm10 10h6v6h-6v-6ZM10 7h7v7M7 10v7h7",
  alert: "m12 3 10 18H2L12 3Zm0 6v5m0 3h.01",
  search: "M21 21l-5-5M18 10a8 8 0 1 1-16 0 8 8 0 0 1 16 0",
  book: "M12 5c-3-2-6-2-10-1v15c4-1 7-1 10 1 3-2 6-2 10-1V4c-4-1-7-1-10 1Zm0 0v15",
  clock: "M12 7v5l3 2m6-2a9 9 0 1 1-18 0 9 9 0 0 1 18 0",
  refresh: "M20 7a9 9 0 1 0 1 7M20 2v5h-5",
  chevron: "m9 5 7 7-7 7",
};
</script>

<template>
  <svg
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    stroke-width="1.65"
    stroke-linecap="round"
    stroke-linejoin="round"
    aria-hidden="true"
  >
    <path :d="paths[name] || paths.file" />
  </svg>
</template>
