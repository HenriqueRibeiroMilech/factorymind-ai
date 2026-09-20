# FactoryMind AI

Projeto de estudo que combina machine learning e IA generativa para apoiar a análise de problemas no chão de fábrica.

A pessoa descreve uma ocorrência, o Jev sugere a área responsável e permite revisar a classificação. Depois, a aplicação busca procedimentos relacionados e gera uma análise com hipóteses, recomendações e fontes. Os relatos e relatórios ficam salvos no histórico.

Na área de Equipamentos, também é possível informar as condições da máquina e consultar um modelo de classificação de falhas. Qualidade e Processos seguem a análise sem esse modelo.

## Tecnologias

- Python, Flask e SQLite no backend
- Vue 3 e Vite no frontend
- Scikit-learn para o modelo de machine learning
- Jev para classificação dos relatos e OpenAI para geração dos relatórios
- TF-IDF para buscar os procedimentos da base de conhecimento

## Como rodar

Você vai precisar de Python 3.12, Node.js 22.18+ e das chaves do Jev e da OpenAI. Os comandos abaixo são para PowerShell, na pasta do projeto.

Prepare o backend:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-lock.txt
Copy-Item backend\.env.example backend\.env
```

Preencha `JEV_API_KEY` e `OPENAI_API_KEY` em `backend/.env`. Em `LLM_MODEL`, escolha o modelo que deseja usar. As chaves ficam no backend; o arquivo `.env` é ignorado pelo Git.

Baixe o dataset, treine o modelo e prepare o banco:

```powershell
.\.venv\Scripts\python.exe -m ml.src.download
.\.venv\Scripts\python.exe -m ml.src.train
.\.venv\Scripts\python.exe backend\init_db.py
```

Esses passos de preparação só precisam ser feitos na primeira execução. Os dados, o modelo treinado e o banco são gerados localmente.

Inicie o backend:

```powershell
.\.venv\Scripts\python.exe backend\run.py
```

Em outro terminal, abra a pasta do projeto e rode o frontend:

```powershell
cd frontend
npm ci
npm run dev
```

Abra [localhost:5173](http://localhost:5173). O backend roda na porta 5000. Se alterar o `.env`, reinicie o backend.

## Para testar a aplicação

O bloco **Primeira vez por aqui?** explica o fluxo e traz exemplos para as três áreas: Equipamentos, Qualidade e Processos. No exemplo de Equipamentos, dá para comparar dois conjuntos de leituras e ver como o resultado do modelo muda.

A classificação pode ser corrigida antes de continuar. Quando há baixa confiança ou risco informado, a aplicação pede confirmação. Ao terminar, o relatório fica disponível no Histórico.

## Machine learning

Usei o dataset [AI4I 2020, da UCI](https://doi.org/10.24432/C5HS5C), com 10 mil registros, para comparar uma referência majoritária, regressão logística e Random Forest. O treino usa seis entradas: tipo do produto, temperatura do ar, temperatura do processo, rotação, torque e desgaste da ferramenta.

A Random Forest teve o melhor F2 na validação. No teste, alcançou **79,41% de recall** e **54% de precisão**, com limiar de 0,27. O pré-processamento é ajustado apenas com os dados de treino e a inferência usa o pipeline salvo.

Os detalhes da avaliação estão em [ml/ML.md](ml/ML.md). O dataset é sintético: o resultado classifica as condições informadas e não prevê quando uma máquina real vai quebrar. Os procedimentos da aplicação também são fictícios, e as recomendações precisam de revisão humana.

## Estrutura

```text
backend/          API, banco, integrações e testes
frontend/         interface em Vue
ml/               download, treino e avaliação do modelo
knowledge_base/   procedimentos usados na busca
```

## Verificação

Para rodar os testes do backend, na raiz:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Para gerar o build do frontend:

```powershell
cd frontend
npm run build
```

Com o build pronto, o Flask também serve a interface em [localhost:5000](http://localhost:5000).
