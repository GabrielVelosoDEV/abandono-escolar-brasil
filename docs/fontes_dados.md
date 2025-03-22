# Levantamento Sistemático de Fontes de Dados para Análise do Abandono Escolar no Ensino Médio Brasileiro

## 1. Critérios Metodológicos para Seleção e Avaliação de Fontes

A identificação e seleção das fontes de dados para este estudo fundamentou-se em critérios metodológicos rigorosos, visando garantir a validade, confiabilidade e abrangência das análises subsequentes. Os critérios aplicados foram:

a) **Validade**: Capacidade dos dados de mensurar adequadamente os fenômenos de interesse, com definições operacionais consistentes e metodologias robustas.

b) **Confiabilidade**: Consistência e estabilidade das medidas ao longo do tempo e entre diferentes contextos, permitindo comparabilidade adequada.

c) **Abrangência**: Cobertura geográfica e populacional representativa, minimizando vieses de seleção que comprometeriam generalizações.

d) **Granularidade**: Nível de desagregação que permita análises específicas por territórios, instituições e perfis estudantis.

e) **Temporalidade**: Disponibilidade de séries históricas para análises longitudinais e identificação de tendências.

f) **Acessibilidade**: Dados de acesso público, não confidenciais, em conformidade com princípios éticos de pesquisa.

g) **Interoperabilidade**: Possibilidade de integração com outras fontes através de identificadores comuns ou variáveis estruturantes.

Cada fonte potencial foi submetida a avaliação sistemática segundo estes critérios, resultando na matriz de fontes apresentada a seguir.

## 2. Fontes Primárias Selecionadas

### 2.1 Censo Escolar (INEP)

**Descrição**: Levantamento estatístico anual coordenado pelo Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira (INEP), que coleta dados sobre estabelecimentos, matrículas, funções docentes, movimento e rendimento escolar em todas as escolas públicas e privadas do país.

**Tipo de dados**: Microdados estruturados em formato CSV, organizados em tabelas relacionais.

**Conteúdo relevante**:
- Taxa de abandono por escola, município e estado
- Características institucionais (infraestrutura, dependência administrativa, localização)
- Perfil docente (formação, vínculo, carga horária)
- Características das turmas (tamanho, turno, modalidade)
- Perfil dos estudantes (sexo, raça/cor, idade)
- Distorção idade-série

**Granularidade**: Dados disponíveis nos níveis de estudante, turma, escola, município, estado e região.

**Periodicidade**: Anual, com séries históricas desde 1995 (com modificações metodológicas relevantes em 2007).

**Método de acesso**: Download direto pelo portal do INEP (https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/censo-escolar), em formato CSV com documentação metodológica.

**Protocolo de extração**:
```python
import pandas as pd
import os
import zipfile

def extrair_censo_escolar(ano, caminho_download):
    """
    Função para extrair e processar dados do Censo Escolar
    
    Parâmetros:
    ano (int): Ano do Censo Escolar a ser processado
    caminho_download (str): Caminho onde o arquivo ZIP está armazenado
    
    Retorna:
    DataFrame com dados processados
    """
    # Definir caminho do arquivo
    arquivo_zip = f"{caminho_download}/microdados_censo_escolar_{ano}.zip"
    
    # Verificar se arquivo existe
    if not os.path.exists(arquivo_zip):
        raise FileNotFoundError(f"Arquivo {arquivo_zip} não encontrado")
    
    # Extrair arquivos relevantes
    with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
        # Localizar arquivos de matrícula e escola
        arquivos = [f for f in zip_ref.namelist() if 
                   ('matricula' in f.lower() and f.endswith('.csv')) or 
                   ('escola' in f.lower() and f.endswith('.csv'))]
        
        # Extrair para diretório temporário
        diretorio_temp = f"{caminho_download}/temp_{ano}"
        os.makedirs(diretorio_temp, exist_ok=True)
        
        for arquivo in arquivos:
            zip_ref.extract(arquivo, diretorio_temp)
    
    # Carregar dados de matrícula
    arquivo_matricula = [f for f in os.listdir(diretorio_temp) if 'matricula' in f.lower() and f.endswith('.csv')][0]
    caminho_matricula = os.path.join(diretorio_temp, arquivo_matricula)
    
    # Identificar separador correto (pode variar entre anos)
    with open(caminho_matricula, 'r', encoding='latin-1') as f:
        primeira_linha = f.readline()
        if '|' in primeira_linha:
            separador = '|'
        elif ';' in primeira_linha:
            separador = ';'
        else:
            separador = ','
    
    # Carregar apenas colunas relevantes para análise de abandono
    colunas_relevantes = [
        'NU_ANO_CENSO', 'CO_UF', 'CO_MUNICIPIO', 'CO_ENTIDADE', 
        'TP_DEPENDENCIA', 'TP_LOCALIZACAO', 'TP_SEXO', 'TP_COR_RACA',
        'NU_IDADE', 'TP_ETAPA_ENSINO', 'IN_TRANSPORTE_PUBLICO',
        'TP_SITUACAO_ALUNO'
    ]
    
    # Verificar se todas as colunas existem neste ano específico
    df_test = pd.read_csv(caminho_matricula, sep=separador, encoding='latin-1', nrows=5)
    colunas_existentes = [col for col in colunas_relevantes if col in df_test.columns]
    
    # Carregar dados com as colunas existentes
    df_matricula = pd.read_csv(
        caminho_matricula, 
        sep=separador, 
        encoding='latin-1',
        usecols=colunas_existentes
    )
    
    # Filtrar apenas ensino médio (códigos podem variar entre anos)
    if ano >= 2020:
        codigos_ensino_medio = [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38]
    else:
        codigos_ensino_medio = [25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37]
    
    df_ensino_medio = df_matricula[df_matricula['TP_ETAPA_ENSINO'].isin(codigos_ensino_medio)]
    
    # Criar indicador de abandono
    # Códigos de situação: 1 = Aprovado, 2 = Reprovado, 3 = Transferido, 4 = Abandono
    if 'TP_SITUACAO_ALUNO' in df_ensino_medio.columns:
        df_ensino_medio['ABANDONO'] = df_ensino_medio['TP_SITUACAO_ALUNO'].apply(
            lambda x: 1 if x == 4 else 0
        )
    
    # Limpar diretório temporário
    for arquivo in os.listdir(diretorio_temp):
        os.remove(os.path.join(diretorio_temp, arquivo))
    os.rmdir(diretorio_temp)
    
    return df_ensino_medio
```

