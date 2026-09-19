<script setup>
import { reactive, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { api } from "../api";
import Icon from "../components/Icon.vue";

const router = useRouter();
// A draft and its idempotency key survive a refresh or a lost provider response.
let saved = null;
try {
  saved = JSON.parse(sessionStorage.getItem("factorymind-draft") || "null");
  if (
    saved &&
    (typeof saved.description !== "string" ||
      typeof saved.reference !== "string" ||
      typeof saved.request_id !== "string" ||
      typeof saved.relevant_risk !== "boolean")
  )
    saved = null;
} catch {
  /* Start empty if browser storage is invalid. */
}
const form = reactive(
  saved || {
    description: "",
    reference: "",
    relevant_risk: false,
    request_id: crypto.randomUUID(),
  },
);
const busy = ref(false);
const error = ref("");
const fingerprint = () =>
  JSON.stringify([form.description, form.reference, form.relevant_risk]);
let submittedFingerprint = saved ? fingerprint() : null;
watch(
  form,
  () => {
    try {
      sessionStorage.setItem("factorymind-draft", JSON.stringify(form));
    } catch {
      /* Storage may be disabled. */
    }
  },
  { deep: true },
);

async function submit() {
  if (busy.value) return;
  // An edited retry is a new report; an unchanged retry retains the same key.
  if (submittedFingerprint && submittedFingerprint !== fingerprint())
    form.request_id = crypto.randomUUID();
  submittedFingerprint = fingerprint();
  busy.value = true;
  error.value = "";
  try {
    const incident = await api("/incidents", {
      method: "POST",
      body: JSON.stringify(form),
    });
    try {
      sessionStorage.removeItem("factorymind-draft");
    } catch {
      /* Optional local draft. */
    }
    await router.push(`/ocorrencias/${incident.id}`);
  } catch (err) {
    error.value = err.message;
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <div class="page-heading">
    <div class="eyebrow">NOVO REGISTRO</div>
    <h1>Registrar ocorrência</h1>
    <p>
      Conte o que aconteceu na operação. Depois, confira a área responsável e
      solicite a análise.
    </p>
  </div>
  <div class="new-layout">
    <form class="card incident-form" @submit.prevent="submit" :aria-busy="busy">
      <div class="card-heading">
        <span class="form-heading-icon"><Icon name="file" :size="21" /></span>
        <div>
          <h2>O que você observou?</h2>
          <p>Você pode registrar o problema mesmo sem saber a causa.</p>
        </div>
      </div>
      <fieldset :disabled="busy">
        <div class="field">
          <div class="label-row">
            <label for="description"
              >Descrição do problema <span class="required">*</span></label
            ><span class="character-count"
              >{{ form.description.length }} / 5000</span
            >
          </div>
          <textarea
            id="description"
            v-model="form.description"
            required
            minlength="10"
            maxlength="5000"
            rows="6"
            placeholder="Descreva o que aconteceu e em qual momento da operação."
          ></textarea>
          <p class="field-hint">
            Inclua os sinais que percebeu, como ruído, vibração, defeito ou
            atraso.
          </p>
        </div>
        <div class="field">
          <label for="reference"
            >Máquina, lote ou etapa
            <span class="optional">opcional</span></label
          ><input
            id="reference"
            v-model="form.reference"
            maxlength="160"
            placeholder="Identificação relacionada ao problema"
          />
        </div>
        <label class="risk-option"
          ><input v-model="form.relevant_risk" type="checkbox" /><span
            class="risk-copy"
            ><strong
              ><Icon name="alert" :size="17" /> Esta situação envolve
              risco</strong
            ><span
              >Marque se a ocorrência exige atenção especial da equipe.</span
            ></span
          ></label
        >
      </fieldset>
      <div v-if="error" class="message error" role="alert">
        <Icon name="alert" /><span>{{ error }}</span>
      </div>
      <div class="form-bottom">
        <span
          ><Icon name="check" :size="16" /> O relato é salvo antes da
          classificação.</span
        ><button class="button primary" :disabled="busy" type="submit">
          <span v-if="busy" class="spinner"></span
          >{{ busy ? "Salvando relato…" : "Salvar e continuar"
          }}<Icon v-if="!busy" name="arrow" :size="18" />
        </button>
      </div>
    </form>
    <aside class="context-column">
      <section class="writing-guide">
        <span class="aside-kicker">PARA UM BOM REGISTRO</span>
        <h2>Alguns detalhes ajudam.</h2>
        <p>Não precisa escrever muito. Comece pelo que você viu.</p>
        <ul>
          <li>
            <span>Quando</span>
            <p>Em que momento o problema apareceu?</p>
          </li>
          <li>
            <span>Onde</span>
            <p>Em qual máquina, lote ou operação?</p>
          </li>
          <li>
            <span>O que mudou</span>
            <p>O que estava diferente do funcionamento habitual?</p>
          </li>
        </ul>
      </section>
      <section class="routing-guide">
        <h3>Áreas de atendimento</h3>
        <div>
          <Icon name="machine" :size="19" />
          <p>
            <strong>Produção e equipamentos</strong
            ><span>Condição e funcionamento das máquinas</span>
          </p>
        </div>
        <div>
          <Icon name="quality" :size="19" />
          <p>
            <strong>Qualidade</strong
            ><span>Defeitos e especificações do produto</span>
          </p>
        </div>
        <div>
          <Icon name="flow" :size="19" />
          <p>
            <strong>Processos industriais</strong
            ><span>Filas, perdas e fluxo de produção</span>
          </p>
        </div>
      </section>
      <div class="history-shortcut">
        <Icon name="history" :size="18" />
        <div>
          <p>Já registrou esse problema?</p>
          <RouterLink to="/historico"
            >Encontrar no histórico <Icon name="arrow" :size="14"
          /></RouterLink>
        </div>
      </div>
    </aside>
  </div>
</template>
