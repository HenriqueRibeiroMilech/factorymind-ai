export async function api(path, options = {}) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 150000);
  try {
    const response = await fetch(`/api/v1${path}`, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
      signal: controller.signal,
    });
    const data = await response.json();
    if (!response.ok) {
      const error = new Error(
        data.error?.message || "Não foi possível concluir. Tente novamente.",
      );
      error.fields = data.error?.fields || [];
      throw error;
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError")
      throw new Error(
        "A resposta demorou mais que o esperado. Seus dados podem estar salvos; consulte o Histórico antes de reenviar.",
      );
    if (error instanceof TypeError)
      throw new Error(
        "Não foi possível conectar ao servidor. Confira se o Flask está em execução e tente novamente.",
      );
    throw error;
  } finally {
    clearTimeout(timer);
  }
}

export const categories = {
  equipment: {
    label: "Produção e equipamentos",
    area: "Produção e manutenção de equipamentos",
    icon: "machine",
  },
  quality: { label: "Qualidade", area: "Qualidade", icon: "quality" },
  processes: {
    label: "Processos industriais",
    area: "Engenharia de processos",
    icon: "flow",
  },
};

export const statuses = {
  pending_triage: { label: "Aguardando classificação", tone: "pending" },
  triaging: { label: "Classificando", tone: "pending" },
  triage_failed: { label: "Tentar classificação", tone: "warning" },
  review_required: { label: "Revisão necessária", tone: "warning" },
  ready: { label: "Pronta para análise", tone: "pending" },
  analyzing: { label: "Em análise", tone: "pending" },
  analysis_failed: { label: "Tentar análise", tone: "warning" },
  completed: { label: "Relatório disponível", tone: "success" },
};

export function formatDate(value) {
  return new Intl.DateTimeFormat("pt-BR", {
    dateStyle: "short",
    timeStyle: "short",
  }).format(new Date(value));
}

export const measurementFields = [
  {
    key: "air_temperature",
    label: "Temperatura do ar",
    unit: "K",
    min: 0.01,
    max: 1000,
  },
  {
    key: "process_temperature",
    label: "Temperatura do processo",
    unit: "K",
    min: 0.01,
    max: 1500,
  },
  {
    key: "rotational_speed",
    label: "Velocidade de rotação",
    unit: "rpm",
    min: 0.01,
    max: 100000,
  },
  { key: "torque", label: "Torque", unit: "Nm", min: 0.01, max: 10000 },
  {
    key: "tool_wear",
    label: "Desgaste da ferramenta",
    unit: "min",
    min: 0,
    max: 100000,
  },
];
