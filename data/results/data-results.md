# Resultados das Análises

Este diretório contém os resultados das análises, modelos e segmentações realizadas sobre o abandono escolar no ensino médio brasileiro.

## Conteúdo

### Análise Exploratória

- **estatisticas_descritivas.csv**: Estatísticas descritivas gerais sobre abandono escolar
- **correlacoes_municipios_2022.csv**: Matriz de correlação entre variáveis no nível municipal
- **correlacoes_escolas_2022.csv**: Matriz de correlação entre variáveis no nível escolar
- **relatorio_correlacao_TAXA_ABANDONO_municipios_2022.csv**: Relatório específico de correlações com abandono

### Segmentação e Classificação

- **clusters_municipios.csv**: Resultado da análise de clusters para municípios
- **clusters_escolas.csv**: Resultado da análise de clusters para escolas
- **perfis_abandono.csv**: Caracterização dos perfis de estudantes que abandonam
- **resultado_modelagem_2022.json**: Resultados do processo de modelagem preditiva

### Modelagem Preditiva

- **models/modelo_random_forest.joblib**: Modelo Random Forest serializado
- **models/modelo_gradient_boosting.joblib**: Modelo Gradient Boosting serializado
- **models/modelo_logistic_regression.joblib**: Modelo de Regressão Logística serializado
- **models/metadados_modelo.json**: Metadados do melhor modelo selecionado
- **importancia_features.csv**: Ranking de importância das variáveis para predição

### Dados Geoespaciais

- **clusters_espaciais.csv**: Resultado da análise de autocorrelação espacial (LISA)
- **indices_espaciais.csv**: Índices de Moran e outras métricas de associação espacial

## Estrutura dos Principais Resultados

### perfis_abandono.csv

- **PERFIL_ID**: Identificador do perfil (1-4)
- **NOME_PERFIL**: Nome atribuído ao perfil
- **PERCENTUAL**: Percentual de estudantes neste perfil
- **[Variáveis de caracterização]**: Valores médios das variáveis para cada perfil

### importancia_features.csv

- **feature**: Nome da variável
- **importance**: Pontuação de importância relativa
- **rank**: Posição no ranking de importância
- **p_value**: P-valor associado (quando aplicável)

## Metodologia

- **Técnicas de Clustering**: K-means e Análise de Cluster Hierárquica
- **Modelos Preditivos**: Random Forest, Gradient Boosting, Regressão Logística
- **Métricas de Avaliação**: Acurácia, Precisão, Recall, F1, AUC-ROC
- **Validação**: Validação cruzada k-fold com k=5

## Principais Descobertas

- Identificação de 4 perfis distintos de estudantes que abandonam a escola
- Modelo preditivo com acurácia de 83% na identificação precoce
- Infraestrutura escolar e formação docente como fatores protetores significativos
- Primeiro ano do ensino médio como período crítico (45,2% dos casos)
- Atividades extracurriculares reduzem em 42% o risco de abandono
