# Dados Processados

Este diretório contém os dados processados e integrados utilizados nas análises do abandono escolar no ensino médio brasileiro. Os arquivos são resultantes das etapas de limpeza, transformação e integração das fontes originais.

## Conteúdo

### Dados por Nível de Agregação

- **dados_integrados_escolas_2022.csv**: Dados integrados no nível de escola, com informações do Censo Escolar, SAEB, Indicadores Educacionais
- **dados_integrados_municipios_2022.csv**: Dados agregados por município, com indicadores educacionais e socioeconômicos
- **dados_integrados_estados_2022.csv**: Dados agregados por UF
- **dados_integrados_alunos_2022.csv**: Amostra de dados no nível de aluno para modelagem preditiva

### Dados por Fonte Processada

- **censo_escolar_2022_ensino_medio.csv**: Dados do Censo Escolar filtrados para o ensino médio
- **censo_escolar_2022_agregado_escola.csv**: Dados do Censo Escolar agregados por escola
- **censo_escolar_2022_agregado_municipio.csv**: Dados do Censo Escolar agregados por município
- **pnad_2022_educacao.csv**: Dados da PNAD processados (módulo educação)
- **indicadores_rendimento_2022_processado.csv**: Indicadores de rendimento processados

## Estrutura dos Dados Principais

### dados_integrados_escolas_2022.csv

- **CO_ENTIDADE**: Código da escola
- **CO_MUNICIPIO**: Código do município (IBGE)
- **CO_UF**: Código da UF
- **DEPENDENCIA**: Dependência administrativa (Federal, Estadual, Municipal, Privada)
- **LOCALIZACAO**: Localização (Urbana, Rural)
- **TAXA_ABANDONO**: Percentual de abandono escolar
- **TOTAL_ALUNOS**: Total de alunos matriculados
- **INDICE_INFRAESTRUTURA**: Índice composto de infraestrutura (0-1)
- **PROP_DOC_SUPERIOR**: Proporção de docentes com ensino superior (%)
- **[Demais variáveis]**: Indicadores contextuais e pedagógicos

### dados_integrados_municipios_2022.csv

- **CO_MUNICIPIO**: Código do município (IBGE)
- **CO_UF**: Código da UF
- **REGIAO**: Região geopolítica (Norte, Nordeste, etc.)
- **TAXA_ABANDONO**: Percentual médio de abandono escolar
- **TOTAL_ALUNOS**: Total de alunos matriculados no município
- **TOTAL_ESCOLAS**: Total de escolas no município
- **PIB_PER_CAPITA**: PIB per capita do município
- **TAXA_DESEMPREGO**: Taxa de desemprego (%)
- **IDEB**: Índice de Desenvolvimento da Educação Básica
- **TAXA_POBREZA**: Percentual da população em situação de pobreza
- **INDICE_GINI**: Índice de desigualdade de Gini
- **[Demais variáveis]**: Indicadores contextuais e educacionais

## Processamento Aplicado

- Limpeza de valores ausentes e atípicos
- Normalização e padronização de variáveis
- Integração de múltiplas fontes
- Cálculo de indicadores derivados
- Agregação em diferentes níveis geográficos
- Transformação de variáveis categóricas

## Observações

- Os scripts utilizados para gerar estes dados estão na pasta `/scripts/processamento/`
- Os dados estão em formato CSV com delimitador vírgula
- Encoding: UTF-8
- Uma descrição detalhada de cada variável pode ser encontrada no arquivo `dicionario_dados_integrados.csv`
