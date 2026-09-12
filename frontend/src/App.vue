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
  <aside class="sidebar">
    <RouterLink to="/" class="brand" aria-label="FactoryMind AI, início"
      ><span class="brand-symbol"><Icon name="machine" :size="27" /></span
      ><span>FactoryMind<span class="brand-ai">AI</span></span></RouterLink
    >
    <div class="workspace-label">WORKSPACE <span>INDUSTRIAL</span></div>
    <nav aria-label="Navegação principal">
      <RouterLink
        to="/"
        :class="{
          active: route.path === '/' || route.path.startsWith('/ocorrencias/'),
        }"
        ><Icon name="plus" /><span>Novo relato</span
        ><Icon name="chevron" :size="14" class="nav-chevron"
      /></RouterLink>
      <RouterLink
        to="/historico"
        :class="{ active: route.path === '/historico' }"
        ><Icon name="history" /><span>Histórico</span></RouterLink
      >
    </nav>
    <div class="sidebar-bottom">
      <div class="sidebar-grid" aria-hidden="true">
        <i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i><i></i>
      </div>
      <p>Mais contexto.<br /><strong>Melhores decisões.</strong></p>
      <span>INTELIGÊNCIA NA OPERAÇÃO</span>
      <div class="portfolio-label"><span></span> Projeto de portfólio</div>
    </div>
  </aside>
  <div class="app-body">
    <header class="topbar">
      <div>
        <span class="topbar-line"></span> OPERAÇÃO INDUSTRIAL
        <span class="topbar-separator">/</span
        ><span class="topbar-context">{{
          route.path === "/historico"
            ? "Histórico"
            : route.path.startsWith("/ocorrencias/")
              ? "Ocorrência"
              : "Novo relato"
        }}</span>
      </div>
      <button class="help-button" @click="helpOpen = true">
        <Icon name="help" :size="18" /><span>Como funciona</span>
      </button>
    </header>
    <main id="main" tabindex="-1"><RouterView /></main>
    <footer class="page-footer">
      <span
        >FactoryMind AI <span class="footer-dot">·</span> Contexto para
        decidir.</span
      ><span>Análise inicial com revisão humana</span>
    </footer>
  </div>
  <HelpDialog v-if="helpOpen" @close="helpOpen = false" />
</template>
