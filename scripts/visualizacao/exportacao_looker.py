"""
Script para exportação de dados processados para visualização no Looker Studio.

Este script prepara e exporta os dados resultantes da análise para serem
consumidos pelo Looker Studio, formatando-os adequadamente para visualização
interativa.
"""

import pandas as pd
import numpy as np
import os
import logging
from pathlib import Path
from datetime import datetime
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("exportacao_looker.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("exportacao_looker")

# Definir diretórios
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
RESULTS_DIR = DATA_DIR / 'results'
LOOKER_DIR = DATA_DIR / 'looker_data'

# Criar diretórios se não existirem
for directory in [DATA_DIR, PROCESSED_DIR, RESULTS_DIR, LOOKER_DIR]:
    if not directory.exists():
        directory.mkdir(parents=True)


def carregar_dados_integrados(ano, nivel='municipios'):
    """
    Carrega dados integrados para exportação
    
    Args:
        ano (int): Ano de referência
        nivel (str): Nível de agregação ('escolas', 'municipios', 'alunos')
    
    Returns:
        pandas.DataFrame: DataFrame com dados integrados
    """
    arquivo = PROCESSED_DIR / f"dados_integrados_{nivel}_{ano}.csv"
    
    if arquivo.exists():
        try:
            df = pd.read_csv(arquivo)
            logger.info(f"Dados integrados de {nivel} para {ano} carregados: {len(df)} registros")
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar dados integrados: {str(e)}")
            return None
    else:
        logger.warning(f"Arquivo {arquivo} não encontrado")
        return None


def carregar_resultados_segmentacao(ano):
    """
    Carrega resultados da segmentação/clusterização
    
    Args:
        ano (int): Ano de referência
    
    Returns:
        dict: Dicionário com DataFrames dos resultados de segmentação
    """
    resultados = {}
    
    # Tentar carregar perfis de abandono
    arquivo_perfis = RESULTS_DIR / f"perfis_abandono_{ano}.csv"
    if arquivo_perfis.exists():
        try:
            df_perfis = pd.read_csv(arquivo_perfis)
            resultados['perfis'] = df_perfis
            logger.info(f"Dados de perfis de abandono carregados: {len(df_perfis)} registros")
        except Exception as e:
            logger.error(f"Erro ao carregar perfis de abandono: {str(e)}")
    
    # Tentar carregar clusters de municípios
    arquivo_clusters = RESULTS_DIR / f"clusters_municipios_{ano}.csv"
    if arquivo_clusters.exists():
        try:
            df_clusters = pd.read_csv(arquivo_clusters)
            resultados['clusters_municipios'] = df_clusters
            logger.info(f"Dados de clusters municipais carregados: {len(df_clusters)} registros")
        except Exception as e:
            logger.error(f"Erro ao carregar clusters municipais: {str(e)}")
    
    # Tentar carregar importância de variáveis do modelo preditivo
    arquivo_importancia = RESULTS_DIR / "importancia_features.csv"
    if arquivo_importancia.exists():
        try:
            df_importancia = pd.read_csv(arquivo_importancia)
            resultados['importancia_features'] = df_importancia
            logger.info(f"Dados de importância de variáveis carregados: {len(df_importancia)} registros")
        except Exception as e:
            logger.error(f"Erro ao carregar importância de variáveis: {str(e)}")
    
    return resultados


def preparar_dados_municipios(df_municipios, campos_obrigatorios=None):
    """
    Prepara dados de municípios para exportação
    
    Args:
        df_municipios (pandas.DataFrame): DataFrame original
        campos_obrigatorios (list): Lista de campos que devem estar presentes
    
    Returns:
        pandas.DataFrame: DataFrame preparado para Looker Studio
    """
    if df_municipios is None:
        return None
    
    # Copiar DataFrame para evitar modificações no original
    df = df_municipios.copy()
    
    # Verificar campos obrigatórios
    if campos_obrigatorios:
        campos_faltantes = [campo for campo in campos_obrigatorios if campo not in df.columns]
        if campos_faltantes:
            logger.error(f"Campos obrigatórios ausentes: {campos_faltantes}")
            return None
    
    # Tratar valores ausentes
    # Para campos numéricos: substituir por média
    for col in df.select_dtypes(include=['int64', 'float64']).columns:
        if df[col].isnull().any():
            media = df[col].mean()
            df[col] = df[col].fillna(media)
            logger.info(f"Substituídos {df[col].isnull().sum()} valores ausentes em {col} pela média ({media:.2f})")
    
    # Para campos categóricos: substituir por "Não informado"
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].isnull().any():
            df[col] = df[col].fillna("Não informado")
            logger.info(f"Substituídos {df[col].isnull().sum()} valores ausentes em {col} por 'Não informado'")
    
    # Limitar precisão para reduzir tamanho dos arquivos
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].round(2)
    
    # Adicionar variáveis categorizadas para facilitar filtros no Looker
    if 'TAXA_ABANDONO' in df.columns:
        df['CATEGORIA_ABANDONO'] = pd.cut(
            df['TAXA_ABANDONO'],
            bins=[0, 5, 10, 15, 100],
            labels=['Baixo (0-5%)', 'Médio (5-10%)', 'Alto (10-15%)', 'Muito Alto (>15%)']
        )
        logger.info("Adicionada categorização de taxa de abandono")
    
    if 'TAXA_POBREZA' in df.columns:
        df['CATEGORIA_POBREZA'] = pd.qcut(
            df['TAXA_POBREZA'],
            q=4,
            labels=['Baixa', 'Média-Baixa', 'Média-Alta', 'Alta'],
            duplicates='drop'
        )
        logger.info("Adicionada categorização de taxa de pobreza")
    
    if 'CO_UF' in df.columns:
        # Adicionar nomes das UFs e regiões
        mapa_uf = {
            11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
            21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
            31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP',
            41: 'PR', 42: 'SC', 43: 'RS',
            50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
        }
        
        regioes = {
            11: 'Norte', 12: 'Norte', 13: 'Norte', 14: 'Norte', 15: 'Norte', 16: 'Norte', 17: 'Norte',
            21: 'Nordeste', 22: 'Nordeste', 23: 'Nordeste', 24: 'Nordeste', 25: 'Nordeste', 
            26: 'Nordeste', 27: 'Nordeste', 28: 'Nordeste', 29: 'Nordeste',
            31: 'Sudeste', 32: 'Sudeste', 33: 'Sudeste', 35: 'Sudeste',
            41: 'Sul', 42: 'Sul', 43: 'Sul',
            50: 'Centro-Oeste', 51: 'Centro-Oeste', 52: 'Centro-Oeste', 53: 'Centro-Oeste'
        }
        
        df['UF_SIGLA'] = df['CO_UF'].map(mapa_uf)
        df['REGIAO'] = df['CO_UF'].map(regioes)
        logger.info("Adicionadas colunas de UF_SIGLA e REGIAO")
    
    logger.info(f"Preparação dos dados municipais concluída: {len(df)} registros, {df.shape[1]} variáveis")
    return df