**Limitações**: 
- Dados autodeclarados pelas escolas, sujeitos a subnotificação ou erro de preenchimento
- Definição operacional limitada de abandono (sem distinção de causas ou circunstâncias)
- Foco em aspectos quantitativos, com limitada capacidade de capturar dimensões qualitativas

**Avaliação**: Fonte primordial para análise do abandono escolar, oferecendo cobertura universal e granularidade adequada. Principal limitação reside na ausência de informações sobre motivações e circunstâncias do abandono.

### 2.2 SAEB - Sistema de Avaliação da Educação Básica (INEP)

**Descrição**: Conjunto de avaliações externas em larga escala que permite realizar diagnóstico da educação básica brasileira, aferindo tanto proficiência dos estudantes quanto fatores contextuais associados ao desempenho escolar.

**Tipo de dados**: Microdados estruturados (formatos CSV, SPSS) incluindo resultados de testes padronizados e questionários contextuais.

**Conteúdo relevante**:
- Proficiência em Língua Portuguesa e Matemática
- Questionários contextuais de estudantes (perfil socioeconômico, hábitos de estudo, motivação)
- Questionários de professores (formação, práticas pedagógicas, condições de trabalho)
- Questionários de diretores (gestão, clima escolar, infraestrutura)
- Questionários de escola (condições de infraestrutura, recursos pedagógicos)

**Granularidade**: Dados no nível do estudante, professor, diretor e escola, com possibilidade de agregação geográfica.

**Periodicidade**: Bienal (anos ímpares), com séries desde 1995 (com modificações metodológicas relevantes em 2005 e 2017).

**Método de acesso**: Download direto pelo portal do INEP (https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/saeb), em formato ZIP contendo múltiplos arquivos.

