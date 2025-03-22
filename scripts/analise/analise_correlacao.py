"""
Script para análise de correlações entre variáveis relacionadas ao abandono escolar.

Este script implementa análises de correlação para identificar relações
estatisticamente significativas entre o abandono escolar e diversos fatores
potencialmente associados.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import os
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("analise_correlacao.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("analise_correlacao")

# Definir diretórios
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
RESULTS_DIR = DATA_DIR / 'results'
PLOTS_DIR = BASE_DIR / 'visualizacoes' / 'graficos'

# Criar diretórios se não existirem
for directory in [DATA_DIR, PROCESSED_DIR, RESULTS_DIR, PLOTS_DIR]:
    if not directory.exists():
        directory.mkdir(parents=True)


def carregar_dados(ano_referencia):
    """
    Carrega os dados processados para análise de correlação
    
    Args:
        ano_referencia (int): Ano de referência dos dados
    
    Returns:
        dict: Dicionário com dataframes carregados
    """
    dados = {}
    
    # Carregar dados por município
    arquivo_municipios = PROCESSED_DIR / f"dados_integrados_municipios_{ano_referencia}.csv"
    if arquivo_municipios.exists():
        dados['municipios'] = pd.read_csv(arquivo_municipios)
        logger.info(f"Dados de {len(dados['municipios'])} municípios carregados")
    else:
        logger.warning(f"Arquivo {arquivo_municipios} não encontrado")
    
    # Carregar dados por escola
    arquivo_escolas = PROCESSED_DIR / f"dados_integrados_escolas_{ano_referencia}.csv"
    if arquivo_escolas.exists():
        dados['escolas'] = pd.read_csv(arquivo_escolas)
        logger.info(f"Dados de {len(dados['escolas'])} escolas carregados")
    else:
        logger.warning(f"Arquivo {arquivo_escolas} não encontrado")
    
    return dados


def calcular_matriz_correlacao(df, metodo='pearson', target_var='TAXA_ABANDONO'):
    """
    Calcula matriz de correlação entre variáveis
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        metodo (str): Método de correlação ('pearson', 'spearman', 'kendall')
        target_var (str): Variável alvo para análise
    
    Returns:
        pandas.DataFrame: Matriz de correlação
    """
    # Selecionar apenas variáveis numéricas
    df_num = df.select_dtypes(include=['int64', 'float64'])
    
    # Verificar se variável alvo está no DataFrame
    if target_var not in df_num.columns:
        logger.warning(f"Variável alvo {target_var} não encontrada no DataFrame")
        return None
    
    # Calcular matriz de correlação
    corr_matrix = df_num.corr(method=metodo)
    
    logger.info(f"Matriz de correlação calculada usando método {metodo}")
    return corr_matrix


def calcular_p_values(df, metodo='pearson'):
    """
    Calcula p-values para correlações
    
    Args:
        df (pandas.DataFrame): DataFrame com dados
        metodo (str): Método de correlação ('pearson', 'spearman')
    
    Returns:
        pandas.DataFrame: Matriz de p-values
    """
    # Selecionar apenas variáveis numéricas
    df_num = df.select_dtypes(include=['int64', 'float64'])
    
    # Inicializar matriz de p-values
    p_values = pd.DataFrame(index=df_num.columns, columns=df_num.columns)
    
    # Calcular p-values para cada par de variáveis
    for i in df_num.columns:
        for j in df_num.columns:
            if metodo == 'pearson':
                corr, p = stats.pearsonr(df_num[i].dropna(), df_num[j].dropna())
            elif metodo == 'spearman':
                corr, p = stats.spearmanr(df_num[i].dropna(), df_num[j].dropna())
            else:
                raise ValueError(f"Método {metodo} não suportado para cálculo de p-values")
            
            p_values.loc[i, j] = p
    
    logger.info(f"P-values calculados usando método {metodo}")
    return p_values


def visualizar_mapa_correlacao(corr_matrix, output_path):
    """
    Cria e salva mapa de calor da matriz de correlação
    
    Args:
        corr_matrix (pandas.DataFrame): Matriz de correlação
        output_path (Path): Caminho para salvar a visualização
    
    Returns:
        bool: True se a visualização foi salva com sucesso
    """
    try:
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(corr_matrix))
        cmap = sns.diverging_palette(230, 20, as_cmap=True)
        
        sns.heatmap(corr_matrix, mask=mask, cmap=cmap, vmax=1, vmin=-1, center=0,
                    annot=True, fmt='.2f', square=True, linewidths=.5)
        
        plt.title('Matriz de Correlação entre Variáveis', fontsize=16)
        plt.tight_layout()
        
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close()
        
        logger.info(f"Mapa de correlação salvo em {output_path}")
        return True
    except Exception as e:
        logger.error(f"Erro ao criar mapa de correlação: {str(e)}")
        return False


def visualizar_correlacoes_target(corr_matrix, target_var, p_values=None, p_threshold=0.05, output_path=None):
    """
    Cria e salva gráfico de barras mostrando correlações com a variável alvo
    
    Args:
        corr_matrix (pandas.DataFrame): Matriz de correlação
        target_var (str): Variável alvo para análise
        p_values (pandas.DataFrame, optional): Matriz de p-values
        p_threshold (float): Limiar de significância para p-values
        output_path (Path): Caminho para salvar a visualização
    
    Returns:
        pandas.Series: Correlações com a variável alvo, ordenadas
    """
    try:
        # Obter correlações com a variável alvo
        correlacoes = corr_matrix[target_var].drop(target_var).sort_values(ascending=False)
        
        # Filtrar correlações significativas
        if p_values is not None:
            p_vals_target = p_values[target_var].drop(target_var)
            significativo = p_vals_target < p_threshold
            correlacoes_sig = correlacoes[significativo]
            
            logger.info(f"Encontradas {len(correlacoes_sig)} correlações significativas (p < {p_threshold})")
        else:
            correlacoes_sig = correlacoes
        
        # Criar gráfico
        plt.figure(figsize=(12, 8))
        cores = ['#ff0d57' if x > 0 else '#1e88e5' for x in correlacoes_sig.values]
        
        bars = plt.barh(
            correlacoes_sig.index, 
            correlacoes_sig.values,
            color=cores
        )
        
        plt.title(f'Correlação com {target_var}', fontsize=16)
        plt.xlabel('Coeficiente de Correlação', fontsize=14)
        plt.grid(True, alpha=0.3, axis='x')
        plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)
        
        # Adicionar marcadores de significância
        if p_values is not None:
            for i, var in enumerate(correlacoes_sig.index):
                p_val = p_values.loc[var, target_var]
                if p_val < 0.001:
                    plt.text(correlacoes_sig[var] + 0.02 * np.sign(correlacoes_sig[var]), i, '***', 
                           ha='left' if correlacoes_sig[var] >= 0 else 'right', va='center')
                elif p_val < 0.01:
                    plt.text(correlacoes_sig[var] + 0.02 * np.sign(correlacoes_sig[var]), i, '**', 
                           ha='left' if correlacoes_sig[var] >= 0 else 'right', va='center')
                elif p_val < 0.05:
                    plt.text(correlacoes_sig[var] + 0.02 * np.sign(correlacoes_sig[var]), i, '*', 
                           ha='left' if correlacoes_sig[var] >= 0 else 'right', va='center')
        
        if output_path:
            plt.tight_layout()
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            plt.close()
            logger.info(f"Gráfico de correlações com {target_var} salvo em {output_path}")
        
        return correlacoes_sig
    except Exception as e:
        logger.error(f"Erro ao criar gráfico de correlações: {str(e)}")
        return None


def gerar_scatterplots(df, target_var, top_vars, output_dir):
    """
    Gera gráficos de dispersão entre variável alvo e principais correlacionadas
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        target_var (str): Variável alvo para análise
        top_vars (list): Lista das variáveis mais correlacionadas
        output_dir (Path): Diretório para salvar as visualizações
    
    Returns:
        int: Número de gráficos gerados com sucesso
    """
    count = 0
    
    for var in top_vars:
        try:
            plt.figure(figsize=(10, 8))
            sns.regplot(x=var, y=target_var, data=df, 
                      scatter_kws={'alpha':0.5}, line_kws={'color':'red'})
            
            plt.title(f'Relação entre {var} e {target_var}', fontsize=16)
            plt.xlabel(var, fontsize=14)
            plt.ylabel(target_var, fontsize=14)
            plt.grid(True, alpha=0.3)
            
            # Calcular e mostrar correlação
            corr_valor = np.corrcoef(df[var].dropna(), df[target_var].dropna())[0, 1]
            plt.annotate(f'Correlação: {corr_valor:.4f}', 
                       xy=(0.05, 0.95), xycoords='axes fraction',
                       bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
            
            # Salvar o gráfico
            output_path = output_dir / f'scatter_{var}_{target_var}.png'
            plt.savefig(output_path, bbox_inches='tight', dpi=300)
            plt.close()
            
            count += 1
        except Exception as e:
            logger.error(f"Erro ao criar gráfico de dispersão para {var}: {str(e)}")
    
    logger.info(f"Gerados {count} gráficos de dispersão")
    return count


def analisar_correlacoes_categoricas(df, cat_vars, target_var, output_dir):
    """
    Analisa relações entre variáveis categóricas e a variável alvo
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        cat_vars (list): Lista de variáveis categóricas
        target_var (str): Variável alvo numérica
        output_dir (Path): Diretório para salvar visualizações
    
    Returns:
        pandas.DataFrame: Resultados dos testes estatísticos
    """
    resultados = []
    count = 0
    
    for var in cat_vars:
        if var in df.columns:
            try:
                # Estatísticas por grupo
                stats_grupo = df.groupby(var)[target_var].agg(['mean', 'median', 'std', 'count']).reset_index()
                
                # Verificar se há mais de um grupo
                if len(stats_grupo) > 1:
                    # Realizar ANOVA
                    grupos = [df[df[var] == cat][target_var].dropna() for cat in df[var].unique()]
                    grupos_validos = [g for g in grupos if len(g) > 0]
                    
                    if len(grupos_validos) >= 2:
                        f_val, p_val = stats.f_oneway(*grupos_validos)
                        
                        # Criar visualização
                        plt.figure(figsize=(12, 8))
                        sns.boxplot(x=var, y=target_var, data=df)
                        plt.title(f'{target_var} por {var}', fontsize=16)
                        plt.xlabel(var, fontsize=14)
                        plt.ylabel(target_var, fontsize=14)
                        plt.grid(True, alpha=0.3, axis='y')
                        plt.annotate(f'ANOVA: p = {p_val:.4f}', 
                                   xy=(0.5, 0.01), xycoords='axes fraction',
                                   ha='center', va='bottom',
                                   fontsize=10)
                        
                        output_path = output_dir / f'boxplot_{var}_{target_var}.png'
                        plt.savefig(output_path, bbox_inches='tight', dpi=300)
                        plt.close()
                        
                        count += 1
                        
                        # Registrar resultado
                        resultados.append({
                            'Variável': var,
                            'Teste': 'ANOVA',
                            'Estatística': f_val,
                            'P-valor': p_val,
                            'Significativo': p_val < 0.05
                        })
            except Exception as e:
                logger.error(f"Erro ao analisar variável categórica {var}: {str(e)}")
    
    logger.info(f"Analisadas {count} relações entre variáveis categóricas e {target_var}")
    
    if resultados:
        return pd.DataFrame(resultados)
    else:
        return None


def executar_analise_correlacao(ano_referencia, target_var='TAXA_ABANDONO', nivel='municipios', metodo='pearson'):
    """
    Função principal para executar a análise completa de correlação
    
    Args:
        ano_referencia (int): Ano de referência dos dados
        target_var (str): Variável alvo para análise
        nivel (str): Nível de agregação dos dados ('municipios' ou 'escolas')
        metodo (str): Método de correlação ('pearson', 'spearman', 'kendall')
    
    Returns:
        dict: Dicionário com resultados da análise
    """
    logger.info(f"Iniciando análise de correlação para {target_var}, nível {nivel}, ano {ano_referencia}")
    
    # Carregar dados
    dados = carregar_dados(ano_referencia)
    
    if nivel not in dados:
        logger.error(f"Dados para nível {nivel} não disponíveis")
        return None
    
    df = dados[nivel]
    
    if target_var not in df.columns:
        logger.error(f"Variável alvo {target_var} não encontrada nos dados")
        return None
    
    resultados = {}
    
    # 1. Calcular matriz de correlação
    corr_matrix = calcular_matriz_correlacao(df, metodo=metodo, target_var=target_var)
    resultados['matriz_correlacao'] = corr_matrix
    
    # Salvar matriz de correlação
    corr_file = RESULTS_DIR / f"correlacao_{nivel}_{ano_referencia}.csv"
    corr_matrix.to_csv(corr_file)
    logger.info(f"Matriz de correlação salva em {corr_file}")
    
    # 2. Calcular p-values
    p_values = calcular_p_values(df, metodo=metodo)
    resultados['p_values'] = p_values
    
    # 3. Visualizar mapa de correlação
    mapa_path = PLOTS_DIR / f"mapa_correlacao_{nivel}_{ano_referencia}.png"
    visualizar_mapa_correlacao(corr_matrix, mapa_path)
    
    # 4. Visualizar correlações com variável alvo
    corr_target_path = PLOTS_DIR / f"correlacoes_{target_var}_{nivel}_{ano_referencia}.png"
    correlacoes_target = visualizar_correlacoes_target(
        corr_matrix, target_var, p_values, p_threshold=0.05, output_path=corr_target_path
    )
    resultados['correlacoes_target'] = correlacoes_target
    
    # 5. Gerar scatterplots para as principais correlações
    top_vars = correlacoes_target.head(5).index.tolist()
    gerar_scatterplots(df, target_var, top_vars, PLOTS_DIR)
    
    # 6. Analisar variáveis categóricas
    cat_vars = df.select_dtypes(include=['object', 'category']).columns.tolist()
    if cat_vars:
        resultados_cat = analisar_correlacoes_categoricas(df, cat_vars, target_var, PLOTS_DIR)
        resultados['analise_categorica'] = resultados_cat
    
    # 7. Gerar relatório de síntese
    # Correlações significativas com a variável alvo
    corr_target = corr_matrix[target_var].drop(target_var)
    p_target = p_values[target_var].drop(target_var)
    
    relatorio = pd.DataFrame({
        'Variável': corr_target.index,
        'Correlação': corr_target.values,
        'P-valor': p_target.values,
        'Significativo': p_target < 0.05
    })
    
    relatorio = relatorio.sort_values('Correlação', ascending=False)
    
    relatorio_file = RESULTS_DIR / f"relatorio_correlacao_{target_var}_{nivel}_{ano_referencia}.csv"
    relatorio.to_csv(relatorio_file, index=False)
    logger.info(f"Relatório de correlação salvo em {relatorio_file}")
    
    resultados['relatorio'] = relatorio
    
    logger.info("Análise de correlação concluída com sucesso")
    return resultados


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Análise de correlações para abandono escolar')
    parser.add_argument('--ano', type=int, required=True, help='Ano de referência dos dados')
    parser.add_argument('--target', type=str, default='TAXA_ABANDONO', help='Variável alvo para análise')
    parser.add_argument('--nivel', type=str, default='municipios', choices=['municipios', 'escolas'],
                       help='Nível de agregação dos dados')
    parser.add_argument('--metodo', type=str, default='pearson', choices=['pearson', 'spearman', 'kendall'],
                       help='Método de correlação')
    
    args = parser.parse_args()
    
    resultados = executar_analise_correlacao(
        args.ano, target_var=args.target, nivel=args.nivel, metodo=args.metodo
    )
    
    if resultados:
        if 'correlacoes_target' in resultados:
            print("\nPrincipais correlações com", args.target)
            print(resultados['correlacoes_target'].head(10))
