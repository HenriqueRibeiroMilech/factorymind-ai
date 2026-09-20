<script setup>
import { computed, onUnmounted, reactive, ref, watch } from "vue";
import { api, categories, formatDate, measurementFields } from "../api";
import Icon from "../components/Icon.vue";
import StatusBadge from "../components/StatusBadge.vue";
import IncidentReport from "../components/IncidentReport.vue";

const props = defineProps({ id: String });
const incident = ref(null);
const loading = ref(true);
const busy = ref(false);
const error = ref("");
const success = ref("");
const showReview = ref(false);
const reviewCategory = ref("");
const justification = ref("");
const form = reactive({ complement: "", hasReadings: false, measurements: {} });
const locked = computed(
  () =>
    busy.value ||
    ["triaging", "analyzing", "completed"].includes(incident.value?.status),
);
const canAnalyze = computed(() =>
  ["ready", "analysis_failed"].includes(incident.value?.status),
);
let serial = 0;
let initialized = false;
onUnmounted(() => serial++);

watch(
  () => props.id,
  () => load(true),
  { immediate: true },
);
watch(
  form,
  () => {
    if (!initialized || incident.value?.status === "completed") return;
    try {
      sessionStorage.setItem(`factorymind-${props.id}`, JSON.stringify(form));
    } catch {
      /* Browser storage is optional. */
    }
  },
  { deep: true },
);

async function load(hydrate = false) {
  const request = ++serial;
  loading.value = true;
  error.value = "";
  try {
    const record = await api(`/incidents/${props.id}`);
    if (request !== serial) return;
    incident.value = record;
    reviewCategory.value = record.category || "";
    showReview.value = false;
    if (hydrate) {
      initialized = false;
      form.complement = record.complement;
      form.hasReadings = Boolean(record.measurements);
      form.measurements = { ...record.measurements };
      if (record.status !== "completed") {
        try {
          const draft = JSON.parse(
            sessionStorage.getItem(`factorymind-${props.id}`) || "null",
          );
          if (draft) Object.assign(form, draft);
        } catch {
          /* Preserve the saved server data if the draft is invalid. */
        }
      }
      initialized = true;
    }
  } catch (err) {
    if (request === serial) error.value = err.message;
  } finally {
    if (request === serial) loading.value = false;
  }
}

async function action(callback) {
  if (busy.value) return;
  busy.value = true;
  error.value = "";
  success.value = "";
  try {
    await callback();
  } catch (err) {
    error.value = err.message;
    if (err.fields?.length)
      error.value +=
        " " +
        err.fields
          .map(
            (field) =>
              measurementFields.find((item) => field.field.endsWith(item.key))
                ?.label || field.field,
          )
          .join(", ");
  } finally {
    busy.value = false;
  }
}

function retryTriage() {
  action(async () => {
    incident.value = await api(`/incidents/${props.id}/triage`, {
      method: "POST",
    });
    reviewCategory.value = incident.value.category || "";
    showReview.value = false;
  });
}

function openReview() {
  reviewCategory.value = incident.value.category;
  showReview.value = true;
}

function confirmCategory() {
  submitReview(
    incident.value.category,
    "Categoria sugerida confirmada pela equipe.",
  );
}

function saveReview() {
  submitReview(reviewCategory.value, justification.value);
}

function submitReview(category, note) {
  action(async () => {
    const unchanged = category === incident.value.category;
    const record = await api(`/incidents/${props.id}/review`, {
      method: "POST",
      body: JSON.stringify({ category, justification: note }),
    });
    incident.value = record;
    if (record.category !== "equipment") {
      form.hasReadings = false;
      form.measurements = {};
    }
    showReview.value = false;
    justification.value = "";
    success.value = unchanged
      ? "Categoria confirmada. Você já pode solicitar a análise."
      : "Categoria corrigida e justificativa salva. Você já pode solicitar a análise.";
  });
}