**Protocolo de extração**:
```python
import pandas as pd
import zipfile
import os

def extrair_saeb(ano, caminho_download):
    """
    Função para extrair e processar dados do SAEB
    
    Parâmetros:
    ano (int): Ano da avaliação SAEB
    caminho_download (str): Caminho onde o arquivo ZIP está armazenado
    
    Retorna:
    Dict com DataFrames processados (alunos, escolas, professores, diretores)
    """
    # Definir caminho do arquivo
    arquivo_zip = f"{caminho_download}/microdados_saeb_{ano}.zip"
    
    # Verificar se arquivo existe
    if not os.path.exists(arquivo_zip):
        raise FileNotFoundError(f"Arquivo {arquivo_zip} não encontrado")
    
    # Extrair arquivos para diretório temporário
    diretorio_temp = f"{caminho_download}/temp_saeb_{ano}"
    os.makedirs(diretorio_temp, exist_ok=True)
    
    with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
        zip_ref.extractall(diretorio_temp)
    
    # Localizar arquivos de interesse (foco no ensino médio)
    arquivos_interesse = {
        'alunos': None,
        'escolas': None,
        'professores': None,
        'diretores': None
    }
    
    # Procurar recursivamente pelos arquivos de interesse
    for root, dirs, files in os.walk(diretorio_temp):
        for file in files:
            caminho_completo = os.path.join(root, file)
            
            # Identificar tipo de arquivo
            file_lower = file.lower()
            if 'aluno' in file_lower and ('ensino medio' in file_lower or 'em' in file_lower) and file.endswith(('.csv', '.CSV')):
                arquivos_interesse['alunos'] = caminho_completo
            elif 'escola' in file_lower and file.endswith(('.csv', '.CSV')):
                arquivos_interesse['escolas'] = caminho_completo
            elif 'professor' in file_lower and file.endswith(('.csv', '.CSV')):
                arquivos_interesse['professores'] = caminho_completo
            elif 'diretor' in file_lower and file.endswith(('.csv', '.CSV')):
                arquivos_interesse['diretores'] = caminho_completo
    
    # Carregar os dados encontrados
    resultados = {}
    
    for tipo, caminho in arquivos_interesse.items():
        if caminho:
            # Testar o separador
            with open(caminho, 'r', encoding='latin-1') as f:
                primeira_linha = f.readline()
                if '|' in primeira_linha:
                    separador = '|'
                elif ';' in primeira_linha:
                    separador = ';'
                else:
                    separador = ','
            
            # Carregar os dados
            try:
                df = pd.read_csv(caminho, sep=separador, encoding='latin-1')
                resultados[tipo] = df
            except Exception as e:
                print(f"Erro ao carregar {tipo}: {e}")
    
    # Limpar diretório temporário
    for root, dirs, files in os.walk(diretorio_temp, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))
    os.rmdir(diretorio_temp)
    
    return resultados
```

**Limitações**:
- Avaliação centrada em 3º ano do ensino médio, não capturando adequadamente estudantes que abandonam nos anos anteriores
- Potencial viés de seleção, pois estudantes ausentes (potencialmente em risco de abandono) não são avaliados
- Nem todas as escolas são avaliadas em cada edição, limitando análises longitudinais em nível institucional

**Avaliação**: Fonte complementar valiosa, especialmente para fatores contextuais associados ao desempenho e potencialmente ao abandono. Principais contribuições incluem informações sobre clima escolar, práticas pedagógicas e perfil socioeconômico detalhado.

### 2.3 PNAD Contínua - Módulo Educação (IBGE)

**Descrição**: Pesquisa por amostra de domicílios que investiga diversas características socioeconômicas da população brasileira, incluindo educação. O módulo educacional, divulgado anualmente, apresenta dados específicos sobre acesso, permanência e motivações de não frequência à escola.

**Tipo de dados**: Microdados estruturados em formatos CSV, SAS e SPSS, com documentação metodológica detalhada.

**Conteúdo relevante**:
- Frequência escolar por faixa etária
- Motivos declarados para não frequência à escola
- Nível de escolaridade da população
- Características socioeconômicas detalhadas (renda, ocupação, condições de moradia)
- Composição familiar
- Intersecções com mercado de trabalho

**Granularidade**: Dados no nível individual e domiciliar, com possibilidade de agregação por UF e grandes regiões. Representatividade municipal apenas para capitais.

**Periodicidade**: Anual para o módulo educacional específico (2º trimestre), com série desde 2016.

