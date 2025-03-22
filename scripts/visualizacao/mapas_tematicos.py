"""
Script para geração de mapas temáticos para visualização da distribuição espacial
do abandono escolar no Brasil.

Este script gera mapas coropléticos (de cores) e outros tipos de visualizações espaciais
para análise da distribuição geográfica do abandono escolar em diferentes níveis 
(UF, municípios, etc.).
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import matplotlib.colors as colors
from mpl_toolkits.axes_grid1 import make_axes_locatable
import os
import logging
from pathlib import Path
import contextily as ctx

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("mapas_tematicos.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("mapas_tematicos")

# Definir diretórios
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
RESULTS_DIR = DATA_DIR / 'results'
PLOTS_DIR = BASE_DIR / 'visualizacoes' / 'mapas'
GEO_DIR = DATA_DIR / 'raw' / 'geo'

# Criar diretórios se não existirem
for directory in [DATA_DIR, PROCESSED_DIR, RESULTS_DIR, PLOTS_DIR, GEO_DIR]:
    if not directory.exists():
        directory.mkdir(parents=True)


def baixar_shapefile_brasil(force_download=False):
    """
    Baixa os shapefiles do Brasil do IBGE se não existirem
    
    Args:
        force_download (bool): Força o download mesmo se os arquivos já existirem
        
    Returns:
        dict: Dicionário com caminhos para os shapefiles baixados
    """
    import requests
    from io import BytesIO
    from zipfile import ZipFile
    
    # URLs dos shapefiles
    urls = {
        'Brasil_UF': 'https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2022/Brasil/BR/BR_UF_2022.zip',
        'Brasil_Municipios': 'https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/municipio_2022/Brasil/BR/BR_Municipios_2022.zip'
    }
    
    shapefiles = {}
    
    for nome, url in urls.items():
        # Definir pasta de destino
        dest_folder = GEO_DIR / nome
        
        # Verificar se já existe
        if dest_folder.exists() and not force_download:
            logger.info(f"Shapefile {nome} já existe. Pulando download.")
            
            # Encontrar o arquivo .shp
            shp_files = list(dest_folder.glob("*.shp"))
            if shp_files:
                shapefiles[nome] = shp_files[0]
            continue
        
        try:
            logger.info(f"Baixando shapefile {nome}...")
            response = requests.get(url)
            response.raise_for_status()
            
            # Criar pasta de destino
            if not dest_folder.exists():
                dest_folder.mkdir(parents=True)
            
            # Extrair ZIP
            with ZipFile(BytesIO(response.content)) as zip_file:
                zip_file.extractall(dest_folder)
            
            # Encontrar o arquivo .shp
            shp_files = list(dest_folder.glob("*.shp"))
            if shp_files:
                shapefiles[nome] = shp_files[0]
                logger.info(f"Shapefile {nome} baixado e extraído com sucesso.")
            else:
                logger.warning(f"Não foi encontrado arquivo .shp em {dest_folder}")
                
        except Exception as e:
            logger.error(f"Erro ao baixar shapefile {nome}: {str(e)}")
    
    return shapefiles


def carregar_dados(ano_referencia, nivel='municipios'):
    """
    Carrega os dados processados para visualização
    
    Args:
        ano_referencia (int): Ano de referência dos dados
        nivel (str): Nível de agregação ('municipios' ou 'estados')
        
    Returns:
        pandas.DataFrame: DataFrame com os dados carregados
    """
    if nivel == 'municipios':
        arquivo = PROCESSED_DIR / f"dados_integrados_municipios_{ano_referencia}.csv"
    elif nivel == 'estados':
        arquivo = PROCESSED_DIR / f"dados_integrados_estados_{ano_referencia}.csv"
    else:
        logger.error(f"Nível {nivel} não reconhecido")
        return None
    
    if arquivo.exists():
        try:
            df = pd.read_csv(arquivo)
            logger.info(f"Dados de {len(df)} {nivel} carregados com sucesso")
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo {arquivo}: {str(e)}")
            return None
    else:
        logger.warning(f"Arquivo {arquivo} não encontrado")
        return None


def gerar_mapa_uf(df_estados, variavel='TAXA_ABANDONO', titulo=None, palette='OrRd', 
                 output_path=None, mostrar_valores=False, mostrar_legenda=True):
    """
    Gera mapa coroplético por UF
    
    Args:
        df_estados (pandas.DataFrame): DataFrame com dados por UF
        variavel (str): Nome da variável a ser visualizada
        titulo (str, optional): Título do mapa
        palette (str): Paleta de cores do mapa
        output_path (Path, optional): Caminho para salvar o mapa
        mostrar_valores (bool): Se deve mostrar valores no mapa
        mostrar_legenda (bool): Se deve mostrar a legenda
        
    Returns:
        bool: True se o mapa foi gerado com sucesso
    """
    try:
        # Carregar shapefile do Brasil (UFs)
        shapefiles = baixar_shapefile_brasil()
        if 'Brasil_UF' not in shapefiles:
            logger.error("Shapefile das UFs não disponível")
            return False
        
        # Carregar o shapefile com geopandas
        gdf_estados = gpd.read_file(shapefiles['Brasil_UF'])
        
        # Verificar se há coluna de código UF no DataFrame
        if 'CO_UF' not in df_estados.columns:
            logger.error("Coluna 'CO_UF' não encontrada nos dados")
            return False
        
        # Verificar se variável existe no DataFrame
        if variavel not in df_estados.columns:
            logger.error(f"Variável '{variavel}' não encontrada nos dados")
            return False
        
        # Normalizar nomes de colunas
        gdf_estados = gdf_estados.rename(columns={'CD_UF': 'CO_UF'})
        
        # Converter códigos para mesmo tipo
        gdf_estados['CO_UF'] = gdf_estados['CO_UF'].astype(int)
        df_estados['CO_UF'] = df_estados['CO_UF'].astype(int)
        
        # Mesclar dados com shapefile
        gdf_merged = gdf_estados.merge(df_estados, on='CO_UF', how='left')
        
        # Mapear códigos UF para siglas (para anotações)
        mapa_uf = {
            11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
            21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
            31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP',
            41: 'PR', 42: 'SC', 43: 'RS',
            50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
        }
        
        # Adicionar siglas ao GeoDataFrame
        gdf_merged['SIGLA'] = gdf_merged['CO_UF'].map(mapa_uf)
        
        # Calcular limites da colorbar
        vmin = df_estados[variavel].min()
        vmax = df_estados[variavel].max()
        
        # Criar a figura
        fig, ax = plt.subplots(1, 1, figsize=(15, 10))
        
        # Plotar o mapa
        gdf_merged.plot(
            column=variavel,
            ax=ax,
            cmap=palette,
            edgecolor='0.8',
            linewidth=0.8,
            legend=mostrar_legenda,
            vmin=vmin,
            vmax=vmax
        )
        
        # Adicionar título
        if titulo:
            ax.set_title(titulo, fontsize=16)
        else:
            ax.set_title(f"{variavel} por Unidade Federativa", fontsize=16)
        
        # Adicionar labels com siglas dos estados
        if mostrar_valores:
            for idx, row in gdf_merged.iterrows():
                valor = row[variavel]
                if not pd.isna(valor):
                    valor_str = f"{valor:.1f}"
                    ax.annotate(
                        f"{row['SIGLA']}\n{valor_str}",
                        xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                        ha='center',
                        va='center',
                        fontsize=8,
                        color='black',
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.7)
                    )
                else:
                    ax.annotate(
                        f"{row['SIGLA']}\nN/A",
                        xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                        ha='center',
                        va='center',
                        fontsize=8,
                        color='black',
                        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.7)
                    )
        else:
            for idx, row in gdf_merged.iterrows():
                ax.annotate(
                    f"{row['SIGLA']}",
                    xy=(row.geometry.centroid.x, row.geometry.centroid.y),
                    ha='center',
                    va='center',
                    fontsize=8,
                    color='black',
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.7)
                )
        
        # Remover eixos
        ax.set_axis_off()
        
        # Adicionar legenda se necessário
        if mostrar_legenda:
            sm = plt.cm.ScalarMappable(cmap=palette, norm=plt.Normalize(vmin=vmin, vmax=vmax))
            sm._A = []
            divider = make_axes_locatable(ax)
            cax = divider.append_axes("right", size="5%", pad=0.1)
            cbar = fig.colorbar(sm, cax=cax)
            cbar.set_label(variavel)
        
        # Salvar ou exibir
        if output_path:
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            plt.close()
            logger.info(f"Mapa salvo em {output_path}")
            return True
        else:
            plt.tight_layout()
            plt.show()
            return True
            
    except Exception as e:
        logger.error(f"Erro ao gerar mapa por UF: {str(e)}")
        return False


def gerar_mapa_municipios(df_municipios, variavel='TAXA_ABANDONO', titulo=None, 
                        uf_codigo=None, palette='OrRd', output_path=None):
    """
    Gera mapa coroplético por municípios
    
    Args:
        df_municipios (pandas.DataFrame): DataFrame com dados por município
        variavel (str): Nome da variável a ser visualizada
        titulo (str, optional): Título do mapa
        uf_codigo (int, optional): Código da UF para filtrar apenas municípios de um estado
        palette (str): Paleta de cores do mapa
        output_path (Path, optional): Caminho para salvar o mapa
        
    Returns:
        bool: True se o mapa foi gerado com sucesso
    """
    try:
        # Carregar shapefile dos municípios
        shapefiles = baixar_shapefile_brasil()
        if 'Brasil_Municipios' not in shapefiles:
            logger.error("Shapefile dos municípios não disponível")
            return False
        
        # Carregar o shapefile com geopandas
        gdf_municipios = gpd.read_file(shapefiles['Brasil_Municipios'])
        
        # Verificar se há coluna de código município no DataFrame
        if 'CO_MUNICIPIO' not in df_municipios.columns:
            logger.error("Coluna 'CO_MUNICIPIO' não encontrada nos dados")
            return False
        
        # Verificar se variável existe no DataFrame
        if variavel not in df_municipios.columns:
            logger.error(f"Variável '{variavel}' não encontrada nos dados")
            return False
        
        # Normalizar nomes de colunas
        gdf_municipios = gdf_municipios.rename(columns={'CD_MUN': 'CO_MUNICIPIO'})
        
        # Converter códigos para mesmo tipo
        gdf_municipios['CO_MUNICIPIO'] = gdf_municipios['CO_MUNICIPIO'].astype(int)
        df_municipios['CO_MUNICIPIO'] = df_municipios['CO_MUNICIPIO'].astype(int)
        
        # Filtrar por UF se especificado
        if uf_codigo:
            if 'CO_UF' in df_municipios.columns:
                df_municipios = df_municipios[df_municipios['CO_UF'] == uf_codigo]
                # Também filtrar o shapefile
                gdf_municipios = gdf_municipios[gdf_municipios['CO_MUNICIPIO'] // 1000 == uf_codigo]
                logger.info(f"Dados filtrados para UF {uf_codigo}: {len(df_municipios)} municípios")
            else:
                logger.warning("Coluna 'CO_UF' não encontrada para filtrar por UF")
        
        # Mesclar dados com shapefile
        gdf_merged = gdf_municipios.merge(df_municipios, on='CO_MUNICIPIO', how='left')
        
        # Calcular limites da colorbar
        vmin = df_municipios[variavel].min()
        vmax = df_municipios[variavel].max()
        
        # Criar a figura
        fig, ax = plt.subplots(1, 1, figsize=(15, 12))
        
        # Plotar o mapa
        gdf_merged.plot(
            column=variavel,
            ax=ax,
            cmap=palette,
            edgecolor='0.8',
            linewidth=0.3,
            legend=True,
            vmin=vmin,
            vmax=vmax,
            missing_kwds={
                "color": "lightgray",
                "label": "Sem dados",
            }
        )
        
        # Adicionar basemap
        try:
            ctx.add_basemap(
                ax, 
                crs=gdf_merged.crs.to_string(), 
                source=ctx.providers.CartoDB.Positron,
                alpha=0.5
            )
        except Exception as e:
            logger.warning(f"Não foi possível adicionar basemap: {str(e)}")
        
        # Adicionar título
        if titulo:
            ax.set_title(titulo, fontsize=16)
        else:
            if uf_codigo:
                uf_nome = {
                    11: 'Rondônia', 12: 'Acre', 13: 'Amazonas', 14: 'Roraima', 15: 'Pará', 16: 'Amapá', 17: 'Tocantins',
                    21: 'Maranhão', 22: 'Piauí', 23: 'Ceará', 24: 'Rio Grande do Norte', 25: 'Paraíba', 
                    26: 'Pernambuco', 27: 'Alagoas', 28: 'Sergipe', 29: 'Bahia',
                    31: 'Minas Gerais', 32: 'Espírito Santo', 33: 'Rio de Janeiro', 35: 'São Paulo',
                    41: 'Paraná', 42: 'Santa Catarina', 43: 'Rio Grande do Sul',
                    50: 'Mato Grosso do Sul', 51: 'Mato Grosso', 52: 'Goiás', 53: 'Distrito Federal'
                }.get(uf_codigo, f"UF {uf_codigo}")
                ax.set_title(f"{variavel} por Município - {uf_nome}", fontsize=16)
            else:
                ax.set_title(f"{variavel} por Município - Brasil", fontsize=16)
        
        # Remover eixos
        ax.set_axis_off()
        
        # Salvar ou exibir
        if output_path:
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            plt.close()
            logger.info(f"Mapa salvo em {output_path}")
            return True
        else:
            plt.tight_layout()
            plt.show()
            return True
            
    except Exception as e:
        logger.error(f"Erro ao gerar mapa por municípios: {str(e)}")
        return False


def gerar_mapa_clusters(df_municipios, coluna_cluster, variavel='TAXA_ABANDONO', titulo=None, 
                      output_path=None):
    """
    Gera mapa com clusters identificados por cores diferentes
    
    Args:
        df_municipios (pandas.DataFrame): DataFrame com dados por município
        coluna_cluster (str): Nome da coluna que contém os clusters
        variavel (str): Nome da variável para incluir nos tooltips e legendas
        titulo (str, optional): Título do mapa
        output_path (Path, optional): Caminho para salvar o mapa
        
    Returns:
        bool: True se o mapa foi gerado com sucesso
    """
    try:
        # Carregar shapefile dos municípios
        shapefiles = baixar_shapefile_brasil()
        if 'Brasil_Municipios' not in shapefiles:
            logger.error("Shapefile dos municípios não disponível")
            return False
        
        # Verificar se colunas existem no DataFrame
        if coluna_cluster not in df_municipios.columns:
            logger.error(f"Coluna '{coluna_cluster}' não encontrada nos dados")
            return False
        
        if 'CO_MUNICIPIO' not in df_municipios.columns:
            logger.error("Coluna 'CO_MUNICIPIO' não encontrada nos dados")
            return False
        
        # Carregar o shapefile com geopandas
        gdf_municipios = gpd.read_file(shapefiles['Brasil_Municipios'])
        
        # Normalizar nomes de colunas
        gdf_municipios = gdf_municipios.rename(columns={'CD_MUN': 'CO_MUNICIPIO'})
        
        # Converter códigos para mesmo tipo
        gdf_municipios['CO_MUNICIPIO'] = gdf_municipios['CO_MUNICIPIO'].astype(int)
        df_municipios['CO_MUNICIPIO'] = df_municipios['CO_MUNICIPIO'].astype(int)
        
        # Mesclar dados com shapefile
        gdf_merged = gdf_municipios.merge(df_municipios[['CO_MUNICIPIO', coluna_cluster, variavel]], 
                                        on='CO_MUNICIPIO', how='left')
        
        # Verificar clusters distintos
        clusters = df_municipios[coluna_cluster].dropna().unique()
        n_clusters = len(clusters)
        
        # Definir paleta de cores
        if n_clusters <= 10:
            from matplotlib.cm import tab10
            cores = [colors.rgb2hex(tab10(i)[:3]) for i in range(n_clusters)]
        else:
            # Para mais de 10 clusters, usar uma paleta contínua
            from matplotlib.cm import viridis
            cores = [colors.rgb2hex(viridis(i/n_clusters)[:3]) for i in range(n_clusters)]
        
        # Criar mapeamento de cluster para cor
        cluster_cores = {cluster: cor for cluster, cor in zip(sorted(clusters), cores)}
        
        # Criar a figura
        fig, ax = plt.subplots(1, 1, figsize=(15, 12))
        
        # Plotar cada cluster com cor específica
        for cluster, cor in cluster_cores.items():
            mask = gdf_merged[coluna_cluster] == cluster
            if mask.any():
                gdf_filtrado = gdf_merged[mask]
                gdf_filtrado.plot(
                    ax=ax,
                    color=cor,
                    edgecolor='0.8',
                    linewidth=0.3,
                    label=f"Cluster {cluster}"
                )
        
        # Plotar municípios sem dados em cinza
        mask_sem_dados = gdf_merged[coluna_cluster].isna()
        if mask_sem_dados.any():
            gdf_merged[mask_sem_dados].plot(
                ax=ax,
                color='lightgray',
                edgecolor='0.8',
                linewidth=0.3,
                label="Sem dados"
            )
        
        # Adicionar basemap
        try:
            ctx.add_basemap(
                ax, 
                crs=gdf_merged.crs.to_string(), 
                source=ctx.providers.CartoDB.Positron,
                alpha=0.3
            )
        except Exception as e:
            logger.warning(f"Não foi possível adicionar basemap: {str(e)}")
        
        # Adicionar título
        if titulo:
            ax.set_title(titulo, fontsize=16)
        else:
            ax.set_title(f"Clusters de {variavel} por Município", fontsize=16)
        
        # Adicionar legenda
        ax.legend(title=f"Clusters de {variavel}", loc='lower right')
        
        # Remover eixos
        ax.set_axis_off()
        
        # Salvar ou exibir
        if output_path:
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            plt.close()
            logger.info(f"Mapa de clusters salvo em {output_path}")
            return True
        else:
            plt.tight_layout()
            plt.show()
            return True
            
    except Exception as e:
        logger.error(f"Erro ao gerar mapa de clusters: {str(e)}")
        return False


def gerar_mapas_tematicos(ano_referencia, variavel='TAXA_ABANDONO'):
    """
    Função principal para gerar conjunto de mapas temáticos
    
    Args:
        ano_referencia (int): Ano de referência dos dados
        variavel (str): Nome da variável a ser visualizada
        
    Returns:
        dict: Dicionário com caminhos para os mapas gerados
    """
    logger.info(f"Iniciando geração de mapas temáticos para {variavel}, ano {ano_referencia}")
    
    mapas_gerados = {}
    
    # 1. Carregar dados
    df_municipios = carregar_dados(ano_referencia, nivel='municipios')
    if df_municipios is None:
        logger.error("Não foi possível carregar dados municipais")
        return mapas_gerados
    
    # Caso não exista dados estaduais, agregar a partir dos dados municipais
    df_estados = carregar_dados(ano_referencia, nivel='estados')
    if df_estados is None and 'CO_UF' in df_municipios.columns:
        logger.info("Agregando dados estaduais a partir dos dados municipais")
        df_estados = df_municipios.groupby('CO_UF').agg({
            variavel: 'mean',
            'TOTAL_ALUNOS': 'sum'
        }).reset_index()
    
    # 2. Gerar mapa por UF
    if df_estados is not None and variavel in df_estados.columns:
        output_path = PLOTS_DIR / f"mapa_uf_{variavel}_{ano_referencia}.png"
        sucesso = gerar_mapa_uf(
            df_estados, 
            variavel=variavel,
            titulo=f"Taxa de Abandono Escolar por UF ({ano_referencia})",
            output_path=output_path,
            mostrar_valores=True
        )
        if sucesso:
            mapas_gerados['mapa_uf'] = output_path
    
    # 3. Gerar mapa nacional por municípios
    if variavel in df_municipios.columns:
        output_path = PLOTS_DIR / f"mapa_municipios_{variavel}_{ano_referencia}.png"
        sucesso = gerar_mapa_municipios(
            df_municipios,
            variavel=variavel,
            titulo=f"Taxa de Abandono Escolar por Município ({ano_referencia})",
            output_path=output_path
        )
        if sucesso:
            mapas_gerados['mapa_municipios'] = output_path
    
    # 4. Gerar mapas para regiões de interesse (top 5 UFs com maior taxa)
    if df_estados is not None and variavel in df_estados.columns:
        top_ufs = df_estados.sort_values(variavel, ascending=False).head(3)
        
        for _, uf in top_ufs.iterrows():
            uf_codigo = int(uf['CO_UF'])
            output_path = PLOTS_DIR / f"mapa_municipios_uf{uf_codigo}_{variavel}_{ano_referencia}.png"
            
            # Filtrar municípios da UF
            df_mun_uf = df_municipios[df_municipios['CO_UF'] == uf_codigo]
            
            if len(df_mun_uf) > 0:
                sucesso = gerar_mapa_municipios(
                    df_mun_uf,
                    variavel=variavel,
                    uf_codigo=uf_codigo,
                    output_path=output_path
                )
                if sucesso:
                    mapas_gerados[f'mapa_municipios_uf{uf_codigo}'] = output_path
    
    # 5. Gerar mapa de clusters se disponível
    colunas_cluster = [col for col in df_municipios.columns if 'CLUSTER' in col.upper()]
    if colunas_cluster:
        coluna_cluster = colunas_cluster[0]
        output_path = PLOTS_DIR / f"mapa_clusters_{coluna_cluster}_{ano_referencia}.png"
        
        sucesso = gerar_mapa_clusters(
            df_municipios,
            coluna_cluster=coluna_cluster,
            variavel=variavel,
            titulo=f"Clusters de Abandono Escolar ({ano_referencia})",
            output_path=output_path
        )
        if sucesso:
            mapas_gerados['mapa_clusters'] = output_path
    
    logger.info(f"Gerados {len(mapas_gerados)} mapas temáticos")
    return mapas_gerados


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Geração de mapas temáticos para análise de abandono escolar')
    parser.add_argument('--ano', type=int, required=True, help='Ano de referência dos dados')
    parser.add_argument('--variavel', type=str, default='TAXA_ABANDONO', help='Variável para visualização nos mapas')
    
    args = parser.parse_args()
    
    mapas = gerar_mapas_tematicos(args.ano, variavel=args.variavel)
    
    if mapas:
        print("\nMapas gerados:")
        for nome, caminho in mapas.items():
            print(f"- {nome}: {caminho}")
    else:
        print("Nenhum mapa foi gerado.")
