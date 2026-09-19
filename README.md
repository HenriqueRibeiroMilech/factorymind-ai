# FactoryMind AI

Uma aplicação de portfólio para registrar problemas do chão de fábrica e reunir contexto para a equipe responsável. **Flask + SQLite + Vue 3**, com classificação pelo Jev, procedimentos fictícios recuperados por TF-IDF e um LLM para redigir a análise inicial. O perfil de equipamentos também usa um classificador treinado de verdade com o AI4I 2020.

O percurso é único: **registrar → classificar → revisar/complementar → analisar → consultar no Histórico**. O texto original, a sugestão do Jev, a decisão humana e o relatório ficam salvos no mesmo registro. Nenhum formulário é preenchido com exemplos.

## Configuração no Windows / PowerShell

Pré-requisitos: **Python 3.12**, **Node.js 22.18+** e Git. Execute a partir da raiz do clone:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-lock.txt
Copy-Item backend\.env.example backend\.env
```

Edite `backend/.env` com suas credenciais:

```dotenv
JEV_API_KEY=sua-chave-typesafe
JEV_MODEL=jev-latest
OPENAI_API_KEY=sua-chave-openai
LLM_MODEL=gpt-4.1-mini
```

O Jev usa o [endpoint Choice da TypeSafe](https://docs.typesafe.ai/primitives/choice). O LLM usa [Chat Completions com saída estruturada da OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=chat). Os três perfis compartilham o mesmo cliente e o mesmo `LLM_MODEL`. As chaves ficam apenas no backend; variáveis do ambiente têm precedência sobre `.env`. Reinicie o Flask após alterá-las. Não há seleção automática de provedor nem respostas substitutas.

`requirements.txt` declara as dependências diretas fixadas; `requirements-lock.txt` inclui também as transitivas utilizadas na avaliação. O frontend possui `package-lock.json`; use `npm ci`.

## Dados, treino e banco

```powershell
.\.venv\Scripts\python.exe -m ml.src.download
.\.venv\Scripts\python.exe -m ml.src.train
.\.venv\Scripts\python.exe backend\init_db.py
```

O primeiro comando obtém o CSV original na UCI e grava sua origem e SHA256 em `ml/data/source.json`. O treino compara referência majoritária, regressão logística e Random Forest; salva `ml/artifacts/pipeline.joblib`, metadados, exploração e avaliação. **O treino é executado fora do servidor.** O artefato binário e os dados baixados são locais e ignorados pelo Git; em um clone limpo, execute os dois comandos. O banco é inicializado sem apagar registros existentes e também é criado automaticamente pelo Flask quando necessário.

O modelo selecionado foi Random Forest, limiar **0,27**: precisão de teste **54%**, recall **79,41%**, matriz de confusão `[[1886, 46], [14, 54]]`. A estratégia, a comparação completa e as limitações estão na [nota de ML](ml/ML.md). A fonte é o [AI4I 2020, UCI, CC BY 4.0](https://doi.org/10.24432/C5HS5C). O dataset é sintético; o escore não calibrado avalia a condição informada e não prevê a data de quebra de uma máquina real.

## Executar a aplicação

Terminal do backend, na raiz:

```powershell
.\.venv\Scripts\python.exe backend\run.py
```

Em outro terminal, na raiz:

```powershell
Set-Location frontend
npm ci
npm run dev
```

Abra [http://127.0.0.1:5173](http://127.0.0.1:5173). O Vite encaminha `/api` para o Flask em `127.0.0.1:5000`, sem precisar configurar CORS. O backend responde em `/api/v1/health`.

Para usar o build local com apenas o processo Flask:

```powershell
Set-Location frontend
npm run build
Set-Location ..
.\.venv\Scripts\python.exe backend\run.py
```

Abra [http://127.0.0.1:5000](http://127.0.0.1:5000). O Flask serve os arquivos de `frontend/dist` e as rotas do Vue. As fontes tipográficas são locais. Os comandos acima usam servidores de desenvolvimento para uso local; esta entrega não inclui implantação ou autenticação.

## Como usar

- **Novo relato:** descreva o problema; identificação e sinalização de risco são opcionais. O relato é salvo antes de chamar o Jev.
- **Conheça e teste:** os botões em destaque na página inicial reúnem o funcionamento e três cenários para experimentar. Cada exemplo tem um relato para copiar, um roteiro e os pontos a conferir no relatório; o caso de equipamentos também inclui as seis leituras fictícias. A ajuda preserva o que já foi digitado.
- **Revisão:** confiança abaixo de 0,75, confiança ausente ou risco sinalizado exigem confirmar/corrigir a categoria e justificar antes da análise. Também é possível revisar voluntariamente. A sugestão original permanece salva.
- **Contexto:** acrescente um complemento sem alterar o original. Em equipamentos, informe todas as seis leituras do mesmo instante ou selecione que não dispõe delas. As temperaturas usam kelvin; vibração permanece no texto. Qualidade e Processos seguem sem ML.
- **Relatório:** consulte hipóteses, recomendações, trechos e lacunas. Quando o ML é executado, veja entradas, escore, limiar, decisão e versão. A interface também mostra os valores originais sem arredondamento em um detalhe expansível.
- **Histórico:** busque por relato, identificação ou ID, filtre pendentes/concluídas e reabra o registro. Um relatório concluído é lido do SQLite, sem nova chamada ao LLM.

Uma chave ausente, credencial recusada ou falha de rede aparece na própria ocorrência. Configure o serviço ou tente novamente pelo mesmo ID. O complemento e as medições salvos permanecem disponíveis. Botões ficam bloqueados durante o envio; uma chave de idempotência protege a criação contra repetição de uma requisição cuja resposta se perdeu. Tentativas interrompidas são liberadas após três minutos. A ajuda mantém o formulário; rascunhos ainda não enviados ficam na sessão do navegador quando o armazenamento local está disponível.

## Organização do código

```text
backend/
  run.py, init_db.py           # inicialização e execução
  app/__init__.py             # create_app, Blueprints e erros HTTP
  app/config.py               # configuração pelo ambiente
  app/integrations/           # um cliente Jev e um cliente LLM
  app/modules/health/         # saúde e configuração, sem expor chaves
  app/modules/incidents/      # rotas, Pydantic, SQL, fluxo e relatório
  app/modules/predictions/    # validação e inferência do pipeline
  tests/                     # integrações simuladas somente nos testes
