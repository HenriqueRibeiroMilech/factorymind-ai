# Avaliação do modelo de equipamentos

Fonte: [AI4I 2020, UCI](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset), DOI [10.24432/C5HS5C](https://doi.org/10.24432/C5HS5C), licença CC BY 4.0. Dataset **sintético**, de manutenção preditiva, com 10,000 registros e 14 colunas. Download: `python -m ml.src.download`. Treino: `python -m ml.src.train`, na raiz do projeto, com as dependências fixadas do backend.

## Exploração objetiva

Sem valores ausentes. Há 339 falhas (3.39%) e 9661 condições sem falha: acurácia isolada seria enganosa. Tipos de produto: {'L': 6000, 'M': 2997, 'H': 1003}. Estatísticas de cada leitura, correlações e taxa de falha por tipo estão em [eda.json](artifacts/eda.json). Temperaturas e outras variáveis têm escalas diferentes; o pipeline padroniza as numéricas e codifica o tipo com one-hot.

## Estratégia e resultado

Alvo: `Machine failure`. Somente tipo, temperatura do ar, temperatura do processo, rotação, torque e desgaste entram no treino. UDI, Product ID e indicadores TWF/HDF/PWF/OSF/RNF são excluídos por seleção explícita das seis entradas. Vibração não existe como feature.

Separação aleatória estratificada 60/20/20, seed 42: {'train': 6000, 'validation': 2000, 'test': 2000}; positivos: {'train': 203, 'validation': 68, 'test': 68}. Pré-processamento ajustado **somente no treino**. Comparamos uma referência que sempre escolhe a classe majoritária, regressão logística balanceada e Random Forest balanceada. Modelos e limiares são escolhidos pela maior F2 na validação, priorizando recall; precisão e depois limiar maior desempataram. Busca de 0,05 a 0,95 com passo 0,01; referência mantida em 0,50. Hiperparâmetros fixos no script, sem busca no teste. O pipeline final permanece ajustado apenas nos 60% de treino; não há novo ajuste com validação ou teste.

| Classificador | Limiar | F2 validação | Precisão teste | Recall teste | F2 teste |
|---|---:|---:|---:|---:|---:|
| baseline | 0.50 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| logistic_regression | 0.80 | 0.4897 | 0.3478 | 0.5882 | 0.5168 |
| random_forest | 0.27 | 0.6933 | 0.5400 | 0.7941 | 0.7258 |

Selecionado: **random_forest**, limiar **0.27**. Matriz de confusão do teste (linhas = real, colunas = predito, ordem sem falha / falha):

| | Predito sem falha | Predito falha |
|---|---:|---:|
| Real sem falha | 1886 | 46 |
| Real falha | 14 | 54 |

Detalhes de todos os candidatos em [evaluation.json](artifacts/evaluation.json). [metadata.json](artifacts/metadata.json) guarda versão, limiar, faixas de treino, hash do CSV e do pipeline, bibliotecas e métricas. `pipeline.joblib` é gerado localmente e ignorado pelo Git; o servidor nunca treina. SHA256 do CSV: `dc6630cd9b1f0f853922fad78a1b6436570d3f1ec863f1dd5c4340ac56bc8a8e`.

## Limites

O split aleatório mede desempenho dentro deste dataset sintético, com temperaturas correlacionadas e modos de falha construídos. Não comprova generalização temporal nem desempenho em uma fábrica real. A aplicação usa `predict_proba` como **escore não calibrado**, não como probabilidade garantida de falha. A decisão classifica a condição das seis leituras simultâneas; não estima quando ocorrerá uma quebra. Uma pontuação baixa pode coexistir com vibração, ruído ou outros sintomas ausentes do dataset. Leituras fora das faixas do treino aparecem como ressalva no relatório. Procedimentos fictícios e análise de LLM precisam de avaliação humana.
