<script setup>
import { categories, formatDate, measurementFields } from "../api";
import Icon from "./Icon.vue";
const props = defineProps({ report: Object });
const sourceIndex = (id) =>
  props.report.sources.findIndex((source) => source.id === id) + 1;
const sourceAnchor = (id) => `evidence-${sourceIndex(id)}`;
const percentage = (value) =>
  new Intl.NumberFormat("pt-BR", {
    style: "percent",
    maximumFractionDigits: 2,
  }).format(value);
</script>

<template>
  <article class="report">
    <div class="report-banner">
      <span class="report-banner-icon"><Icon name="check" :size="25" /></span>
      <div>
        <span class="eyebrow">ANÁLISE INICIAL CONCLUÍDA</span>
        <h2>{{ report.responsible_area }}</h2>
        <p>Relatório salvo em {{ formatDate(report.generated_at) }}</p>
      </div>
      <span class="report-stamp">FM / RELATÓRIO</span>
    </div>
    <div v-if="report.review_needed" class="message warning">
      <Icon name="alert" /><span
        >Esta análise indica pontos que precisam de avaliação humana. Consulte
        as limitações e informações pendentes.</span
      >
    </div>
    <div class="report-layout">
      <div class="report-main">
        <section class="card section-card">
          <div class="section-title">
            <span class="section-index">01</span>
            <h2>O problema relatado</h2>
          </div>
          <blockquote>{{ report.original_description }}</blockquote>
          <div v-if="report.complement" class="report-complement">
            <span class="eyebrow">COMPLEMENTO DO OPERADOR</span>
            <p>{{ report.complement }}</p>
          </div>
          <dl class="report-facts">
            <div>
              <dt>Categoria</dt>
              <dd>{{ report.category_label }}</dd>
            </div>
            <div>
              <dt>Identificação</dt>
              <dd>{{ report.reference || "Não informada" }}</dd>
            </div>
            <div>
              <dt>Risco relevante</dt>
              <dd>
                {{
                  report.relevant_risk
                    ? "Sinalizado pelo operador"
                    : "Não sinalizado"
                }}
              </dd>
            </div>
            <div>
              <dt>Sugestão original do Jev</dt>
              <dd>{{ categories[report.triage.suggested_category]?.label }}</dd>
            </div>
            <div>
              <dt>Confiança da classificação</dt>
              <dd>
                {{
                  report.triage.confidence === null
                    ? "Não informada"
                    : percentage(report.triage.confidence)
                }}
              </dd>
            </div>
          </dl>
          <div v-if="report.human_review" class="review-saved">
            <Icon name="check" :size="17" />
            <div>
              <strong>Categoria revisada pela equipe</strong>
              <p>{{ report.human_review.justification }}</p>
            </div>
          </div>
        </section>
        <section class="card section-card">
          <div class="section-title">
            <span class="section-index">02</span>
            <h2>Análise inicial</h2>
          </div>
          <p class="analysis-copy">{{ report.initial_analysis }}</p>
          <h3 class="subsection-title">Hipóteses a verificar</h3>
          <p v-if="!report.hypotheses.length" class="muted">
            Não há hipóteses com informação suficiente nesta análise.
          </p>
          <ol v-else class="findings-list">
            <li v-for="(finding, index) in report.hypotheses" :key="index">
              <span class="finding-index">{{
                String(index + 1).padStart(2, "0")
              }}</span>
              <div>
                <p>{{ finding.text }}</p>
                <div class="citation-links">
                  <a
                    v-for="source in finding.source_ids"
                    :key="source"
                    :href="`#${sourceAnchor(source)}`"
                    ><Icon name="book" :size="13" /> Fonte
                    {{ sourceIndex(source) }}</a
                  ><span v-if="!finding.source_ids.length" class="no-source"
                    >Sem apoio documental · verificar com a equipe</span
                  >
                </div>
              </div>
            </li>
          </ol>
        </section>
        <section class="card section-card ml-section">
          <div class="section-title">
            <span class="section-index">03</span>
            <h2>Condição do equipamento</h2>
            <span class="ml-label">AI4I 2020</span>
          </div>
          <template v-if="report.ml.status === 'available'"
            ><div
              class="ml-decision"
              :class="{ flagged: report.ml.decision === 'failure' }"
            >
              <Icon
                :name="report.ml.decision === 'failure' ? 'alert' : 'machine'"
                :size="24"
              />
              <div>
                <span>DECISÃO DO CLASSIFICADOR</span>
                <h3>
                  {{
                    report.ml.decision === "failure"
                      ? "Condição classificada com falha"
                      : "Condição classificada sem falha"
                  }}
                </h3>
              </div>
            </div>
            <div class="ml-values">
              <div>
                <span>Escore do modelo</span
                ><strong>{{ percentage(report.ml.score) }}</strong>
              </div>
              <div>
                <span>Limiar de decisão</span
                ><strong>{{ percentage(report.ml.threshold) }}</strong>
              </div>
            </div>
            <p class="field-hint">
              Escore não calibrado. A decisão compara o escore ao limiar; não
              estima quando ocorrerá uma quebra.
            </p>
            <h3 class="subsection-title">
              Entradas informadas no mesmo instante
            </h3>
            <dl class="readings-list">
              <div>
                <dt>Tipo de produto</dt>
                <dd>{{ report.ml.inputs.product_type }}</dd>
              </div>
              <div v-for="field in measurementFields" :key="field.key">
                <dt>{{ field.label }}</dt>
                <dd>
                  {{ report.ml.inputs[field.key] }}
                  <span>{{ field.unit }}</span>
                </dd>
              </div>
            </dl>
            <details class="model-details">
              <summary>Versão e valores originais do modelo</summary>
              <code>{{ report.ml.version }}</code>
              <p>
                Escore: {{ report.ml.score }} · Limiar:
                {{ report.ml.threshold }}
              </p>
            </details>
            <div v-if="report.ml.out_of_range.length" class="message warning">
              <Icon name="alert" />
              <div>
                <strong>Leituras fora da faixa do treino</strong>
                <p
                  v-for="warning in report.ml.out_of_range"
                  :key="warning.field"
                >
                  {{
                    measurementFields.find(
                      (field) => field.key === warning.field,
                    )?.label
                  }}: faixa de treino {{ warning.training_min }} a
                  {{ warning.training_max }}.
                </p>
              </div>
            </div></template
          >
          <div v-else class="ml-unavailable">
            <Icon
              :name="report.ml.status === 'not_applicable' ? 'file' : 'machine'"
              :size="25"
            />
            <div>
              <h3>
                {{
                  report.ml.status === "not_applicable"
                    ? "Não aplicável a esta categoria"
                    : "Análise sem leitura do equipamento"
                }}
              </h3>
              <p>{{ report.ml.limitation }}</p>
            </div>
          </div>
          <p v-if="report.ml.status === 'available'" class="ml-limitation">
            {{ report.ml.limitation }} Sintomas como vibração e ruído continuam
            relevantes, mesmo com escore baixo.
          </p>
        </section>
        <section class="card section-card">
          <div class="section-title">
            <span class="section-index">04</span>
            <h2>Recomendações para a equipe</h2>
          </div>
          <p v-if="!report.recommendations.length" class="muted">
            Faltam evidências para recomendações específicas.
          </p>
          <ol class="findings-list recommendations">
            <li v-for="(finding, index) in report.recommendations" :key="index">
              <span class="finding-index"
                ><Icon name="arrow" :size="17"
              /></span>
              <div>
                <p>{{ finding.text }}</p>
                <div class="citation-links">
                  <a
                    v-for="source in finding.source_ids"
                    :key="source"
                    :href="`#${sourceAnchor(source)}`"
                    ><Icon name="book" :size="13" /> Fonte
                    {{ sourceIndex(source) }}</a
                  ><span v-if="!finding.source_ids.length" class="no-source"
                    >Sem apoio documental · verificar com a equipe</span
                  >
                </div>
              </div>
            </li>
          </ol>
        </section>
        <section class="card section-card">
          <div class="section-title">
            <span class="section-index">05</span>
            <h2>O que ainda precisa ser verificado</h2>
          </div>
          <ul class="missing-list">
            <li
              v-for="(item, index) in report.missing_information"
              :key="`missing-${index}`"
            >
              {{ item }}
            </li>
            <li
              v-for="(gap, index) in report.evidence_gaps"
              :key="`gap-${index}`"
            >
              {{ gap }}
            </li>
          </ul>
          <p
            v-if="
              !report.missing_information.length && !report.evidence_gaps.length
            "
          >
            Nenhuma informação adicional foi solicitada pelo relatório. Valide
            as conclusões com a equipe.
          </p>
        </section>
      </div>
      <aside class="evidence-column">
        <div class="evidence-header">
          <Icon name="book" :size="22" />
          <h2>Fontes da análise</h2>
        </div>
        <p class="evidence-intro">
          Trechos do acervo da área, preservados para conferência. Os
          procedimentos são fictícios.
        </p>
        <p v-if="!report.sources.length" class="message warning">
          Nenhum trecho relevante encontrado.
        </p>
        <details
          v-for="(source, index) in report.sources"
          :id="`evidence-${index + 1}`"
          :key="source.id"
          class="evidence-card"
          open
        >
          <summary>
            <span class="source-number">FONTE {{ index + 1 }}</span
            ><strong>{{ source.title }}</strong
            ><span>{{ source.section }}</span>
          </summary>
          <blockquote>{{ source.excerpt }}</blockquote>
          <small>{{ source.document }}</small>
        </details>
        <div class="record-info">
          <span>MODELOS UTILIZADOS</span>
          <p>
            Classificação: {{ report.triage.model }}<br />Relatório:
            {{ report.llm_model }}
          </p>
        </div>
      </aside>
    </div>
    <div class="report-disclaimer">
      <Icon name="help" :size="20" />
      <p>{{ report.notice }}</p>
    </div>
  </article>
</template>
