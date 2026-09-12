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
    <div class="eyebrow"><span></span> REGISTRO DE OCORRÊNCIA</div>
    <h1>O que aconteceu<br />na operação<span class="accent-text">?</span></h1>
    <p>
      Transforme o que você observou em uma análise com contexto.<br
        class="desktop-break"
      />
      Comece pelo relato. Nós ajudamos a organizar o próximo passo.
    </p>
  </div>
  <div class="new-layout">
    <form class="card incident-form" @submit.prevent="submit" :aria-busy="busy">
      <div class="card-heading">
        <span class="section-index">01</span>
        <div>
          <h2>Conte o que você observou</h2>
          <p>Os detalhes fazem diferença na análise.</p>
        </div>
        <Icon name="file" class="muted-icon" :size="23" />
      </div>
      <fieldset :disabled="busy">
        <div class="field">
          <div class="label-row">
            <label for="description"
              >Relato da ocorrência <span class="required">*</span></label
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
            rows="7"
            placeholder="Descreva o problema, em que momento aconteceu e o que você percebeu."
          ></textarea>
          <p class="field-hint">
            Descreva o fato observado, mesmo que a causa ainda seja
            desconhecida.
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
            placeholder="Identificação relacionada à ocorrência"
          />
          <p class="field-hint">
            Use a referência que ajudar a equipe a localizar o problema.
          </p>
        </div>
        <label class="risk-option"
          ><input v-model="form.relevant_risk" type="checkbox" /><span
            class="risk-copy"
            ><strong
              ><Icon name="alert" :size="17" /> Há um risco relevante nesta
              ocorrência</strong
            ><span
              >Sinalize se a situação exige atenção especial da equipe.</span
            ></span
          ></label
        >
      </fieldset>
      <div v-if="error" class="message error" role="alert">
        <Icon name="alert" /><span>{{ error }}</span>
      </div>
      <div class="form-bottom">
        <span
          ><Icon name="check" :size="16" /> Relato salvo antes da
          classificação</span
        ><button class="button primary" :disabled="busy" type="submit">
          <span v-if="busy" class="spinner"></span
          >{{ busy ? "Salvando e classificando…" : "Registrar e classificar"
          }}<Icon v-if="!busy" name="arrow" :size="18" />
        </button>
      </div>
    </form>
    <aside class="context-column">
      <div class="journey-card">
        <span class="small-tag">UM CAMINHO, TRÊS ETAPAS</span>
        <h2>Da observação<br />à próxima ação.</h2>
        <div class="journey-line" aria-hidden="true">
          <span><Icon name="file" :size="20" /></span><i></i
          ><span><Icon name="flow" :size="20" /></span><i></i
          ><span><Icon name="check" :size="20" /></span>
        </div>
        <ol>
          <li>
            <span>01</span>
            <div>
              <strong>O relato encontra a área</strong>
              <p>O Jev classifica o problema para direcionar a análise.</p>
            </div>
          </li>
          <li>
            <span>02</span>
            <div>
              <strong>As evidências entram em cena</strong>
              <p>Documentos e medições apoiam o especialista da área.</p>
            </div>
          </li>
          <li>
            <span>03</span>
            <div>
              <strong>A equipe recebe o contexto</strong>
              <p>Um relatório inicial, com fontes e pontos a verificar.</p>
            </div>
          </li>
        </ol>
        <div class="journey-note">
          <span class="note-line"></span> A decisão continua com a sua equipe.
        </div>
      </div>
      <div class="scope-note">
        <Icon name="book" :size="20" />
        <div>
          <h3>Feito para o chão de fábrica</h3>
          <p>
            Equipamentos, qualidade e processos. Uma ocorrência, com o histórico
            preservado.
          </p>
          <RouterLink to="/historico"
            >Consultar histórico <Icon name="arrow" :size="15"
          /></RouterLink>
        </div>
      </div>
    </aside>
  </div>
  <div class="area-strip">
    <span>CONTEXTO PARA CADA ÁREA</span>
    <div><Icon name="machine" :size="18" /> Produção e equipamentos</div>
    <div><Icon name="quality" :size="18" /> Qualidade</div>
    <div><Icon name="flow" :size="18" /> Processos industriais</div>
  </div>
</template>