ml/src/                      # obtenção dos dados e treino reproduzível
ml/artifacts/                # métricas e metadados; pipeline gerado localmente
knowledge_base/              # procedimentos fictícios de cada área
frontend/src/                # páginas Vue, componentes e CSS
```

`routes.py` valida a requisição e chama `service.py`. `storage.py` faz SQL parametrizado e controla estados de processamento. `profiles.py` escolhe instruções e ferramentas com um dicionário Python. `knowledge.py` limita a busca à área e combina TF-IDF de palavras e caracteres para recuperar flexões como “vibrou”/“vibração”. Há um corte mínimo de similaridade: a busca pode não retornar documentos.

O LLM recebe o relato, o contexto recuperado e o resultado de ML quando aplicável. `report.py` valida o formato com Pydantic e rejeita IDs de fonte desconhecidos. Dados originais, categoria, números de ML e excertos vêm diretamente das fontes e do backend. Os campos de prosa não aceitam algarismos: números são apresentados em campos próprios, evitando que o LLM substitua escore, medições ou limites. Uma hipótese/recomendação sem fonte fica marcada como lacuna e solicita revisão. A validação de IDs não comprova que um trecho sustenta semanticamente a recomendação; essa conferência continua com a equipe.

O escopo tem um Flask síncrono, um SQLite, um Jev e um LLM, sem frameworks de agentes, filas ou serviços auxiliares. O projeto não constitui procedimento industrial aprovado.

## Verificação

Na raiz:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
Set-Location frontend
npm run build
```

Os testes cobrem criação idempotente, persistência entre instâncias Flask, revisão, bloqueio de duplicatas, retomada de interrupções, falhas dos provedores, uso seletivo do ML, medições inválidas, preservação de números, citações, lacunas e trechos exatos. Com o treino disponível, verificam também o pipeline real, o ajuste do pré-processamento apenas no treino e a matriz de confusão do teste. Sem os artefatos, dois testes de integração do ML são explicitamente pulados.

Para repetir a verificação manual de sucesso no navegador sem usar credenciais de produção, há um **servidor exclusivamente de testes**, com banco temporário e os três relatos exatos da ajuda:

```powershell
.\.venv\Scripts\python.exe backend\tests\browser_harness.py
```

Abra [http://127.0.0.1:5001](http://127.0.0.1:5001) após gerar o build. Apenas Jev e LLM são simulados nesse processo de teste; recuperação e ML usam a implementação real. O caso de Qualidade começa com uma sugestão incorreta de baixa confiança para exercitar a correção humana. O processo normal `backend/run.py` não importa esse arquivo e não oferece nenhuma chave de ativação de simulações. Encerre o servidor de testes com `Ctrl+C` para remover seu banco temporário. Para validar as chamadas reais, configure as duas chaves e use o servidor normal.
