# Dados para Visualização no Looker Studio

Este diretório contém os arquivos CSV processados para importação no Looker Studio, possibilitando a criação de dashboards interativos sobre o abandono escolar no ensino médio brasileiro.

## Arquivos Disponíveis

- **dados_escolas_looker.csv**: Dados de escolas formatados para visualização
- **dados_municipios_looker.csv**: Dados municipais com indicadores socioeconômicos
- **dados_perfis_looker.csv**: Características dos perfis de abandono identificados
- **importancia_variaveis_looker.csv**: Importância relativa das variáveis no modelo preditivo
- **series_temporais_looker.csv**: Séries históricas para análise de tendências
- **metadados.json**: Informações sobre os dados exportados
- **README.md**: Este arquivo de documentação

## Estrutura de Dados para o Dashboard

Os dados foram estruturados em formatos específicos para facilitar a criação dos seguintes componentes visuais:

### 1. Mapa Coroplético de Taxa de Abandono
- **Nível Geográfico**: UF e Município
- **Métricas Principais**: Taxa de abandono, Total de alunos
- **Filtros Disponíveis**: Região, Dependência Administrativa, Ano

### 2. Distribuição de Escolas por Taxa de Abandono
- **Agrupamento**: Faixas de abandono (Baixo, Médio, Alto, Muito Alto)
- **Detalhamento**: Dependência administrativa, Localização, Região

### 3. Correlações com Abandono Escolar
- **Variáveis Socioeconômicas**: PIB per capita, Taxa de pobreza, Índice de Gini
- **Variáveis Educacionais**: IDEB, Distorção idade-série, Adequação docente

### 4. Visualização de Perfis de Abandono
- **Perfil 1**: Acadêmico-Vulnerável
- **Perfil 2**: Trabalho-Estudo
- **Perfil 3**: Desmotivacional
- **Perfil 4**: Circunstancial-Familiar

### 5. Simulador de Intervenções
- **Inputs**: Tipo de intervenção, Cobertura, Intensidade
- **Outputs**: Redução potencial, Custo-benefício, Impacto regional

## Instruções para Importação

1. Acesse o [Looker Studio](https://lookerstudio.google.com/)
2. Clique em "Criar" e selecione "Relatório"
3. Selecione "Upload de arquivo" como fonte de dados
4. Importe os arquivos CSV disponíveis neste diretório
5. Configure as visualizações conforme necessário

## Modelos de Visualização Recomendados

### Para Análise Regional
- Mapa coroplético
- Gráfico de barras empilhadas
- Cartões de indicadores-chave

### Para Análise de Perfis
- Gráficos de radar
- Diagramas de dispersão
- Gráficos de colunas

### Para Modelagem Preditiva
- Gráficos de importância de variáveis
- Matriz de confusão
- Curva ROC

## Observações

- Os dados estão em formato CSV com delimitador vírgula
- Todos os valores percentuais estão em escala de 0-100 (não 0-1)
- Campos numéricos usam ponto como separador decimal
- Campos de texto estão entre aspas duplas quando contêm vírgulas