**Método de acesso**: Download direto pelo portal do IBGE (https://www.ibge.gov.br/estatisticas/sociais/trabalho/17270-pnad-continua.html), em formatos diversos.

**Protocolo de extração**:
```python
import pandas as pd
import os
import zipfile

def extrair_pnad_educacao(ano, caminho_download):
    """
    Função para extrair e processar dados do módulo de educação da PNAD Contínua
    
    Parâmetros:
    ano (int): Ano da PNAD
    caminho_download (str): Caminho onde o arquivo ZIP está armazenado
    
    Retorna:
    DataFrame com dados relevantes para análise de abandono escolar
    """
    # Definir caminho do arquivo
    arquivo_zip = f"{caminho_download}/PNAD_Continua_Educacao_{ano}.zip"
    
    # Verificar se arquivo existe
    if not os.path.exists(arquivo_zip):
        raise FileNotFoundError(f"Arquivo {arquivo_zip} não encontrado")
    
    # Extrair arquivos
    diretorio_temp = f"{caminho_download}/temp_pnad_{ano}"
    os.makedirs(diretorio_temp, exist_ok=True)
    
    with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
        zip_ref.extractall(diretorio_temp)
    
    # Encontrar o arquivo de microdados
    arquivos_csv = [f for f in os.listdir(diretorio_temp) if f.endswith('.csv')]
    
    if not arquivos_csv:
        raise FileNotFoundError("Nenhum arquivo CSV encontrado no arquivo ZIP")
    
    # Geralmente há apenas um arquivo CSV principal
    arquivo_principal = os.path.join(diretorio_temp, arquivos_csv[0])
    
    # Carregar os dados com foco em variáveis relevantes para abandono escolar
    # As variáveis podem mudar entre anos, verificar dicionário específico
    colunas_interesse = [
        'UF', 'V2007', 'V2009', 'V2010',  # UF, sexo, idade, cor/raça
        'V3001', 'V3002', 'V3003A', 'V3006', 'V3007',  # Frequência escolar e nível
        'V3004', 'V3005',  # Motivo de não frequência
        'V5001A', 'V5002A',  # Trabalho
        'VD5004', 'VD5005', 'VD5006',  # Rendimentos
        'V2001', 'V2002', 'V2005'  # Características do domicílio
    ]
    
    # Verificar quais colunas existem neste ano específico
    df_test = pd.read_csv(arquivo_principal, sep=';', encoding='latin-1', nrows=5)
    colunas_existentes = [col for col in colunas_interesse if col in df_test.columns]
    
    # Carregar apenas as colunas que existem
    df_pnad = pd.read_csv(
        arquivo_principal,
        sep=';',
        encoding='latin-1',
        usecols=colunas_existentes
    )
    
    # Filtrar para faixa etária do ensino médio (15 a 19 anos)
    if 'V2009' in df_pnad.columns:  # Coluna de idade
        df_pnad = df_pnad[(df_pnad['V2009'] >= 15) & (df_pnad['V2009'] <= 19)]
    
    # Limpar diretório temporário
    for arquivo in os.listdir(diretorio_temp):
        os.remove(os.path.join(diretorio_temp, arquivo))
    os.rmdir(diretorio_temp)
    
    return df_pnad
```

**Limitações**:
- Amostragem não permite desagregação para municípios menores ou escolas específicas
- Informações sobre motivos de não frequência são autodeclaradas e categorizadas de forma genérica
- Desenho transversal limita análises de trajetórias educacionais completas

**Avaliação**: Fonte extremamente valiosa para análise de motivos de abandono e contexto socioeconômico, permitindo conexões entre educação, trabalho e condições familiares. Complementa adequadamente as limitações do Censo Escolar quanto às motivações do abandono.

### 2.4 Indicadores Educacionais do INEP

**Descrição**: Conjunto consolidado de indicadores calculados a partir de dados do Censo Escolar, apresentando estatísticas educacionais em diferentes níveis de agregação, com metodologias padronizadas.

**Tipo de dados**: Dados agregados estruturados em formato CSV e Excel.

**Conteúdo relevante**:
- Taxas de rendimento (aprovação, reprovação, abandono)
- Distorção idade-série
- Média de alunos por turma
- Complexidade de gestão escolar
- Adequação da formação docente
- INSE (Indicador de Nível Socioeconômico das Escolas)

**Granularidade**: Disponível nos níveis escola, município, estado e país.

**Periodicidade**: Anual, com séries históricas desde 2007 (com algumas variações dependendo do indicador específico).

**Método de acesso**: Download direto pelo portal do INEP (https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/indicadores-educacionais).

**Protocolo de extração**:
```python
import pandas as pd
import os

def extrair_indicadores_educacionais(ano, indicador, caminho_download):
    """
    Função para extrair e processar indicadores educacionais do INEP
    
    Parâmetros:
    ano (int): Ano dos indicadores
    indicador (str): Tipo de indicador ('rendimento', 'distorcao', 'docente', 'complexidade', 'inse')
    caminho_download (str): Caminho onde o arquivo está armazenado
    
    Retorna:
    DataFrame com os indicadores processados
    """
    # Mapeamento de indicadores para nomes de arquivos (padrão pode variar entre anos)
    mapeamento = {
        'rendimento': f'indicadores_rendimento_{ano}',
        'distorcao': f'indicadores_distorcao_{ano}',
        'docente': f'indicadores_adequacao_docente_{ano}',
        'complexidade': f'indicadores_complexidade_{ano}',
        'inse': f'indicadores_nivel_socioeconomico_{ano}'
    }
    
    if indicador not in mapeamento:
        raise ValueError(f"Indicador {indicador} não reconhecido")
    
    # Tentar diferentes extensões de arquivo
    extensoes = ['.csv', '.xlsx', '.xls']
    arquivo_encontrado = None
    
    for ext in extensoes:
        arquivo_potencial = os.path.join(caminho_download, mapeamento[indicador] + ext)
        if os.path.exists(arquivo_potencial):
            arquivo_encontrado = arquivo_potencial
            break
    
    if not arquivo_encontrado:
        raise FileNotFoundError(f"Não foi encontrado arquivo para {indicador} de {ano}")
    
    # Carregar o arquivo conforme sua extensão
    if arquivo_encontrado.endswith('.csv'):
        # Testar diferentes separadores
        separadores = [',', ';', '|', '\t']
        for sep in separadores:
            try:
                df = pd.read_csv(arquivo_encontrado, sep=sep, encoding='latin-1')
                # Se conseguiu ler pelo menos uma coluna, considera sucesso
                if len(df.columns) > 1:
                    break
            except:
                continue
    else:  # Excel
        df = pd.read_excel(arquivo_encontrado)
    
    # Filtrar apenas ensino médio se existir coluna de etapa
    colunas_etapa = [col for col in df.columns if 'etapa' in col.lower()]
    if colunas_etapa:
        coluna_etapa = colunas_etapa[0]
        # Códigos ou nomes para ensino médio podem variar
        filtros_em = ['Ensino Médio', 'ENSINO MÉDIO', 'Médio', 'MÉDIO', 3]
        for filtro in filtros_em:
            try:
                df_filtrado = df[df[coluna_etapa] == filtro]
                if not df_filtrado.empty:
                    df = df_filtrado
                    break
            except:
                continue
    
    return df
```

**Limitações**:
- Dados agregados limitam análises individualizadas
- Metodologias de cálculo podem variar entre períodos, afetando comparabilidade temporal
- Indicadores sintéticos podem obscurecer detalhes relevantes para compreensão dos fenômenos

**Avaliação**: Fonte extremamente útil para análises comparativas e evolutivas, com metodologia padronizada e ampla cobertura territorial. Particularmente relevante para contextualizações iniciais e identificação de tendências.

### 2.5 Microdados do ENEM 

**Descrição**: Base de dados com informações sobre participantes do Exame Nacional do Ensino Médio, incluindo resultados, respostas ao questionário socioeconômico e dados do percurso escolar declarado.

**Tipo de dados**: Microdados estruturados em formato CSV.

**Conteúdo relevante**:
- Desempenho nas áreas de conhecimento avaliadas
- Perfil socioeconômico detalhado dos participantes
- Características familiares (escolaridade dos pais, renda familiar)
- Trajetória escolar pregressa (tipo de escola, reprovações)
- Acesso a bens culturais e tecnológicos

**Granularidade**: Dados no nível individual, com possibilidade de agregação geográfica.

**Periodicidade**: Anual, com séries desde 1998 (com modificações metodológicas significativas em 2009 e 2017).

**Método de acesso**: Download direto pelo portal do INEP (https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados/enem).

**Protocolo de extração**:
```python
import pandas as pd
import os
import zipfile

def extrair_enem(ano, caminho_download, amostra=0.1):
    """
    Função para extrair e processar microdados do ENEM
    
    Parâmetros:
    ano (int): Ano do ENEM
    caminho_download (str): Caminho onde o arquivo ZIP está armazenado
    amostra (float): Proporção da amostra a ser extraída (para arquivos muito grandes)
    
    Retorna:
    DataFrame com dados relevantes para análise de abandono escolar
    """
    # Definir caminho do arquivo
    arquivo_zip = f"{caminho_download}/microdados_enem_{ano}.zip"
    
    # Verificar se arquivo existe
    if not os.path.exists(arquivo_zip):
        raise FileNotFoundError(f"Arquivo {arquivo_zip} não encontrado")
    
    # Extrair arquivos
    diretorio_temp = f"{caminho_download}/temp_enem_{ano}"
    os.makedirs(diretorio_temp, exist_ok=True)
    
    with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
        # Extrair apenas o arquivo principal de microdados
        arquivos = [f for f in zip_ref.namelist() if f.endswith('.csv') and 'microdados' in f.lower()]
        if not arquivos:
            raise FileNotFoundError("Arquivo CSV de microdados não encontrado no ZIP")
        
        for arquivo in arquivos:
            zip_ref.extract(arquivo, diretorio_temp)
    
    # Encontrar o arquivo CSV extraído
    arquivos_csv = [f for f in os.listdir(diretorio_temp) if f.endswith('.csv')]
    if not arquivos_csv:
        raise FileNotFoundError("Arquivo CSV não encontrado após extração")
    
    arquivo_microdados = os.path.join(diretorio_temp, arquivos_csv[0])
    
    # Identificar colunas relevantes para análise de abandono
    # Estas colunas podem variar entre anos, verificar dicionário específico
    colunas_interesse = [
        # Identificação e demográficas
        'NU_INSCRICAO', 'TP_SEXO', 'NU_IDADE', 'TP_COR_RACA', 'TP_ESTADO_CIVIL',
        'TP_NACIONALIDADE', 'SG_UF_NASCIMENTO', 'TP_ST_CONCLUSAO',
        
        # Escola
        'TP_ESCOLA', 'TP_ENSINO', 'IN_TREINEIRO',
        
        # Socioeconômicas (variam conforme o ano)
        'Q001', 'Q002', 'Q003', 'Q004', 'Q005', 'Q006', 'Q007', 'Q008', 'Q009', 'Q010',
        'Q011', 'Q012', 'Q013', 'Q014', 'Q015', 'Q016', 'Q017', 'Q018', 'Q019', 'Q020',
        'Q021', 'Q022', 'Q023', 'Q024', 'Q025',
        
        # Desempenho
        'NU_NOTA_CN', 'NU_NOTA_CH', 'NU_NOTA_LC', 'NU_NOTA_MT', 'NU_NOTA_REDACAO'
    ]
    
    # Verificar quais colunas existem neste ano específico
    # Usando o método nrows para ler apenas algumas linhas inicialmente
    df_test = pd.read_csv(arquivo_microdados, sep=';', encoding='latin-1', nrows=5)
    colunas_existentes = [col for col in colunas_interesse if col in df_test.columns]
    
    # Ler uma amostra aleatória para processamento mais rápido (dados são muito grandes)
    df_enem = pd.read_csv(
        arquivo_microdados,
        sep=';',
        encoding='latin-1',
        usecols=colunas_existentes,
        skiprows=lambda x: x > 0 and pd.np.random.random() > amostra
    )
    
    # Filtrar apenas concluintes e não-treineiros
    if 'IN_TREINEIRO' in df_enem.columns:
        df_enem = df_enem[df_enem['IN_TREINEIRO'] == 0]
    
    if 'TP_ST_CONCLUSAO' in df_enem.columns:
        # Códigos podem variar entre anos
        # Geralmente: 1 = Já concluiu, 2 = Está concluindo no ano
        df_enem = df_enem[df_enem['TP_ST_CONCLUSAO'].isin([1, 2])]
    
    # Limpar diretório temporário
    for arquivo in os.listdir(diretorio_temp):
        os.remove(os.path.join(diretorio_temp, arquivo))
    os.rmdir(diretorio_temp)
    
    return df_enem
```

**Limitações**:
- Viés de seleção significativo, pois contempla apenas estudantes que optaram por realizar o exame
- Sub-representação de estudantes que abandonaram a escola precocemente
- Informações autodeclaradas sujeitas a imprecisões

**Avaliação**: Fonte complementar valiosa para análise de perfil socioeconômico detalhado e trajetória escolar, especialmente para compreensão de fatores associados à conclusão bem-sucedida. Deve ser utilizada com cautela devido ao viés de seleção inerente.

## 3. Fontes Complementares

### 3.1 Atlas do Desenvolvimento Humano no Brasil (PNUD)

**Descrição**: Plataforma que disponibiliza indicadores de desenvolvimento humano calculados a partir de dados censitários, incluindo dimensões de educação, renda e longevidade.

**Tipo de dados**: Dados agregados estruturados (XLS, CSV).

**Conteúdo relevante**:
- IDHM Educação e seus componentes
- Indicadores de escolaridade da população adulta
- Indicadores de fluxo escolar (adequação idade-série)
- Expectativa de anos de estudo
- Indicadores socioeconômicos contextuais

**Granularidade**: Dados municipais, estaduais e para regiões metropolitanas.

**Periodicidade**: Associada aos Censos Demográficos (2000, 2010).

**Método de acesso**: Download direto pelo portal (http://www.atlasbrasil.org.br/).

**Limitações**: Periodicidade limitada e defasagem temporal significativa.

**Avaliação**: Fonte valiosa para contextualização socioeconômica territorial, permitindo associações entre abandono escolar e características estruturais dos municípios.

### 3.2 SIOPE - Sistema de Informações sobre Orçamentos Públicos em Educação

**Descrição**: Sistema que coleta, processa e disponibiliza dados sobre receitas e investimentos públicos em educação nos diferentes níveis administrativos.

**Tipo de dados**: Dados estruturados em formato CSV e Excel.

**Conteúdo relevante**:
- Investimento por aluno
- Percentual de recursos aplicados em educação
- Distribuição de investimentos por categoria
- Detalhamento de despesas educacionais

**Granularidade**: Federal, estadual e municipal.

**Periodicidade**: Anual, com séries desde 2006.

**Método de acesso**: Consulta online e exportação de relatórios (https://www.fnde.gov.br/siope/).

**Limitações**: Limitações na padronização de categorias entre entes federativos.

**Avaliação**: Fonte relevante para análises da relação entre investimento educacional e taxas de abandono, especialmente em estudos comparativos entre redes de ensino.

### 3.3 QEdu

**Descrição**: Portal que organiza e disponibiliza dados educacionais brasileiros em formato acessível, com foco na educação básica.

**Tipo de dados**: Dados agregados estruturados com visualizações interativas.

**Conteúdo relevante**:
- Taxas de aprovação, reprovação e abandono
- Distorção idade-série
- Indicadores de aprendizagem
- Perfil de escolas e redes

**Granularidade**: Escola, município, estado e país.

**Periodicidade**: Anual, com séries desde 2010.

**Método de acesso**: API REST e download direto (https://www.qedu.org.br/).

**Limitações**: Dados derivados de outras fontes primárias, sem informações exclusivas.

**Avaliação**: Fonte secundária útil para visualizações preliminares e exploração inicial de dados, com interface amigável e boas opções de filtros.

## 4. Estratégia de Integração de Fontes

A análise abrangente do abandono escolar requer integração metodologicamente robusta das diversas fontes identificadas, permitindo complementaridade e triangulação de evidências. A estratégia de integração proposta compreende:

### 4.1 Harmonização de Definições e Variáveis

a) **Padronização conceitual**: Estabelecimento de definições operacionais consistentes para fenômenos-chave (abandono, evasão, desempenho).

b) **Correspondência entre variáveis**: Mapeamento sistemático de variáveis equivalentes entre diferentes bases, com documentação de diferenças metodológicas.

c) **Normalização de escalas**: Transformação de indicadores em escalas comparáveis quando necessário (z-scores, percentis).

### 4.2 Estratégia de Vinculação de Registros

a) **Identificadores comuns**: Utilização de códigos padronizados (INEP para escolas, IBGE para municípios) como chaves de integração.

