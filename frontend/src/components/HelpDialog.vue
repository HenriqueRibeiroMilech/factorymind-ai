<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import { measurementFields } from "../api";
import Icon from "./Icon.vue";
import TestExamples from "./TestExamples.vue";

const props = defineProps({
  section: { type: String, default: "workflow" },
  exampleCategory: { type: String, default: "equipment" },
});
const emit = defineEmits(["close", "example-change"]);
const dialog = ref(null);
let previousFocus;
onMounted(() => {
  previousFocus = document.activeElement;
  dialog.value.showModal();
  dialog.value.querySelector("button").focus();
});
onUnmounted(() => previousFocus?.focus());
</script>

<template>
  <dialog
    ref="dialog"
    class="help-dialog"
    :class="{ 'examples-dialog': props.section === 'examples' }"
    aria-labelledby="guide-title"
    @close="emit('close')"
    @click="
      (event) => {
        if (event.target === dialog) dialog.close();
      }
    "
  >
    <div class="dialog-header">
      <span class="eyebrow">{{
        props.section === "workflow"
          ? "CONHEÇA O PROJETO"
          : "TESTE AS TRÊS ÁREAS"
      }}</span
      ><button
        class="icon-button"
        aria-label="Fechar ajuda"
        @click="dialog.close()"
      >
        <Icon name="close" />
      </button>
    </div>
    <template v-if="props.section === 'workflow'">
      <h2 id="guide-title">Como o FactoryMind funciona</h2>
      <p>
        O relato direciona a análise. Para equipamentos, um modelo de machine
        learning avalia as medições e leva seu resultado para o relatório.
      </p>
      <section class="ml-guide" aria-labelledby="ml-guide-title">
        <div class="ml-guide-heading">
          <Icon name="machine" :size="24" />
          <div>
            <span>AI4I 2020 · TREINO REAL</span>
            <h3 id="ml-guide-title">Machine Learning de equipamentos</h3>
          </div>
        </div>
        <p>
          Um classificador supervisionado foi treinado com o dataset sintético
          AI4I 2020. O treino compara uma referência simples, Regressão
          Logística e Random Forest, com conjuntos separados de treino,
          validação e teste.
        </p>
        <ol class="ml-guide-flow">
          <li>
            <span>01</span><strong>Seis leituras</strong>
            <p>Valores do mesmo instante, informados pelo operador.</p>
          </li>
          <li>
            <span>02</span><strong>Modelo treinado</strong>
            <p>O pipeline aplica o pré-processamento e calcula o escore.</p>
          </li>
          <li>
            <span>03</span><strong>Decisão e relatório</strong>
            <p>O escore é comparado ao limiar definido na validação.</p>
          </li>
        </ol>
        <div class="ml-guide-inputs">
          <strong>Entradas do modelo</strong>
          <ul>
            <li>Tipo de produto <span>L, M ou H</span></li>
            <li v-for="field in measurementFields" :key="field.key">
              {{ field.label }} <span>{{ field.unit }}</span>
            </li>
          </ul>
        </div>
        <p class="ml-guide-result">
          <strong>No relatório:</strong> entradas, escore, limiar, decisão e
          versão vêm do pipeline de ML. O LLM recebe esses dados para redigir a
          análise; ele não calcula o resultado do classificador.
        </p>
        <p class="ml-guide-limit">
          O escore não é uma probabilidade calibrada nem prevê a data de uma
          quebra. Vibração fica no relato e continua relevante mesmo com escore
          baixo. Sem as seis leituras, o ML não é executado; em Qualidade e
          Processos, ele não se aplica.
        </p>
      </section>
      <h3 class="guide-flow-title">O percurso completo</h3>
      <ol class="help-steps">
        <li>
          <span>01</span>
          <div>
            <strong>Registre o que aconteceu</strong>
            <p>
              O relato original é salvo. Identificação e risco são opcionais.
            </p>
          </div>
        </li>
        <li>
          <span>02</span>
          <div>
            <strong>Confira a categoria sugerida pelo Jev</strong>
            <p>
              Se estiver correta, siga com ela. Com baixa confiança ou risco,
              basta Confirmar categoria. Use Revisar categoria apenas para abrir
              a edição e justificar um ajuste.
            </p>
          </div>
        </li>
        <li>
          <span>03</span>
          <div>
            <strong>Complete as informações</strong>
            <p>
              Acrescente um complemento e, em equipamentos, as seis medições
              disponíveis. Você pode consultar os exemplos em qualquer etapa sem
              perder os campos.
            </p>
          </div>
        </li>
        <li>
          <span>04</span>
          <div>
            <strong>Gere e confira a análise</strong>
            <p>
              O relatório reúne o resultado de ML quando aplicável,
              procedimentos da área, hipóteses, recomendações e informações que
              faltam.
            </p>
          </div>
        </li>
        <li>
          <span>05</span>
          <div>
            <strong>Retome pelo Histórico</strong>
            <p>
              Reabra uma ocorrência ou consulte o relatório salvo. Se um serviço
              falhar, tente novamente pelo mesmo ID.
            </p>
          </div>
        </li>
      </ol>
    </template>
    <template v-else>
      <h2 id="guide-title">Exemplos para testar</h2>
      <p>
        Escolha uma área e consulte o roteiro enquanto preenche a ocorrência. Os
        dados são fictícios; o exemplo de equipamentos também permite comparar
        duas leituras de ML.
      </p>
      <TestExamples
        :category="props.exampleCategory"
        @select-scenario="emit('example-change', $event)"
      />
    </template>
    <p class="help-notice">
      As análises usam os serviços configurados e podem variar. O dataset é
      sintético e os procedimentos do acervo são fictícios; hipóteses e
      recomendações precisam de revisão da equipe.
    </p>
    <button class="button primary full" @click="dialog.close()">
      Continuar nesta etapa <Icon name="arrow" :size="18" />
    </button>
  </dialog>
</template>
