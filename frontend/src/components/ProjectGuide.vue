<script setup>
import { ref } from "vue";
import Icon from "./Icon.vue";
import HelpDialog from "./HelpDialog.vue";

const guideSection = ref(null);
const exampleCategory = ref("equipment");
</script>

<template>
  <section class="project-guide" aria-label="Conheça e teste o projeto">
    <div class="project-guide-copy">
      <span class="guide-icon"><Icon name="book" :size="22" /></span>
      <div>
        <h2>Primeira vez por aqui?</h2>
        <p>
          Entenda o machine learning e consulte os exemplos durante a análise.
        </p>
      </div>
    </div>
    <div class="guide-actions">
      <button
        type="button"
        class="guide-button"
        @click="guideSection = 'workflow'"
        aria-haspopup="dialog"
      >
        <Icon name="flow" :size="18" /> Como funciona
      </button>
      <button
        type="button"
        class="guide-button guide-button-primary"
        @click="guideSection = 'examples'"
        aria-haspopup="dialog"
      >
        <Icon name="file" :size="18" /> Exemplos para testar
        <Icon name="arrow" :size="16" />
      </button>
    </div>
  </section>
  <HelpDialog
    v-if="guideSection"
    :section="guideSection"
    :example-category="exampleCategory"
    @example-change="exampleCategory = $event"
    @close="guideSection = null"
  />
</template>
