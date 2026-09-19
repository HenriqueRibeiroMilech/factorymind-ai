<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import Icon from "./Icon.vue";
import TestExamples from "./TestExamples.vue";

const props = defineProps({ section: { type: String, default: "workflow" } });
const emit = defineEmits(["close"]);
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
      }}</span>
      <button
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
        Você registra um problema da fábrica e recebe uma análise inicial com a
        área responsável, as fontes consultadas e o que ainda precisa ser
        verificado.
      </p>
      <ol class="help-steps">
        <li>
          <span>01</span>
          <div>
            <strong>Registre o que aconteceu</strong>
            <p>
              Descreva o problema observado. Máquina, lote ou etapa são
              opcionais. O relato original é salvo antes da classificação.
            </p>
          </div>
        </li>
        <li>
          <span>02</span>
          <div>
            <strong>Confira a área responsável</strong>
            <p>
              O Jev sugere Produção e equipamentos, Qualidade ou Processos
              industriais. Você pode corrigir a categoria. Confiança baixa ou
              ausente e risco sinalizado exigem revisão com justificativa.
            </p>
          </div>
        </li>
        <li>
          <span>03</span>
          <div>
            <strong>Complete as informações disponíveis</strong>
            <p>
              Acrescente um complemento sem alterar o texto original. Para
              equipamentos, informe as seis leituras do mesmo instante ou
              continue sem medições. Nas outras áreas, siga com o relato.
            </p>
          </div>
        </li>
        <li>
          <span>04</span>
          <div>
            <strong>Solicite e confira a análise</strong>
            <p>
              O sistema busca procedimentos da área e usa o modelo de
              equipamentos quando há uma leitura completa. O LLM redige o
              relatório com hipóteses, recomendações, trechos de apoio e
              limitações.
            </p>
          </div>
        </li>
        <li>
          <span>05</span>
          <div>
            <strong>Retome pelo Histórico</strong>
            <p>
              Reabra uma ocorrência para continuar ou consultar o relatório
              salvo. Atualizar a página não apaga a análise concluída. Se um
              serviço falhar, tente novamente pelo mesmo registro.
            </p>
          </div>
        </li>
      </ol>
      <div class="guide-model-note">
        <Icon name="machine" :size="20" />
        <div>
          <strong>O que o modelo de equipamentos avalia?</strong>
          <p>
            Ele classifica a condição das seis leituras com base no dataset
            sintético AI4I 2020. Vibração não é uma entrada desse modelo; um
            escore baixo não descarta o sintoma relatado nem prevê a data de uma
            quebra.
          </p>
        </div>
      </div>
    </template>
    <template v-else>
      <h2 id="guide-title">Exemplos para testar</h2>
      <p>
        Escolha uma área, copie o relato e siga o roteiro. Os dados abaixo são
        fictícios e servem para conhecer o projeto.
      </p>
      <TestExamples />
    </template>
    <p class="help-notice">
      As análises usam os serviços configurados e podem variar. Os procedimentos
      do acervo são fictícios; hipóteses e recomendações precisam de revisão da
      equipe.
    </p>
    <button class="button primary full" @click="dialog.close()">
      Voltar ao relato <Icon name="arrow" :size="18" />
    </button>
  </dialog>
</template>