def preparar_dados_escolas(df_escolas, campos_obrigatorios=None):
    """
    Prepara dados de escolas para exportação
    
    Args:
        df_escolas (pandas.DataFrame): DataFrame original
        campos_obrigatorios (list): Lista de campos que devem estar presentes
    
    Returns:
        pandas.DataFrame: DataFrame preparado para Looker Studio
    """
    if df_escolas is None:
        return None
    
    # Processar de forma similar aos municípios
    df = df_escolas.copy()
    
    # Verificar campos obrigatórios
    if campos_obrigatorios:
        campos_faltantes = [campo for campo in campos_obrigatorios if campo not in df.columns]
        if campos_faltantes:
            logger.error(f"Campos obrigatórios ausentes: {campos_faltantes}")
            return None
    
    # Tratar valores ausentes
    for col in df.select_dtypes(include=['int64', 'float64']).columns:
        if df[col].isnull().any():
            df[col] = df[col].fillna(df[col].mean())
    
    for col in df.select_dtypes(include=['object']).columns:
        if df[col].isnull().any():
            df[col] = df[col].fillna("Não informado")
    
    # Limitar precisão
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].round(2)
    
    # Se dependência administrativa estiver presente como código, converter para texto
    if 'TP_DEPENDENCIA' in df.columns and df['TP_DEPENDENCIA'].dtype in ['int64', 'float64']:
        mapa_dependencia = {1: 'Federal', 2: 'Estadual', 3: 'Municipal', 4: 'Privada'}
        df['DEPENDENCIA'] = df['TP_DEPENDENCIA'].map(mapa_dependencia)
    
    # Se localização estiver presente como código, converter para texto
    if 'TP_LOCALIZACAO' in df.columns and df['TP_LOCALIZACAO'].dtype in ['int64', 'float64']:
        mapa_localizacao = {1: 'Urbana', 2: 'Rural'}
        df['LOCALIZACAO'] = df['TP_LOCALIZACAO'].map(mapa_localizacao)
    
    # Adicionar categorização de abandono
    if 'TAXA_ABANDONO' in df.columns:
        df['CATEGORIA_ABANDONO'] = pd.cut(
            df['TAXA_ABANDONO'],
            bins=[0, 5, 10, 15, 100],
            labels=['Baixo (0-5%)', 'Médio (5-10%)', 'Alto (10-15%)', 'Muito Alto (>15%)']
        )
    
    # Se houver índice de infraestrutura, adicionar categorização
    if 'INDICE_INFRAESTRUTURA' in df.columns:
        df['CATEGORIA_INFRAESTRUTURA'] = pd.qcut(
            df['INDICE_INFRAESTRUTURA'],
            q=4,
            labels=['Inadequada', 'Básica', 'Adequada', 'Excelente'],
            duplicates='drop'
        )
    
    logger.info(f"Preparação dos dados de escolas concluída: {len(df)} registros, {df.shape[1]} variáveis")
    return df


