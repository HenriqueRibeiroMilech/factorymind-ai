<script setup>
import { ref } from "vue";
import { useRoute } from "vue-router";
import Icon from "./components/Icon.vue";
import HelpDialog from "./components/HelpDialog.vue";

const route = useRoute();
const helpOpen = ref(false);
</script>

<template>
  <a href="#main" class="skip-link">Pular para o conteúdo</a>
  <header class="app-header">
    <RouterLink to="/" class="brand" aria-label="FactoryMind AI, início">
      <span class="brand-crop"
        ><img
          src="/brand/factorymind-logo.png"
          alt="Factorymind-ai"
          width="2172"
          height="724"
      /></span>
    </RouterLink>
    <nav aria-label="Navegação principal">
      <RouterLink to="/" :class="{ active: route.path === '/' }"
        ><Icon name="plus" :size="18" /><span>Novo relato</span></RouterLink
      >
      <RouterLink
        to="/historico"
        :class="{
          active:
            route.path === '/historico' ||
            route.path.startsWith('/ocorrencias/'),
        }"
        ><Icon name="history" :size="18" /><span>Histórico</span></RouterLink
      >
    </nav>
    <div class="header-actions">
      <button class="help-button" @click="helpOpen = true">
        <Icon name="help" :size="18" /><span>Como funciona</span>
      </button>
    </div>
  </header>
  <div class="app-body">
    <main id="main" tabindex="-1"><RouterView /></main>
    <footer class="page-footer">
      <span
        >FactoryMind AI <span class="footer-dot">/</span> Ocorrências
        industriais</span
      ><span>As análises precisam de revisão da equipe.</span>
    </footer>
  </div>
  <HelpDialog v-if="helpOpen" @close="helpOpen = false" />
</template>