b) **Agregação multinível**: Implementação de estrutura hierárquica que permita análises nos níveis individual, escolar, municipal e estadual.

c) **Temporalidade**: Alinhamento de recortes temporais considerando defasagens entre coletas e diferentes periodicidades.

### 4.3 Protocolo de Integração Específico

```python
def integrar_fontes_abandono(ano_referencia, caminho_dados):
    """
    Função para integrar múltiplas fontes de dados sobre abandono escolar
    
    Parâmetros:
    ano_referencia (int): Ano base para integração
    caminho_dados (str): Diretório com dados processados
    
    Retorna:
    Dict com DataFrames integrados em diferentes níveis
    """
    resultados = {}
    
    # 1. Carregar dados do Censo Escolar (nível escola)
    df_censo = pd.read_csv(f"{caminho_dados}/censo_escolar_{ano_referencia}_processado.csv")
    
    # 2. Carregar indicadores educacionais
    df_indicadores = pd.read_csv(f"{caminho_dados}/indicadores_{ano_referencia}_processado.csv")
    
    # 3. Carregar dados do SAEB se disponível (anos ímpares)
    if ano_referencia % 2 == 1:  # Anos ímpares têm SAEB
        df_saeb_escola = pd.read_csv(f"{caminho_dados}/saeb_{ano_referencia}_escola_processado.csv")
        # Integrar com dados do Censo por código da escola
        df_escola_integrado = pd.merge(
            df_censo,
            df_saeb_escola,
            on='CO_ENTIDADE',
            how='left',
            suffixes=('_censo', '_saeb')
        )
    else:
        df_escola_integrado = df_censo
    
    # 4. Integrar com indicadores educacionais
    df_escola_integrado = pd.merge(
        df_escola_integrado,
        df_indicadores,
        on='CO_ENTIDADE',
        how='left'
    )
    
    # 5. Agregar para nível municipal
    df_municipio = df_escola_integrado.groupby('CO_MUNICIPIO').agg({
        'ABANDONO': 'mean',
        'QT_MAT_BAS': 'sum',
        'QT_ABANDONO': 'sum',
        # Outras agregações relevantes
    }).reset_index()
    
    # 6. Integrar com dados da PNAD (nível UF)
    df_pnad = pd.read_csv(f"{caminho_dados}/pnad_{ano_referencia}_processado.csv")
    
    # Agregar PNAD para nível UF
    df_pnad_uf = df_pnad.groupby('UF').agg({
        # Agregações relevantes
    }).reset_index()
    
    # 7. Integrar com dados municipais do Atlas Brasil
    df_atlas = pd.read_csv(f"{caminho_dados}/atlas_brasil_municipios.csv")
    
    df_municipio_integrado = pd.merge(
        df_municipio,
        df_atlas,
        on='CO_MUNICIPIO',
        how='left'
    )
    
    # 8. Integrar dados do SIOPE
    df_siope = pd.read_csv(f"{caminho_dados}/siope_{ano_referencia}_processado.csv")
    
    df_municipio_integrado = pd.merge(
        df_municipio_integrado,
        df_siope,
        on='CO_MUNICIPIO',
        how='left'
    )
    
    # Armazenar resultados em diferentes níveis
    resultados['escola'] = df_escola_integrado
    resultados['municipio'] = df_municipio_integrado
    
    # 9. Agregação para nível UF
    df_uf = df_municipio_integrado.groupby('CO_UF').agg({
        # Agregações relevantes
    }).reset_index()
    
    # Integrar com dados PNAD no nível UF
    df_uf_integrado = pd.merge(
        df_uf,
        df_pnad_uf,
        left_on='CO_UF',
        right_on='UF',
        how='left'
    )
    
    resultados['uf'] = df_uf_integrado
    
    return resultados
```

