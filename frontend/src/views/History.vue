<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { api, categories, formatDate } from "../api";
import Icon from "../components/Icon.vue";
import StatusBadge from "../components/StatusBadge.vue";
const query = ref("");
const filter = ref("");
const page = ref(1);
const result = ref({ items: [], total: 0, page_size: 20 });
const loading = ref(true);
const error = ref("");
let serial = 0;
onUnmounted(() => serial++);
async function load(reset = false) {
  if (reset) page.value = 1;
  const request = ++serial;
  loading.value = true;
  error.value = "";
  try {
    const data = await api(
      `/incidents?${new URLSearchParams({ q: query.value.trim(), status: filter.value, page: page.value })}`,
    );
    if (request === serial) result.value = data;
  } catch (err) {
    if (request === serial) error.value = err.message;
  } finally {
    if (request === serial) loading.value = false;
  }
}
onMounted(load);
</script>

<template>
  <div class="page-heading heading-with-action">
    <div>
      <div class="eyebrow"><span></span> REGISTROS DA OPERAÇÃO</div>
      <h1>Ocorrências</h1>
      <p>Consulte os relatórios ou continue uma ocorrência pendente.</p>
    </div>
    <RouterLink to="/" class="button primary"
      ><Icon name="plus" :size="18" /> Novo relato</RouterLink
    >
  </div>
  <section class="card history-card" aria-label="Ocorrências registradas">
    <form class="history-toolbar" @submit.prevent="load(true)">
      <div class="search-field">
        <Icon name="search" :size="19" /><input
          v-model="query"
          aria-label="Buscar ocorrência"
          placeholder="Buscar por relato, identificação ou ID"
          maxlength="200"
        />
      </div>
      <select
        v-model="filter"
        aria-label="Filtrar por situação"
        @change="load(true)"
      >
        <option value="">Todas as situações</option>
        <option value="pending">Pendentes</option>
        <option value="completed">Concluídas</option></select
      ><button class="button secondary" type="submit" :disabled="loading">
        Buscar
      </button>
    </form>
    <div v-if="error" class="message error" role="alert">
      <Icon name="alert" /><span>{{ error }}</span
      ><button class="text-button" @click="load()">Tentar novamente</button>
    </div>
    <div v-if="loading" class="empty-state" role="status">
      <span class="spinner"></span>
      <p>Buscando ocorrências…</p>
    </div>
    <template v-else-if="!error">
      <div v-if="!result.items.length" class="empty-state">
        <span class="empty-icon"><Icon name="history" :size="30" /></span>
        <h2>
          {{
            query || filter
              ? "Nenhuma ocorrência encontrada"
              : "Nenhuma ocorrência registrada"
          }}
        </h2>
        <p>
          {{
            query || filter
              ? "Tente outro termo ou altere o filtro de situação."
              : "Os relatos e as análises salvos aparecerão aqui."
          }}
        </p>
        <RouterLink v-if="!query && !filter" to="/" class="button primary"
          >Registrar primeira ocorrência <Icon name="arrow" :size="18"
        /></RouterLink>
      </div>
      <div v-else>
        <div class="history-table-head">
          <span>OCORRÊNCIA</span><span>ÁREA / SITUAÇÃO</span
          ><span>REGISTRO</span>
        </div>
        <RouterLink
          v-for="item in result.items"
          :key="item.id"
          :to="`/ocorrencias/${item.id}`"
          class="history-row"
          ><div class="history-description">
            <span class="record-id"
              >FM · {{ item.id.slice(0, 8).toUpperCase() }}</span
            >
            <h2>{{ item.description }}</h2>
            <span v-if="item.reference" class="record-reference">{{
              item.reference
            }}</span>
          </div>
          <div class="history-classification">
            <span>{{
              categories[item.category]?.label || "Classificação pendente"
            }}</span
            ><StatusBadge :status="item.status" />
          </div>
          <div class="history-date">
            <span>{{ formatDate(item.created_at) }}</span
            ><Icon name="arrow" :size="18" /></div
        ></RouterLink>
      </div>
      <div class="history-pagination">
        <span
          >{{ result.total }}
          {{ result.total === 1 ? "ocorrência" : "ocorrências" }}</span
        >
        <div>
          <button
            class="text-button"
            :disabled="page === 1"
            @click="
              page--;
              load();
            "
          >
            Anterior</button
          ><span>Página {{ page }}</span
          ><button
            class="text-button"
            :disabled="page * result.page_size >= result.total"
            @click="
              page++;
              load();
            "
          >
            Próxima
          </button>
        </div>
      </div>
    </template>
  </section>
</template>
