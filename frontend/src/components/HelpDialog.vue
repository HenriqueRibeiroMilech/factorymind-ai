<script setup>
import { onMounted, onUnmounted, ref } from "vue";
import Icon from "./Icon.vue";
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
    @close="emit('close')"
    @click="
      (event) => {
        if (event.target === dialog) dialog.close();
      }
    "
  >
    <div class="dialog-header">
      <span class="eyebrow">DA OBSERVAÇÃO À ANÁLISE</span
      ><button
        class="icon-button"
        aria-label="Fechar ajuda"
        @click="dialog.close()"
      >
        <Icon name="close" />
      </button>
    </div>
    <h2>Um relato. Um caminho claro.</h2>
    <p>
      Descreva o que observou. O FactoryMind reúne as informações para apoiar a
      próxima decisão da equipe.
    </p>
    <ol class="help-steps">
      <li>
        <span>01</span>
        <div>
          <strong>Registre e classifique</strong>
          <p>
            O relato é salvo e o Jev sugere uma das três áreas. Você pode
            revisar a categoria.
          </p>
        </div>
      </li>
      <li>
        <span>02</span>
        <div>
          <strong>Complete o contexto</strong>
          <p>
            Acrescente o que souber. Para equipamentos, informe as seis leituras
            do mesmo instante ou siga sem elas.
          </p>
        </div>
      </li>
      <li>
        <span>03</span>
        <div>
          <strong>Consulte as evidências</strong>
          <p>
            A análise reúne documentos da área e o modelo de equipamentos quando
            aplicável. O relatório fica no Histórico.
          </p>
        </div>
      </li>
    </ol>
    <h3>Exemplos do chão de fábrica</h3>
    <div class="help-examples">
      <article>
        <Icon name="machine" />
        <div>
          <strong>Produção e equipamentos</strong>
          <p>“A mesa da fresadora vibrou durante a segunda passada.”</p>
        </div>
      </article>
      <article>
        <Icon name="quality" />
        <div>
          <strong>Qualidade</strong>
          <p>“O diâmetro das peças do lote está fora da tolerância.”</p>
        </div>
      </article>
      <article>
        <Icon name="flow" />
        <div>
          <strong>Processos industriais</strong>
          <p>“As peças estão formando fila entre a usinagem e a inspeção.”</p>
        </div>
      </article>
    </div>
    <p class="help-notice">
      Análise inicial para portfólio, com procedimentos fictícios. Hipóteses e
      recomendações precisam de avaliação humana.
    </p>
    <button class="button primary full" @click="dialog.close()">
      Entendi, continuar <Icon name="arrow" :size="18" />
    </button>
  </dialog>
</template>