## 5. Matriz de Avaliação das Fontes

A tabela abaixo sintetiza a avaliação das fontes principais segundo os critérios metodológicos estabelecidos, em escala de 1 (muito baixo) a 5 (muito alto):

| Fonte de Dados | Validade | Confiabilidade | Abrangência | Granularidade | Temporalidade | Acessibilidade | Interoperabilidade | Média |
|----------------|----------|---------------|-------------|--------------|--------------|---------------|-------------------|-------|
| Censo Escolar | 5 | 4 | 5 | 5 | 5 | 5 | 5 | 4.9 |
| SAEB | 4 | 4 | 3 | 4 | 3 | 5 | 4 | 3.9 |
| PNAD Contínua | 4 | 5 | 4 | 3 | 4 | 5 | 3 | 4.0 |
| Indicadores Educacionais | 5 | 5 | 5 | 4 | 5 | 5 | 5 | 4.9 |
| Microdados ENEM | 3 | 4 | 3 | 5 | 5 | 5 | 3 | 4.0 |
| Atlas do Desenvolvimento | 4 | 5 | 5 | 3 | 2 | 5 | 4 | 4.0 |
| SIOPE | 3 | 4 | 5 | 3 | 4 | 4 | 3 | 3.7 |

## 6. Considerações Finais

