<script setup>
import { computed, ref } from "vue";
import { categories, measurementFields } from "../api";
import Icon from "./Icon.vue";

const props = defineProps({ category: { type: String, default: "equipment" } });
const emit = defineEmits(["select-scenario"]);

const scenarios = [
  {
    category: "equipment",
    label: "Equipamentos",
    title: "Vibração na fresadora",
    description: "A mesa da fresadora vibrou durante a segunda passada.",
    reference: "Fresadora F-07",
    steps: [
      "Cole o relato na descrição do problema e clique em Salvar e continuar.",
      "Confira a categoria Produção e equipamentos. Se for solicitada uma confirmação, clique em Confirmar categoria. Para corrigir, abra Revisar categoria e justifique o ajuste.",
      "Selecione Tenho as seis medições, informe os valores abaixo e clique em Gerar análise inicial.",
    ],
    expected:
      "O relatório deve mostrar a área de Produção e manutenção, as fontes e o resultado do modelo: entradas, escore, limiar, decisão e versão. A vibração continua relevante mesmo se o escore for baixo.",
  },
  {
    category: "quality",
    label: "Qualidade",
    title: "Peças fora da tolerância",
    description: "O diâmetro das peças do lote está fora da tolerância.",
    reference: "Lote Q-12",
    steps: [
      "Cole o relato na descrição do problema e clique em Salvar e continuar.",
      "Confira se a categoria é Qualidade. Se for preciso ajustar a classificação, use Revisar categoria e justifique que o problema observado é um desvio na peça.",
      "Você pode acrescentar um complemento. Depois, clique em Gerar análise inicial, sem informar medições de equipamento.",
    ],
    expected:
      "A área responsável deve ser Qualidade. O modelo de equipamentos aparece como não aplicável. Confira se a análise trata a causa do defeito como hipótese e aponta os documentos e informações que faltam.",
  },
  {
    category: "processes",
    label: "Processos",
    title: "Fila entre operações",
    description: "As peças estão formando fila entre a usinagem e a inspeção.",
    reference: "Usinagem → inspeção",
    steps: [
      "Cole o relato na descrição do problema e clique em Salvar e continuar.",
      "Confira a categoria Processos industriais. Se ela estiver correta, confirme quando solicitado; use Revisar categoria apenas se precisar corrigir.",
      "Se quiser, complemente com o período observado e as etapas envolvidas. Solicite a análise com as informações disponíveis.",
    ],
    expected:
      "O relatório deve encaminhar a ocorrência para Engenharia de processos, com o modelo de equipamentos identificado como não aplicável. Confira as hipóteses sobre o fluxo e os dados solicitados antes de concluir que há um gargalo.",
  },
];
const active = computed(() =>
  Math.max(
    0,
    scenarios.findIndex((item) => item.category === props.category),
  ),
);
const scenario = computed(() => scenarios[active.value]);
const copied = ref(false);
const copyError = ref("");
const readings = {
  product_type: "L",
  air_temperature: 298.1,
  process_temperature: 308.6,
  rotational_speed: 1551,
  torque: 42.8,
  tool_wear: 0,
};

const comparisonReadings = {
  product_type: "L",
  air_temperature: 300,
  process_temperature: 313,
  rotational_speed: 1400,
  torque: 70,
  tool_wear: 210,
};

function selectScenario(index) {
  emit("select-scenario", scenarios[index].category);
  copied.value = false;
  copyError.value = "";
}
async function copyDescription() {
  copyError.value = "";
  try {
    await navigator.clipboard.writeText(scenario.value.description);
    copied.value = true;
  } catch {
    copied.value = false;
    copyError.value =
      "Selecione o texto do relato e copie manualmente para o formulário.";
  }
}
</script>

