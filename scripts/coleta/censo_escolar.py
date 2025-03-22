"""
Script para extração de dados do Censo Escolar do INEP.

Este script realiza o download, extração e processamento inicial dos microdados
do Censo Escolar, focando nos dados relevantes para análise do abandono escolar
no ensino médio.
"""

import pandas as pd
import numpy as np
import os
import zipfile
import requests
from datetime import datetime
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("censo_escolar.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("censo_escolar")

# Definir diretórios
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')

# Criar diretórios se não existirem
for directory in [DATA_DIR, RAW_DIR, PROCESSED_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)


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
        logger.info(f"Arquivo {filename} já existe. Pulando download.")
        return filepath
    
    try:
        logger.info(f"Iniciando download do Censo Escolar {ano}...")
        # Realizar o download
        response = requests.get(base_url, stream=True)
        response.raise_for_status()
        
        # Salvar o arquivo
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Download do Censo Escolar {ano} concluído com sucesso.")
        return filepath
    
    except Exception as e:
        logger.error(f"Erro ao baixar Censo Escolar {ano}: {str(e)}")
        return None


def extrair_censo_escolar(ano, arquivo_zip):
    """
    Função para extrair e processar dados do Censo Escolar
    
    Args:
        ano (int): Ano do Censo Escolar
        arquivo_zip (str): Caminho para o arquivo ZIP dos microdados
    
    Returns:
        pandas.DataFrame: DataFrame com dados do ensino médio extraídos e processados
    """
    logger.info(f"Iniciando extração de dados do Censo Escolar {ano}...")
    
    # Verificar se arquivo existe
    if not os.path.exists(arquivo_zip):
        logger.error(f"Arquivo {arquivo_zip} não encontrado")
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
        
        logger.info("Arquivos do Censo Escolar extraídos com sucesso")
        
        # Encontrar o arquivo de matrícula
        matricula_file = None
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if 'MATRICULA' in file.upper() and file.endswith('.CSV'):
                    matricula_file = os.path.join(root, file)
                    break
        
        if not matricula_file:
            logger.error("Arquivo de matrícula não encontrado")
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
        logger.info("Carregando dados de matrícula do ensino médio...")
        
        # Para processamento completo, remover o parâmetro nrows
        df_matricula = pd.read_csv(
            matricula_file,
            sep=separador,
            encoding='latin-1',
            usecols=colunas_existentes
        )
        
        # Filtrar apenas ensino médio (códigos variam por ano)
        codigos_ensino_medio = list(range(25, 38))  # Códigos típicos do ensino médio
        df_ensino_medio = df_matricula[df_matricula['TP_ETAPA_ENSINO'].isin(codigos_ensino_medio)]
        
        logger.info(f"Processados {len(df_ensino_medio)} registros de matrícula do ensino médio")
        
        # Encontrar o arquivo de escolas
        escola_file = None
        for root, _, files in os.walk(temp_dir):
            for file in files:
                if 'ESCOLA' in file.upper() and file.endswith('.CSV'):
                    escola_file = os.path.join(root, file)
                    break
        
        if escola_file:
            logger.info("Carregando dados de escolas...")
            
            # Ler amostra para identificar o separador
            with open(escola_file, 'r', encoding='latin-1') as f:
                primeira_linha = f.readline()
                if '|' in primeira_linha:
                    separador = '|'
                elif ';' in primeira_linha:
                    separador = ';'
                else:
                    separador = ','
            
            # Colunas relevantes para escolas
            colunas_escolas = [
                'CO_ENTIDADE', 'NO_ENTIDADE', 'CO_MUNICIPIO', 'CO_UF',
                'TP_DEPENDENCIA', 'TP_LOCALIZACAO', 
                'IN_AGUA_FILTRADA', 'IN_AGUA_REDE_PUBLICA', 
                'IN_ENERGIA_REDE_PUBLICA', 'IN_ESGOTO_REDE_PUBLICA',
                'IN_BIBLIOTECA', 'IN_LABORATORIO_INFORMATICA', 
                'IN_LABORATORIO_CIENCIAS', 'IN_QUADRA_ESPORTES',
                'IN_SALA_ATENDIMENTO_ESPECIAL', 'IN_INTERNET'
            ]
            
            # Ler as primeiras linhas para verificar colunas existentes
            df_teste = pd.read_csv(escola_file, sep=separador, encoding='latin-1', nrows=5)
            colunas_existentes = [col for col in colunas_escolas if col in df_teste.columns]
            
            # Ler os dados de escolas
            df_escolas = pd.read_csv(
                escola_file,
                sep=separador,
                encoding='latin-1',
                usecols=colunas_existentes
            )
            
            logger.info(f"Processados {len(df_escolas)} registros de escolas")
            
            # Calcular índice de infraestrutura
            colunas_infra = [col for col in df_escolas.columns if col.startswith('IN_')]
            
            if colunas_infra:
                # Converter para numérico se necessário
                for col in colunas_infra:
                    if df_escolas[col].dtype == 'object':
                        df_escolas[col] = pd.to_numeric(df_escolas[col], errors='coerce')
                
                # Calcular índice como média dos indicadores
                df_escolas['INDICE_INFRAESTRUTURA'] = df_escolas[colunas_infra].mean(axis=1)
                
                logger.info("Índice de infraestrutura calculado para escolas")
            
            # Salvar dados de escolas processados
            output_escolas = os.path.join(PROCESSED_DIR, f"censo_escolar_{ano}_escolas.csv")
            df_escolas.to_csv(output_escolas, index=False)
            logger.info(f"Dados de escolas salvos em {output_escolas}")
        
        # Criar variável indicadora de abandono
        df_ensino_medio['ABANDONO'] = 0
        if 'TP_SITUACAO' in df_ensino_medio.columns:
            # Códigos de situação: 1 = Aprovado, 2 = Reprovado, 3 = Transferido, 4 = Abandono
            df_ensino_medio['ABANDONO'] = df_ensino_medio['TP_SITUACAO'].apply(
                lambda x: 1 if x == 4 else 0
            )
        
        # Salvar dados processados
        output_file = os.path.join(PROCESSED_DIR, f"censo_escolar_{ano}_ensino_medio.csv")
        df_ensino_medio.to_csv(output_file, index=False)
        
        logger.info(f"Dados processados salvos em {output_file}")
        
        # Limpeza: remover diretório temporário
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))
        os.rmdir(temp_dir)
        
        return df_ensino_medio
    
    except Exception as e:
        logger.error(f"Erro ao extrair dados do Censo Escolar: {str(e)}")
        return None