O levantamento sistemático de fontes de dados para análise do abandono escolar evidencia a disponibilidade de um conjunto robusto e complementar de repositórios públicos que, quando adequadamente integrados, permitem análise abrangente e multidimensional do fenômeno. A triangulação entre diferentes fontes possibilita superar limitações específicas de cada repositório isoladamente.

A estratégia metodológica proposta prioriza a complementaridade entre fontes, explorando as potencialidades específicas de cada base: o Censo Escolar como fonte primária para quantificação e distribuição do fenômeno; o SAEB e o ENEM para fatores associados ao desempenho e perfil socioeconômico detalhado; a PNAD para motivos declarados e contexto familiar; e as demais fontes para enriquecimento contextual.

Limitações importantes permanecem, notadamente: a) escassez de dados longitudinais que permitam acompanhamento de trajetórias individuais completas; b) informações limitadas sobre motivações específicas do abandono no nível individual; e c) ausência de dados qualitativos sistematizados que capturem dimensões subjetivas do fenômeno. Tais limitações apontam para a necessidade de complementação futura com estudos qualitativos focalizados.

A matriz de fontes e protocolos apresentados, contudo, fornece base metodologicamente robusta para análises quantitativas abrangentes, constituindo fundamento empírico sólido para compreensão do abandono escolar e formulação de intervenções baseadas em evidências.

## Referências Bibliográficas

ALVES, M. T. G.; SOARES, J. F. Contexto escolar e indicadores educacionais: condições desiguais para a efetivação de uma política de avaliação educacional. Educação e Pesquisa, v. 39, n. 1, p. 177-194, 2013.

INEP - INSTITUTO NACIONAL DE ESTUDOS E PESQUISAS EDUCACIONAIS ANÍSIO TEIXEIRA. Censo da Educação Básica 2022: notas estatísticas. Brasília: INEP, 2023.

IBGE - INSTITUTO BRASILEIRO DE GEOGRAFIA E ESTATÍSTICA. Pesquisa Nacional por Amostra de Domicílios Contínua: educação 2022. Rio de Janeiro: IBGE, 2023.

NERI, M. C. O estado da educação no Brasil: uma análise multidimensional. Rio de Janeiro: FGV Social, 2021.

SOARES, T. M. et al. Fatores associados ao abandono escolar no ensino médio público de Minas Gerais. Educação e Pesquisa, v. 41, n. 3, p. 757-772, 2015.

TODOS PELA EDUCAÇÃO. Anuário Brasileiro da Educação Básica 2022. São Paulo: Editora Moderna, 2022.
