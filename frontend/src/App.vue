<script setup>
import { useRoute } from "vue-router";
import Icon from "./components/Icon.vue";
import ProjectGuide from "./components/ProjectGuide.vue";

const route = useRoute();
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
  </header>
  <div class="app-body">
    <main id="main" tabindex="-1"><ProjectGuide /><RouterView /></main>
    <footer class="page-footer">
      <span
        >FactoryMind AI <span class="footer-dot">/</span> Ocorrências
        industriais</span
      ><span>As análises precisam de revisão da equipe.</span>
    </footer>
  </div>
</template>