async function saveContext() {
  const measurements =
    incident.value.category === "equipment" && form.hasReadings
      ? form.measurements
      : null;
  incident.value = await api(`/incidents/${props.id}/context`, {
    method: "PATCH",
    body: JSON.stringify({ complement: form.complement, measurements }),
  });
  try {
    sessionStorage.removeItem(`factorymind-${props.id}`);
  } catch {
    /* Optional local draft. */
  }
}

function submit(event) {
  const analyze = event.submitter?.value === "analyze";
  action(async () => {
    await saveContext();
    if (analyze) {
      incident.value = await api(`/incidents/${props.id}/analyze`, {
        method: "POST",
      });
      if (incident.value.status === "completed") {
        try {
          sessionStorage.removeItem(`factorymind-${props.id}`);
        } catch {
          /* Optional local draft. */
        }
        success.value =
          "Relatório salvo. Você pode consultá-lo novamente pelo Histórico.";
      }
    } else {
      success.value = "Informações salvas nesta ocorrência.";
    }
  });
}
</script>

<template>
  <RouterLink class="back-link" to="/historico"
    ><Icon name="back" :size="16" /> Voltar ao histórico</RouterLink
  >
  <div v-if="loading" class="loading-state" role="status">
    <span class="spinner"></span> Abrindo ocorrência…
  </div>
  <div v-if="error" class="message error" role="alert">
    <Icon name="alert" /><span>{{ error }}</span
    ><button v-if="!incident" class="text-button" @click="load(true)">
      Tentar novamente
    </button>
  </div>
  <template v-if="incident && !loading">
    <div class="page-heading detail-heading">
      <div>
        <div class="eyebrow">
          FM · {{ incident.id.slice(0, 8).toUpperCase() }}
        </div>
        <h1>
          {{
            incident.status === "completed"
              ? "Relatório da ocorrência"
              : "Detalhes da ocorrência"
          }}
        </h1>
        <p>
          Registrada em {{ formatDate(incident.created_at) }}
          <span v-if="incident.reference">· {{ incident.reference }}</span>
        </p>
      </div>
      <StatusBadge :status="incident.status" />
    </div>
    <div v-if="success" class="message success" role="status">
      <Icon name="check" /><span>{{ success }}</span>
    </div>
    <div v-if="incident.last_error" class="message error" role="alert">
      <Icon name="alert" />
      <div>
        <strong>A ocorrência está salva.</strong>
        <p>{{ incident.last_error.message }}</p>
      </div>
    </div>
    <IncidentReport v-if="incident.report" :report="incident.report" />
    <template v-else>
      <div class="progress-track" aria-label="Progresso da ocorrência">
        <div class="done">
          <span><Icon name="check" :size="14" /></span> Relato salvo
        </div>
        <i></i>
        <div :class="incident.category ? 'done' : 'current'">
          <span>{{ incident.category ? "✓" : "2" }}</span> Classificação
        </div>
        <i></i>
        <div :class="incident.category ? 'current' : ''">
          <span>3</span> Análise e relatório
        </div>
      </div>
      <div class="detail-layout">
        <div class="detail-main">
          <section class="card section-card original-card">
            <div class="section-title">
              <span class="section-index">01</span>
              <h2>Relato original</h2>
              <span v-if="incident.relevant_risk" class="risk-tag"
                ><Icon name="alert" :size="14" /> Risco sinalizado</span
              >
            </div>
            <blockquote>{{ incident.description }}</blockquote>
            <p class="field-hint">
              Este texto é preservado. Novas informações entram como
              complemento.
            </p>
          </section>
          <section v-if="!incident.category" class="card section-card">
            <div class="section-title">
              <span class="section-index">02</span>
              <h2>Classificação do relato</h2>
            </div>
            <p>
              O Jev precisa classificar o problema para direcionar a análise à
              área responsável.
            </p>
            <button
              v-if="!locked"
              class="button primary"
              :disabled="busy"
              @click="retryTriage"
            >
              <span v-if="busy" class="spinner"></span
              ><Icon v-else name="refresh" :size="18" /> Tentar classificação
              novamente
            </button>
          </section>
          <section v-if="incident.category" class="card section-card">
            <div class="section-title">
              <span class="section-index">02</span>
              <h2>Área responsável</h2>
            </div>
            <div class="category-result">
              <span class="category-icon"
                ><Icon :name="categories[incident.category].icon" :size="24"
              /></span>
              <div>
                <h3>{{ categories[incident.category].label }}</h3>
                <p>{{ categories[incident.category].area }}</p>
              </div>
            </div>
            <div class="classification-meta">
              <span
                >Sugestão do Jev:
                <strong>{{
                  categories[incident.suggested_category]?.label
                }}</strong></span
              ><span
                >Confiança:
                {{
                  incident.confidence === null
                    ? "não informada"
                    : `${(incident.confidence * 100).toFixed(1)}%`
                }}</span
              >
            </div>
            <div v-if="incident.review" class="review-saved">
              <Icon name="check" :size="17" />
              <div>
                <strong>Decisão da equipe registrada</strong>
                <p>{{ incident.review.justification }}</p>
                <small>{{ formatDate(incident.review.reviewed_at) }}</small>
              </div>
            </div>
            <div
              v-if="incident.status === 'review_required'"
              class="message warning"
            >
              <Icon name="alert" /><span>{{
                incident.relevant_risk
                  ? "Você sinalizou risco. Se a área estiver correta, confirme a categoria para continuar. Para corrigir, clique em Revisar categoria."
                  : "A confiança está baixa ou não foi informada. Se a sugestão estiver correta, confirme a categoria. Para corrigir, clique em Revisar categoria."
              }}</span>
            </div>
            <div v-if="!showReview && !locked" class="category-actions">
              <button
                v-if="incident.status === 'review_required'"
                type="button"
                class="button primary"
                @click="confirmCategory"
              >
                Confirmar categoria <Icon name="check" :size="17" />
              </button>
              <button
                type="button"
                class="text-button review-toggle"
                @click="openReview"
              >
                {{
                  incident.review
                    ? "Ajustar decisão da equipe"
                    : "Revisar categoria"
                }}
                <Icon name="arrow" :size="15" />
              </button>
            </div>
            <form
              v-if="showReview"
              class="review-form"
              @submit.prevent="saveReview"
            >
              <fieldset :disabled="locked">
                <div class="field">
                  <label for="category">Categoria confirmada pela equipe</label
                  ><select id="category" v-model="reviewCategory" required>
                    <option
                      v-for="(category, key) in categories"
                      :key="key"
                      :value="key"
                    >
                      {{ category.label }}
                    </option>
                  </select>
                </div>
                <div class="field">
                  <label for="justification">Justificativa da revisão</label
                  ><textarea
                    id="justification"
                    v-model="justification"
                    required
                    minlength="8"
                    maxlength="1500"
                    rows="3"
                    placeholder="Explique por que a categoria foi confirmada ou corrigida."
                  ></textarea>
                </div>
                <div class="review-actions">
                  <button
                    type="submit"
                    class="button primary"
                    :disabled="locked"
                  >
                    Salvar revisão <Icon name="check" :size="17" /></button
                  ><button
                    type="button"
                    class="text-button"
                    @click="showReview = false"
                  >
                    Cancelar
                  </button>
                </div>
              </fieldset>
            </form>
          </section>
          <form
            class="card section-card"
            @submit.prevent="submit"
            :aria-busy="busy"
          >
            <div class="section-title">
              <span class="section-index">03</span>
              <h2>Complementar ocorrência</h2>
            </div>
            <fieldset :disabled="locked">
              <div class="field">
                <label for="complement"
                  >Complemento ao relato
                  <span class="optional">opcional</span></label
                ><textarea
                  id="complement"
                  v-model="form.complement"
                  maxlength="5000"
                  rows="4"
                  placeholder="Acrescente informações que ajudem a entender a ocorrência."
                ></textarea>
              </div>
              <div
                v-if="incident.category === 'equipment'"
                class="measurements-section"
              >
                <h3>Leitura do equipamento</h3>
                <p>
                  O modelo utiliza seis medições do mesmo instante. Vibração
                  permanece no relato.
                </p>
                <div class="reading-choices">
                  <label :class="{ selected: !form.hasReadings }"
                    ><input
                      v-model="form.hasReadings"
                      type="radio"
                      :value="false"
                      name="readings"
                    />
                    Não disponho das medições</label
                  ><label :class="{ selected: form.hasReadings }"
                    ><input
                      v-model="form.hasReadings"
                      type="radio"
                      :value="true"
                      name="readings"
                    />
                    Tenho as seis medições</label
                  >
                </div>
                <p v-if="!form.hasReadings" class="field-hint">
                  Você pode continuar. O relatório registrará que o modelo não
                  foi executado.
                </p>
                <div v-else class="measurements-grid">
                  <div class="field">
                    <label for="product_type">Tipo de produto</label
                    ><select
                      id="product_type"
                      v-model="form.measurements.product_type"
                      required
                    >
                      <option :value="undefined" disabled>Selecione</option>
                      <option value="L">L</option>
                      <option value="M">M</option>
                      <option value="H">H</option>
                    </select>
                  </div>
                  <div
                    v-for="field in measurementFields"
                    :key="field.key"
                    class="field"
                  >
                    <label :for="field.key">{{ field.label }}</label>
                    <div class="unit-input">
                      <input
                        :id="field.key"
                        v-model.number="form.measurements[field.key]"
                        type="number"
                        step="any"
                        :min="field.min"
                        :max="field.max"
                        required
                        inputmode="decimal"
                      /><span>{{ field.unit }}</span>
                    </div>
                  </div>
                </div>
              </div>
              <p v-else-if="incident.category" class="inline-note">
                <Icon name="book" :size="17" /> A análise usará o relato e os
                documentos da área. O modelo de equipamentos não se aplica a
                esta categoria.
              </p>
            </fieldset>
            <div class="detail-form-bottom">
              <button
                class="button secondary"
                type="submit"
                value="save"
                :disabled="locked"
              >
                Salvar informações</button
              ><button
                class="button primary"
                type="submit"
                value="analyze"
                :disabled="locked || !canAnalyze"
              >
                <span v-if="busy" class="spinner"></span
                >{{ busy ? "Processando…" : "Gerar análise inicial"
                }}<Icon v-if="!busy" name="arrow" :size="18" />
              </button>
            </div>
            <p v-if="!canAnalyze && !locked" class="field-hint">
              Conclua a classificação e a revisão necessária para gerar a
              análise.
            </p>
          </form>
        </div>
        <aside class="detail-aside">
          <div class="aside-note">
            <Icon name="book" :size="24" />
            <h3>Sobre a análise</h3>
            <p>
              O relatório distingue o que foi observado, o que o modelo calculou
              e o que ainda é hipótese.
            </p>
            <div class="aside-divider"></div>
            <p>
              Os documentos citados ficam disponíveis em trechos para a equipe
              conferir.
            </p>
            <span class="small-tag">CONFIRA AS FONTES DO RELATÓRIO</span>
          </div>
          <div class="record-info">
            <span>ID COMPLETO</span><code>{{ incident.id }}</code>
            <p>Use este registro para retomar o trabalho.</p>
          </div>
        </aside>
      </div>
      <div
        v-if="['triaging', 'analyzing'].includes(incident.status)"
        class="message warning"
      >
        <Icon name="clock" />
        <div>
          <strong>Esta ocorrência está em processamento.</strong>
          <p>
            Atualize a situação para consultar o resultado. Se a tentativa tiver
            sido interrompida, uma nova tentativa será liberada em até três
            minutos.
          </p>
          <button class="text-button" @click="load()">
            Atualizar situação <Icon name="refresh" :size="15" />
          </button>
        </div>
      </div>
    </template>
  </template>
</template>