def preparar_dados_perfis(df_perfis):
    """
    Prepara dados de perfis de abandono para exportação
    
    Args:
        df_perfis (pandas.DataFrame): DataFrame original
    
    Returns:
        pandas.DataFrame: DataFrame preparado para Looker Studio
    """
    if df_perfis is None:
        return None
    
    # Processar de forma específica para dados de perfis
    df = df_perfis.copy()
    
    # Garantir nomes descritivos para os perfis
    if 'PERFIL' in df.columns and 'NOME_PERFIL' not in df.columns:
        # Exemplo de mapeamento
        mapa_perfis = {
            0: 'Perfil Geral (Não Abandono)',
            1: 'Perfil Acadêmico-Vulnerável',
            2: 'Perfil Trabalho-Estudo',
            3: 'Perfil Desmotivacional',
            4: 'Perfil Circunstancial-Familiar'
        }
        
        # Verificar se os valores existem no mapeamento
        valores_perfil = df['PERFIL'].unique()
        for valor in valores_perfil:
            if valor not in mapa_perfis:
                mapa_perfis[valor] = f'Perfil {valor}'
        
        df['NOME_PERFIL'] = df['PERFIL'].map(mapa_perfis)
    
    # Limitar precisão para métricas
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].round(2)
    
    # Adicionar colunas derivadas para visualização
    # Por exemplo, normalizar valores para gráfico de radar
    colunas_metricas = [col for col in df.columns if col not in ['PERFIL', 'NOME_PERFIL', 'COUNT', 'PERCENTAGE']]
    
    if colunas_metricas:
        # Criar versões normalizadas entre 0 e 1 para gráfico de radar
        for col in colunas_metricas:
            min_val = df[col].min()
            max_val = df[col].max()
            if max_val > min_val:  # Evitar divisão por zero
                df[f'{col}_NORM'] = (df[col] - min_val) / (max_val - min_val)
            else:
                df[f'{col}_NORM'] = 0.5  # Valor padrão
    
    logger.info(f"Preparação dos dados de perfis concluída: {len(df)} registros, {df.shape[1]} variáveis")
    return df