def processar_censo_escolar(ano):
    """
    Função principal para processamento completo do Censo Escolar
    
    Args:
        ano (int): Ano de referência do Censo Escolar
    
    Returns:
        bool: True se o processamento foi bem-sucedido, False caso contrário
    """
    logger.info(f"Iniciando processamento completo do Censo Escolar {ano}")
    
    try:
        # 1. Download dos dados
        arquivo_zip = download_censo_escolar(ano)
        if not arquivo_zip:
            return False
        
        # 2. Extração e processamento
        df_ensino_medio = extrair_censo_escolar(ano, arquivo_zip)
        if df_ensino_medio is None:
            return False
        
        # 3. Cálculos agregados por escola
        logger.info("Calculando estatísticas agregadas por escola...")
        df_agregado_escola = df_ensino_medio.groupby('CO_ENTIDADE').agg({
            'CO_MUNICIPIO': 'first',
            'CO_UF': 'first',
            'TP_DEPENDENCIA': 'first',
            'TP_LOCALIZACAO': 'first',
            'ABANDONO': 'mean',
            'NU_ANO_CENSO': 'count'
        }).reset_index()
        
        # Renomear colunas
        df_agregado_escola = df_agregado_escola.rename(columns={
            'ABANDONO': 'TAXA_ABANDONO',
            'NU_ANO_CENSO': 'TOTAL_ALUNOS'
        })
        
        # Salvar dados agregados
        output_agregado = os.path.join(PROCESSED_DIR, f"censo_escolar_{ano}_agregado_escola.csv")
        df_agregado_escola.to_csv(output_agregado, index=False)
        logger.info(f"Dados agregados por escola salvos em {output_agregado}")
        
        # 4. Cálculos agregados por município
        logger.info("Calculando estatísticas agregadas por município...")
        df_agregado_municipio = df_ensino_medio.groupby('CO_MUNICIPIO').agg({
            'CO_UF': 'first',
            'ABANDONO': 'mean',
            'NU_ANO_CENSO': 'count',
            'CO_ENTIDADE': 'nunique'
        }).reset_index()
        
        # Renomear colunas
        df_agregado_municipio = df_agregado_municipio.rename(columns={
            'ABANDONO': 'TAXA_ABANDONO',
            'NU_ANO_CENSO': 'TOTAL_ALUNOS',
            'CO_ENTIDADE': 'TOTAL_ESCOLAS'
        })
        
        # Salvar dados agregados por município
        output_municipio = os.path.join(PROCESSED_DIR, f"censo_escolar_{ano}_agregado_municipio.csv")
        df_agregado_municipio.to_csv(output_municipio, index=False)
        logger.info(f"Dados agregados por município salvos em {output_municipio}")
        
        logger.info(f"Processamento completo do Censo Escolar {ano} finalizado com sucesso")
        return True
    
    except Exception as e:
        logger.error(f"Erro no processamento completo do Censo Escolar {ano}: {str(e)}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Processamento de dados do Censo Escolar do INEP')
    parser.add_argument('--ano', type=int, required=True, help='Ano de referência do Censo Escolar')
    parser.add_argument('--download-only', action='store_true', help='Apenas fazer download dos dados')
    
    args = parser.parse_args()
    
    if args.download_only:
        arquivo = download_censo_escolar(args.ano)
        if arquivo:
            print(f"Download concluído: {arquivo}")
        else:
            print("Falha no download")
    else:
        success = processar_censo_escolar(args.ano)
        print(f"Processamento {'concluído com sucesso' if success else 'falhou'}")