<template>
  <div class="scenario-switcher" aria-label="Escolha um cenário de teste">
    <button
      v-for="(item, index) in scenarios"
      :key="item.category"
      type="button"
      :aria-pressed="active === index"
      :class="{ selected: active === index }"
      @click="selectScenario(index)"
    >
      <Icon :name="categories[item.category].icon" :size="17" /><span>{{
        item.label
      }}</span>
    </button>
  </div>
  <article class="test-scenario" :aria-label="scenario.title">
    <div class="scenario-heading">
      <span class="scenario-number">0{{ active + 1 }}</span>
      <div>
        <span class="scenario-area">{{
          categories[scenario.category].label
        }}</span>
        <h3>{{ scenario.title }}</h3>
      </div>
    </div>
    <div class="example-description">
      <span class="example-label">RELATO PARA COPIAR</span>
      <blockquote>{{ scenario.description }}</blockquote>
      <button type="button" class="copy-button" @click="copyDescription">
        <Icon :name="copied ? 'check' : 'file'" :size="15" />{{
          copied ? "Relato copiado" : "Copiar relato"
        }}
      </button>
      <p v-if="copied || copyError" class="copy-feedback" role="status">
        {{ copyError || "Cole o texto no campo Descrição do problema." }}
      </p>
    </div>
    <p class="example-reference">
      Identificação sugerida <strong>{{ scenario.reference }}</strong>
      <span>opcional</span>
    </p>
    <h4>Como testar este cenário</h4>
    <ol class="scenario-steps">
      <li v-for="step in scenario.steps" :key="step">{{ step }}</li>
    </ol>
    <template v-if="scenario.category === 'equipment'">
      <div class="example-measurements">
        <h4>Leituras para o teste</h4>
        <p>Considere os seis valores como uma leitura do mesmo instante.</p>
        <dl>
          <div>
            <dt>Tipo de produto</dt>
            <dd>{{ readings.product_type }}</dd>
          </div>
          <div v-for="field in measurementFields" :key="field.key">
            <dt>{{ field.label }}</dt>
            <dd>
              {{ readings[field.key] }} <span>{{ field.unit }}</span>
            </dd>
          </div>
        </dl>
      </div>
      <details class="example-ml-comparison">
        <summary>Comparar outra condição no modelo</summary>
        <p>
          Para explorar o ML, crie outro registro de equipamentos com o mesmo
          relato e esta segunda leitura fictícia. Compare o escore, o limiar e a
          decisão dos dois relatórios.
        </p>
        <div class="example-measurements">
          <h4>Segunda leitura para comparar</h4>
          <p>
            Considere novamente os seis valores como uma leitura do mesmo
            instante.
          </p>
          <dl>
            <div>
              <dt>Tipo de produto</dt>
              <dd>{{ comparisonReadings.product_type }}</dd>
            </div>
            <div v-for="field in measurementFields" :key="field.key">
              <dt>{{ field.label }}</dt>
              <dd>
                {{ comparisonReadings[field.key] }}
                <span>{{ field.unit }}</span>
              </dd>
            </div>
          </dl>
        </div>
        <p>
          O torque e o desgaste são maiores neste conjunto. O modelo avalia a
          combinação das seis entradas; o resultado não substitui a observação
          de vibração no relato.
        </p>
      </details>
      <p class="scenario-alternative">
        <strong>Para testar sem medições:</strong> em outro registro, escolha
        Não disponho das medições. O relatório deve informar que o modelo não
        foi executado.
      </p>
    </template>
    <div class="scenario-result">
      <Icon name="check" :size="18" />
      <div>
        <h4>O que conferir no relatório</h4>
        <p>{{ scenario.expected }}</p>
      </div>
    </div>
  </article>
  <div class="examples-next-step">
    <Icon name="history" :size="18" />
    <p>
      Depois de concluir, abra o <strong>Histórico</strong> e reabra a
      ocorrência. Repita com os outros dois cenários para conhecer as três
      áreas.
    </p>
  </div>
  <p class="examples-review-tip">
    <strong>Quer testar a revisão humana?</strong> Marque Esta situação envolve
    risco em um novo relato. Você poderá confirmar a categoria com um clique ou
    abrir Revisar categoria para corrigir e justificar o ajuste.
  </p>
</template>
