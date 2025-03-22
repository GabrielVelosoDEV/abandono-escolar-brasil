# Notebook: Coleta de Dados para Análise do Abandono Escolar

## 1. Introdução

Este notebook implementa o processo de coleta de dados educacionais de múltiplas fontes para análise do abandono escolar no ensino médio brasileiro. As principais fontes utilizadas são:
- Censo Escolar (INEP)
- SAEB (INEP)
- PNAD Contínua - Módulo Educação (IBGE)
- Indicadores Educacionais (INEP)

## 2. Configuração do Ambiente

# Importar bibliotecas necessárias
import pandas as pd
import numpy as np
import os
import zipfile
import requests
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Definir diretórios
BASE_DIR = os.path.dirname(os.path.abspath('__file__'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')

# Criar diretórios se não existirem
for directory in [DATA_DIR, RAW_DIR, PROCESSED_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Função para registrar log
def log_message(message, level="INFO"):
    """Registra mensagens de log com timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

log_message("Ambiente configurado com sucesso")

## 3. Funções para Download de Dados

### 3.1 Censo Escolar (INEP)

def download_censo_escolar(ano, dest_dir=RAW_DIR):
    """
    Função para download dos microdados do Censo Escolar
    
    Args:
        ano (int): Ano de referência do Censo Escolar
        dest_dir (str): Diretório de destino para os arquivos
    
    Returns:
        str: Caminho para o arquivo baixado
    """
    # URL base para download dos microdados do Censo Escolar
    base_url = f"https://download.inep.gov.br/microdados/microdados_censo_escolar_{ano}.zip"
    
    # Nome do arquivo de destino
    filename = f"microdados_censo_escolar_{ano}.zip"
    filepath = os.path.join(dest_dir, filename)
    
    # Verificar se o arquivo já existe
    if os.path.exists(filepath):
        log_message(f"Arquivo {filename} já existe. Pulando download.")
        return filepath
    
    try:
        log_message(f"Iniciando download do Censo Escolar {ano}...")
        # Realizar o download
        response = requests.get(base_url, stream=True)
        response.raise_for_status()
        
        # Salvar o arquivo
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        log_message(f"Download do Censo Escolar {ano} concluído com sucesso.")
        return filepath
    
    except Exception as e:
        log_message(f"Erro ao baixar Censo Escolar {ano}: {str(e)}", "ERROR")
        return None

### 3.2 SAEB (INEP)

def download_saeb(ano, dest_dir=RAW_DIR):
    """
    Função para download dos microdados do SAEB
    
    Args:
        ano (int): Ano de referência do SAEB
        dest_dir (str): Diretório de destino para os arquivos
    
    Returns:
        str: Caminho para o arquivo baixado
    """
    # URL base para download dos microdados do SAEB
    base_url = f"https://download.inep.gov.br/microdados/microdados_saeb_{ano}.zip"
    
    # Nome do arquivo de destino
    filename = f"microdados_saeb_{ano}.zip"
    filepath = os.path.join(dest_dir, filename)
    
    # Verificar se o arquivo já existe
    if os.path.exists(filepath):
        log_message(f"Arquivo {filename} já existe. Pulando download.")
        return filepath
    
    try:
        log_message(f"Iniciando download do SAEB {ano}...")
        # Realizar o download
        response = requests.get(base_url, stream=True)
        response.raise_for_status()
        
        # Salvar o arquivo
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        log_message(f"Download do SAEB {ano} concluído com sucesso.")
        return filepath
    
    except Exception as e:
        log_message(f"Erro ao baixar SAEB {ano}: {str(e)}", "ERROR")
        return None

### 3.3 PNAD Contínua (IBGE)

def download_pnad(ano, dest_dir=RAW_DIR):
    """
    Função para download dos microdados da PNAD Contínua - Módulo Educação
    
    Args:
        ano (int): Ano de referência da PNAD
        dest_dir (str): Diretório de destino para os arquivos
    
    Returns:
        str: Caminho para o arquivo baixado
    """
    # URL base para download dos microdados da PNAD
    base_url = f"https://ftp.ibge.gov.br/Trabalho_e_Rendimento/Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/Microdados/Visita/PNADC_{ano}_visita_5.zip"
    
    # Nome do arquivo de destino
    filename = f"PNAD_Continua_Educacao_{ano}.zip"
    filepath = os.path.join(dest_dir, filename)
    
    # Verificar se o arquivo já existe
    if os.path.exists(filepath):
        log_message(f"Arquivo {filename} já existe. Pulando download.")
        return filepath
    
    try:
        log_message(f"Iniciando download da PNAD {ano}...")
        # Realizar o download
        response = requests.get(base_url, stream=True)
        response.raise_for_status()
        
        # Salvar o arquivo
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        log_message(f"Download da PNAD {ano} concluído com sucesso.")
        return filepath
    
    except Exception as e:
        log_message(f"Erro ao baixar PNAD {ano}: {str(e)}", "ERROR")
        return None

### 3.4 Indicadores Educacionais (INEP)

def download_indicadores(ano, dest_dir=RAW_DIR):
    """
    Função para download dos indicadores educacionais do INEP
    
    Args:
        ano (int): Ano de referência dos indicadores
        dest_dir (str): Diretório de destino para os arquivos
    
    Returns:
        str: Caminho para o arquivo baixado
    """
    # URL base para download dos indicadores educacionais
    base_url = f"https://download.inep.gov.br/informacoes_estatisticas/indicadores_educacionais/indicadores_{ano}.zip"
    
    # Nome do arquivo de destino
    filename = f"indicadores_educacionais_{ano}.zip"
    filepath = os.path.join(dest_dir, filename)
    
    # Verificar se o arquivo já existe
    if os.path.exists(filepath):
        log_message(f"Arquivo {filename} já existe. Pulando download.")
        return filepath
    
    try:
        log_message(f"Iniciando download dos indicadores educacionais {ano}...")
        # Realizar o download
        response = requests.get(base_url, stream=True)
        response.raise_for_status()
        
        # Salvar o arquivo
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        log_message(f"Download dos indicadores educacionais {ano} concluído com sucesso.")
        return filepath
    
    except Exception as e:
        log_message(f"Erro ao baixar indicadores educacionais {ano}: {str(e)}", "ERROR")
        return None

## 4. Extração e Pré-processamento Inicial

### 4.1 Extração do Censo Escolar

def extrair_censo_escolar(ano, arquivo_zip):
    """
    Função para extrair e processar dados do Censo Escolar
    
    Args:
        ano (int): Ano do Censo Escolar
        arquivo_zip (str): Caminho para o arquivo ZIP dos microdados
    
    Returns:
        pandas.DataFrame: DataFrame com dados do ensino médio extraídos e processados
    """
    log_message(f"Iniciando extração de dados do Censo Escolar {ano}...")
    
    # Verificar se arquivo existe
    if not os.path.exists(arquivo_zip):
        log_message(f"Arquivo {arquivo_zip} não encontrado", "ERROR")
        return None
    
    # Extrair arquivos para diretório temporário
    temp_dir = os.path.join(RAW_DIR, f"temp_censo_{ano}")
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
            # Extrair apenas arquivos relevantes (matricula e escola)
            for file in zip_ref.namelist():
                if ('MATRICULA' in file.upper() or 'ESCOLA' in file.upper()) and file.endswith('.CSV'):
                    zip_ref.extract(file, temp_dir)
        
        log_message("Arquivos do Censo Escolar extraídos com sucesso")
        
        # Encontrar o arquivo de matrícula
        matricula_file = None
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if 'MATRICULA' in file.upper() and file.endswith('.CSV'):
                    matricula_file = os.path.join(root, file)
                    break
        
        if not matricula_file:
            log_message("Arquivo de matrícula não encontrado", "ERROR")
            return None
        
        # Ler amostra para identificar o separador
        with open(matricula_file, 'r', encoding='latin-1') as f:
            primeira_linha = f.readline()
            if '|' in primeira_linha:
                separador = '|'
            elif ';' in primeira_linha:
                separador = ';'
            else:
                separador = ','
        
        # Definir colunas relevantes para análise de abandono no ensino médio
        colunas_relevantes = [
            'NU_ANO_CENSO', 'CO_UF', 'CO_MUNICIPIO', 'CO_ENTIDADE', 
            'TP_DEPENDENCIA', 'TP_LOCALIZACAO', 'TP_SEXO', 'TP_COR_RACA',
            'NU_IDADE', 'TP_ETAPA_ENSINO', 'IN_TRANSPORTE_PUBLICO',
            'TP_SITUACAO'  # Situação do aluno ao final do ano letivo
        ]
        
        # Ler apenas as primeiras linhas para verificar colunas existentes
        df_teste = pd.read_csv(matricula_file, sep=separador, encoding='latin-1', nrows=5)
        colunas_existentes = [col for col in colunas_relevantes if col in df_teste.columns]
        
        # Ler os dados de matrícula (apenas ensino médio)
        log_message("Carregando dados de matrícula do ensino médio...")
        
        # Lendo amostra pequena para demonstração
        df_matricula = pd.read_csv(
            matricula_file,
            sep=separador,
            encoding='latin-1',
            usecols=colunas_existentes,
            nrows=10000  # Limitando para amostra
        )
        
        # Filtrar apenas ensino médio (códigos variam por ano)
        codigos_ensino_medio = list(range(25, 38))  # Códigos típicos do ensino médio
        df_ensino_medio = df_matricula[df_matricula['TP_ETAPA_ENSINO'].isin(codigos_ensino_medio)]
        
        log_message(f"Processados {len(df_ensino_medio)} registros de matrícula do ensino médio")
        
        # Salvar amostra processada
        output_file = os.path.join(PROCESSED_DIR, f"amostra_censo_escolar_{ano}_ensino_medio.csv")
        df_ensino_medio.to_csv(output_file, index=False)
        
        log_message(f"Amostra salva em {output_file}")
        
        # Limpeza: remover diretório temporário
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)
        
        return df_ensino_medio
    
    except Exception as e:
        log_message(f"Erro ao extrair dados do Censo Escolar: {str(e)}", "ERROR")
        return None

# Funções similares para as outras fontes...

## 5. Execução do Pipeline de Coleta

# Definir ano de referência
ano_referencia = 2022

# Pipeline para Censo Escolar
arquivo_censo = download_censo_escolar(ano_referencia)
if arquivo_censo:
    df_censo = extrair_censo_escolar(ano_referencia, arquivo_censo)
    print(f"Shape dos dados do Censo Escolar: {df_censo.shape if df_censo is not None else 'N/A'}")

# Pipeline para SAEB (anos ímpares)
if (ano_referencia % 2) == 1:  # SAEB ocorre em anos ímpares
    arquivo_saeb = download_saeb(ano_referencia)
    # Processamento do SAEB...

# Pipeline para PNAD
arquivo_pnad = download_pnad(ano_referencia)
# Processamento da PNAD...

# Pipeline para Indicadores Educacionais
arquivo_indicadores = download_indicadores(ano_referencia)
# Processamento dos indicadores...

## 6. Resumo e Próximos Passos

# Exibir resumo do processamento
log_message("=== Resumo da Coleta de Dados ===")
log_message(f"Ano de referência: {ano_referencia}")
log_message(f"Arquivos baixados: {sum(1 for x in [arquivo_censo, arquivo_saeb, arquivo_pnad, arquivo_indicadores] if x is not None)}")
log_message("Próximos passos: Integração das fontes de dados no notebook 2_integracao_fontes.ipynb")

# Considerações importantes para a próxima etapa
log_message("Observações:")
log_message("1. Os dados do Censo Escolar são fundamentais para a quantificação do abandono")
log_message("2. Os dados do SAEB fornecem informações contextuais importantes")
log_message("3. A PNAD permite compreender motivações autodeclaradas do abandono")
log_message("4. Os indicadores educacionais oferecem visão agregada e padronizada")