def preparar_series_temporais(anos, nivel='municipios'):
    """
    Prepara séries temporais para análise de tendências
    
    Args:
        anos (list): Lista de anos para inclusão
        nivel (str): Nível de agregação ('escolas', 'municipios')
    
    Returns:
        pandas.DataFrame: DataFrame com séries temporais
    """
    dfs = []
    
    for ano in anos:
        # Carregar dados
        arquivo = PROCESSED_DIR / f"dados_integrados_{nivel}_{ano}.csv"
        
        if not arquivo.exists():
            logger.warning(f"Arquivo {arquivo} não encontrado para o ano {ano}")
            continue
        
        try:
            df = pd.read_csv(arquivo)
            
            # Adicionar coluna de ano
            df['ANO'] = ano
            
            # Selecionar apenas colunas relevantes para análise temporal
            colunas_chave = ['ANO']
            
            if nivel == 'municipios':
                colunas_chave.extend(['CO_MUNICIPIO', 'CO_UF'])
            elif nivel == 'escolas':
                colunas_chave.extend(['CO_ENTIDADE', 'CO_MUNICIPIO', 'CO_UF'])
            
            # Adicionar métricas principais
            colunas_metricas = ['TAXA_ABANDONO']
            
            # Verificar quais métricas estão disponíveis
            colunas_existentes = colunas_chave + [col for col in colunas_metricas if col in df.columns]
            
            # Selecionar apenas as colunas relevantes
            df_selecionado = df[colunas_existentes]
            
            dfs.append(df_selecionado)
            logger.info(f"Dados do ano {ano} adicionados à série temporal")
            
        except Exception as e:
            logger.error(f"Erro ao processar dados do ano {ano}: {str(e)}")
    
    if not dfs:
        logger.error("Nenhum dado disponível para criar séries temporais")
        return None
    
    # Concatenar todos os anos
    df_series = pd.concat(dfs, ignore_index=True)
    
    # Calcular médias anuais
    if nivel == 'municipios':
        grupos = ['ANO', 'CO_UF']
    elif nivel == 'escolas':
        grupos = ['ANO', 'CO_UF', 'CO_MUNICIPIO']
    else:
        grupos = ['ANO']
    
    df_series_agregado = df_series.groupby(grupos).agg({
        'TAXA_ABANDONO': 'mean'
    }).reset_index()
    
    # Adicionar UF e região se CO_UF estiver disponível
    if 'CO_UF' in df_series_agregado.columns:
        mapa_uf = {
            11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
            21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
            31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP',
            41: 'PR', 42: 'SC', 43: 'RS',
            50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
        }
        
        regioes = {
            11: 'Norte', 12: 'Norte', 13: 'Norte', 14: 'Norte', 15: 'Norte', 16: 'Norte', 17: 'Norte',
            21: 'Nordeste', 22: 'Nordeste', 23: 'Nordeste', 24: 'Nordeste', 25: 'Nordeste', 
            26: 'Nordeste', 27: 'Nordeste', 28: 'Nordeste', 29: 'Nordeste',
            31: 'Sudeste', 32: 'Sudeste', 33: 'Sudeste', 35: 'Sudeste',
            41: 'Sul', 42: 'Sul', 43: 'Sul',
            50: 'Centro-Oeste', 51: 'Centro-Oeste', 52: 'Centro-Oeste', 53: 'Centro-Oeste'
        }
        
        df_series_agregado['UF_SIGLA'] = df_series_agregado['CO_UF'].map(mapa_uf)
        df_series_agregado['REGIAO'] = df_series_agregado['CO_UF'].map(regioes)
    
    # Arredondar valores
    for col in df_series_agregado.select_dtypes(include=['float64']).columns:
        df_series_agregado[col] = df_series_agregado[col].round(2)
    
    logger.info(f"Séries temporais preparadas: {len(df_series_agregado)} registros")
    return df_series_agregado


def exportar_para_looker(dataframes, ano_referencia, output_dir=LOOKER_DIR):
    """
    Exporta os dataframes preparados para o Looker Studio
    
    Args:
        dataframes (dict): Dicionário com DataFrames preparados
        ano_referencia (int): Ano de referência
        output_dir (Path): Diretório para exportação
    
    Returns:
        dict: Dicionário com caminhos para os arquivos exportados
    """
    logger.info(f"Iniciando exportação para Looker Studio (ano: {ano_referencia})")
    
    arquivos_exportados = {}
    
    # Exportar cada DataFrame
    for nome, df in dataframes.items():
        if df is not None and not df.empty:
            try:
                # Definir nome do arquivo
                arquivo = output_dir / f"{nome}_{ano_referencia}.csv"
                
                # Exportar para CSV
                df.to_csv(arquivo, index=False)
                
                arquivos_exportados[nome] = arquivo
                logger.info(f"DataFrame '{nome}' exportado para {arquivo}: {len(df)} registros, {df.shape[1]} variáveis")
            except Exception as e:
                logger.error(f"Erro ao exportar DataFrame '{nome}': {str(e)}")
    
    # Criar arquivo de metadados
    metadados = {
        'data_exportacao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ano_referencia': ano_referencia,
        'arquivos_exportados': {nome: str(caminho) for nome, caminho in arquivos_exportados.items()},
        'contagens': {nome: len(dataframes[nome]) for nome in arquivos_exportados.keys()},
        'variaveis': {nome: dataframes[nome].shape[1] for nome in arquivos_exportados.keys()}
    }
    
    arquivo_metadados = output_dir / f"metadados_looker_{ano_referencia}.json"
    with open(arquivo_metadados, 'w') as f:
        json.dump(metadados, f, indent=4)
    
    arquivos_exportados['metadados'] = arquivo_metadados
    logger.info(f"Metadados exportados para {arquivo_metadados}")
    
    # Criar arquivo README.md com instruções
    readme_content = f"""# Dados para Visualização no Looker Studio

Este diretório contém os arquivos CSV processados para importação no Looker Studio.

## Arquivos Disponíveis

{chr(10).join([f"- **{nome}**: {caminho.name}" for nome, caminho in arquivos_exportados.items()])}

## Instruções para Importação

1. Acesse o [Looker Studio](https://lookerstudio.google.com/)
2. Clique em "Criar" e selecione "Relatório"
3. Selecione "Upload de arquivo" como fonte de dados
4. Importe os arquivos CSV disponíveis neste diretório
5. Configure as visualizações conforme necessário

## Recomendações de Visualizações

- **Mapa coroplético** para taxas de abandono por região
- **Gráficos de barras** para comparação entre dependências administrativas
- **Gráfico de radar** para visualização de perfis de abandono
- **Tabelas dinâmicas** para análise multidimensional
- **Indicadores de desempenho** para métricas principais

Data de exportação: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""
    
    arquivo_readme = output_dir / "README.md"
    with open(arquivo_readme, 'w') as f:
        f.write(readme_content)
    
    arquivos_exportados['readme'] = arquivo_readme
    logger.info(f"Arquivo README criado em: {arquivo_readme}")
    
    return arquivos_exportados


def gerar_exportacao_looker(ano_referencia, anos_serie_temporal=None):
    """
    Função principal para gerar exportação completa para o Looker Studio
    
    Args:
        ano_referencia (int): Ano principal de referência
        anos_serie_temporal (list): Lista de anos para série temporal
    
    Returns:
        dict: Dicionário com caminhos para os arquivos exportados
    """
    logger.info(f"Iniciando processo completo de exportação para Looker Studio (ano ref: {ano_referencia})")
    
    # 1. Carregar dados integrados
    df_municipios = carregar_dados_integrados(ano_referencia, nivel='municipios')
    df_escolas = carregar_dados_integrados(ano_referencia, nivel='escolas')
    
    # 2. Carregar resultados de segmentação
    resultados_segmentacao = carregar_resultados_segmentacao(ano_referencia)
    
    # 3. Preparar dados para Looker Studio
    dfs_preparados = {}
    
    # Preparar dados de municípios
    if df_municipios is not None:
        df_municipios_prep = preparar_dados_municipios(df_municipios, 
                                                     campos_obrigatorios=['CO_MUNICIPIO', 'TAXA_ABANDONO'])
        if df_municipios_prep is not None:
            dfs_preparados['dados_municipios'] = df_municipios_prep
    
    # Preparar dados de escolas
    if df_escolas is not None:
        df_escolas_prep = preparar_dados_escolas(df_escolas,
                                               campos_obrigatorios=['CO_ENTIDADE', 'TAXA_ABANDONO'])
        if df_escolas_prep is not None:
            dfs_preparados['dados_escolas'] = df_escolas_prep
    
    # Preparar dados de perfis (se disponíveis)
    if 'perfis' in resultados_segmentacao:
        df_perfis_prep = preparar_dados_perfis(resultados_segmentacao['perfis'])
        if df_perfis_prep is not None:
            dfs_preparados['dados_perfis'] = df_perfis_prep
    
    # Preparar dados de importância de variáveis (se disponíveis)
    if 'importancia_features' in resultados_segmentacao:
        dfs_preparados['importancia_variaveis'] = resultados_segmentacao['importancia_features']
    
    # 4. Preparar séries temporais
    if anos_serie_temporal:
        df_series = preparar_series_temporais(anos_serie_temporal, nivel='municipios')
        if df_series is not None:
            dfs_preparados['series_temporais'] = df_series
    
    # 5. Exportar dados preparados
    arquivos_exportados = exportar_para_looker(dfs_preparados, ano_referencia)
    
    logger.info(f"Exportação para Looker Studio concluída: {len(arquivos_exportados)} arquivos gerados")
    return arquivos_exportados


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Exportação de dados para Looker Studio')
    parser.add_argument('--ano', type=int, required=True, help='Ano de referência principal')
    parser.add_argument('--serie-temporal', type=str, help='Anos para série temporal (separados por vírgula)')
    
    args = parser.parse_args()
    
    # Processar anos para série temporal
    anos_serie = None
    if args.serie_temporal:
        try:
            anos_serie = [int(ano.strip()) for ano in args.serie_temporal.split(',')]
        except ValueError:
            print("Erro: Formato inválido para série temporal. Use números separados por vírgula.")
            anos_serie = None
    
    # Executar exportação
    arquivos = gerar_exportacao_looker(args.ano, anos_serie_temporal=anos_serie)
    
    print("\nExportação para Looker Studio concluída:")
    for nome, caminho in arquivos.items():
        print(f"- {nome}: {caminho}")
