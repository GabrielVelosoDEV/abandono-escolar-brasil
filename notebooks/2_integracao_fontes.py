# Notebook: Análise Exploratória de Dados - Abandono Escolar no Ensino Médio

## 1. Introdução

Este notebook realiza a análise exploratória dos dados integrados sobre abandono escolar no ensino médio brasileiro. O objetivo é identificar padrões, correlações e insights iniciais que orientarão as etapas subsequentes de modelagem e visualização.

## 2. Configuração do Ambiente

# Importar bibliotecas necessárias
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
import statsmodels.api as sm
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configurações de visualização
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 12
cores = ["#1e88e5", "#ff0d57", "#13b755", "#7c52ff", "#ffc000"]

# Definir diretórios
BASE_DIR = os.path.dirname(os.path.abspath('__file__'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
RESULTS_DIR = os.path.join(DATA_DIR, 'results')
PLOTS_DIR = os.path.join(BASE_DIR, 'visualizacoes/graficos')

# Criar diretórios se não existirem
for directory in [DATA_DIR, PROCESSED_DIR, RESULTS_DIR, PLOTS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Função para registrar log
def log_message(message, level="INFO"):
    """Registra mensagens de log com timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

log_message("Ambiente configurado com sucesso")

## 3. Carregamento dos Dados Integrados

# Definir ano de referência
ano_referencia = 2022

# Carregar dados por município
arquivo_municipios = os.path.join(PROCESSED_DIR, f"dados_integrados_municipios_{ano_referencia}.csv")
if os.path.exists(arquivo_municipios):
    df_municipios = pd.read_csv(arquivo_municipios)
    log_message(f"Dados de {len(df_municipios)} municípios carregados com sucesso")
else:
    log_message(f"Arquivo {arquivo_municipios} não encontrado.", "WARNING")
    # Criar dados simulados para demonstração
    df_municipios = None

# Carregar dados por escola
arquivo_escolas = os.path.join(PROCESSED_DIR, f"dados_integrados_escolas_{ano_referencia}.csv")
if os.path.exists(arquivo_escolas):
    df_escolas = pd.read_csv(arquivo_escolas)
    log_message(f"Dados de {len(df_escolas)} escolas carregados com sucesso")
else:
    log_message(f"Arquivo {arquivo_escolas} não encontrado.", "WARNING")
    # Criar dados simulados para demonstração
    df_escolas = None

# Se os dados não foram encontrados, criar dados simulados para demonstração
if df_municipios is None and df_escolas is None:
    log_message("Criando dados simulados para demonstração", "WARNING")
    
    # Simulação de dados municipais
    np.random.seed(42)
    n_municipios = 500
    
    df_municipios = pd.DataFrame({
        'CO_MUNICIPIO': np.random.randint(1000000, 9999999, n_municipios),
        'CO_UF': np.random.choice(range(11, 53), n_municipios),
        'TAXA_ABANDONO': np.random.beta(2, 15, n_municipios) * 100,
        'TOTAL_ALUNOS': np.random.randint(200, 10000, n_municipios),
        'TOTAL_ESCOLAS': np.random.randint(1, 50, n_municipios),
        'PIB_PER_CAPITA': np.random.lognormal(10, 1, n_municipios),
        'TAXA_DESEMPREGO': np.random.beta(2, 10, n_municipios) * 100,
        'IDEB': np.random.normal(4.5, 1.2, n_municipios).clip(0, 10),
        'TAXA_POBREZA': np.random.beta(2, 7, n_municipios) * 100,
        'INDICE_GINI': np.random.beta(5, 15, n_municipios),
    })
    
    # Adicionar variáveis categóricas
    df_municipios['CATEGORIA_ABANDONO'] = pd.cut(
        df_municipios['TAXA_ABANDONO'],
        bins=[0, 5, 10, 15, 100],
        labels=['Baixo (0-5%)', 'Médio (5-10%)', 'Alto (10-15%)', 'Muito Alto (>15%)']
    )
    
    df_municipios['NIVEL_POBREZA'] = pd.qcut(
        df_municipios['TAXA_POBREZA'],
        q=4,
        labels=['Baixo', 'Médio-Baixo', 'Médio-Alto', 'Alto']
    )
    
    # Adicionar correlações realistas
    # Maior taxa de abandono associada a maior pobreza e menor IDEB
    df_municipios['TAXA_ABANDONO'] = (
        df_municipios['TAXA_ABANDONO'] + 
        0.3 * df_municipios['TAXA_POBREZA'] - 
        4 * df_municipios['IDEB'] + 
        np.random.normal(0, 3, n_municipios)
    ).clip(0, 100)
    
    # Simulação de dados escolares
    n_escolas = 2000
    
    df_escolas = pd.DataFrame({
        'CO_ENTIDADE': np.random.randint(10000, 99999, n_escolas),
        'CO_MUNICIPIO': np.random.choice(df_municipios['CO_MUNICIPIO'], n_escolas),
        'CO_UF': np.random.choice(range(11, 53), n_escolas),
        'DEPENDENCIA': np.random.choice(['Federal', 'Estadual', 'Municipal', 'Privada'], 
                                       n_escolas, p=[0.05, 0.6, 0.15, 0.2]),
        'LOCALIZACAO': np.random.choice(['Urbana', 'Rural'], n_escolas, p=[0.85, 0.15]),
        'TAXA_ABANDONO': np.random.beta(2, 15, n_escolas) * 100,
        'TOTAL_ALUNOS': np.random.randint(20, 1200, n_escolas)
    })
    
    log_message("Dados simulados criados com sucesso")

## 4. Análise Descritiva Global

log_message("Iniciando análise descritiva global...")

# 4.1 Estatísticas básicas da taxa de abandono
if df_municipios is not None:
    # Estatísticas descritivas
    abandono_stats = df_municipios['TAXA_ABANDONO'].describe()
    print("\nEstatísticas da Taxa de Abandono:")
    print(abandono_stats)
    
    # Taxa de abandono ponderada pelo número de alunos
    taxa_ponderada = (df_municipios['TAXA_ABANDONO'] * df_municipios['TOTAL_ALUNOS']).sum() / df_municipios['TOTAL_ALUNOS'].sum()
    print(f"\nTaxa de abandono média: {abandono_stats['mean']:.2f}%")
    print(f"Taxa de abandono média ponderada: {taxa_ponderada:.2f}%")
    
    # Distribuição por categoria de abandono
    print("\nDistribuição por categoria de abandono:")
    dist_categorias = df_municipios['CATEGORIA_ABANDONO'].value_counts(normalize=True).mul(100).round(1)
    print(dist_categorias)
    
    # Histograma da taxa de abandono
    plt.figure(figsize=(12, 8))
    sns.histplot(df_municipios['TAXA_ABANDONO'], kde=True, bins=30, color=cores[0])
    plt.axvline(abandono_stats['mean'], color='red', linestyle='--', 
               label=f'Média: {abandono_stats["mean"]:.2f}%')
    plt.axvline(abandono_stats['50%'], color='green', linestyle='--', 
               label=f'Mediana: {abandono_stats["50%"]:.2f}%')
    plt.title('Distribuição da Taxa de Abandono nos Municípios', fontsize=16)
    plt.xlabel('Taxa de Abandono (%)', fontsize=14)
    plt.ylabel('Frequência', fontsize=14)
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    # Salvar a figura
    plt.savefig(os.path.join(PLOTS_DIR, 'distribuicao_taxa_abandono.png'), bbox_inches='tight', dpi=300)
    plt.close()
    log_message("Histograma da taxa de abandono salvo com sucesso")

# 4.2 Análise por dependência administrativa (se dados disponíveis)
if df_escolas is not None and 'DEPENDENCIA' in df_escolas.columns:
    # Calcular taxa média por dependência administrativa
    abandono_dependencia = df_escolas.groupby('DEPENDENCIA').agg({
        'TAXA_ABANDONO': 'mean',
        'TOTAL_ALUNOS': 'sum'
    }).reset_index()
    
    # Adicionar taxa ponderada
    abandono_dependencia['TAXA_PONDERADA'] = 0
    total_alunos = df_escolas['TOTAL_ALUNOS'].sum()
    
    for i, dep in enumerate(abandono_dependencia['DEPENDENCIA']):
        escolas_dep = df_escolas[df_escolas['DEPENDENCIA'] == dep]
        taxa_pond = (escolas_dep['TAXA_ABANDONO'] * escolas_dep['TOTAL_ALUNOS']).sum() / escolas_dep['TOTAL_ALUNOS'].sum()
        abandono_dependencia.loc[i, 'TAXA_PONDERADA'] = taxa_pond
    
    print("\nTaxa de abandono por dependência administrativa:")
    print(abandono_dependencia)
    
    # Gráfico de barras
    plt.figure(figsize=(12, 8))
    sns.barplot(x='DEPENDENCIA', y='TAXA_PONDERADA', 
               data=abandono_dependencia.sort_values('TAXA_PONDERADA', ascending=False),
               palette=cores)
    
    plt.title('Taxa de Abandono por Dependência Administrativa', fontsize=16)
    plt.xlabel('Dependência Administrativa', fontsize=14)
    plt.ylabel('Taxa de Abandono (%)', fontsize=14)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Adicionar valores nas barras
    for i, v in enumerate(abandono_dependencia['TAXA_PONDERADA']):
        plt.text(i, v + 0.5, f'{v:.2f}%', ha='center', fontsize=12)
    
    # Salvar a figura
    plt.savefig(os.path.join(PLOTS_DIR, 'abandono_por_dependencia.png'), bbox_inches='tight', dpi=300)
    plt.close()
    log_message("Gráfico de abandono por dependência administrativa salvo com sucesso")

# 4.3 Análise por localização (urbana/rural)
if df_escolas is not None and 'LOCALIZACAO' in df_escolas.columns:
    # Similar ao anterior, mas para localização
    abandono_localizacao = df_escolas.groupby('LOCALIZACAO').agg({
        'TAXA_ABANDONO': 'mean',
        'TOTAL_ALUNOS': 'sum'
    }).reset_index()
    
    # Adicionar taxa ponderada
    abandono_localizacao['TAXA_PONDERADA'] = 0
    
    for i, loc in enumerate(abandono_localizacao['LOCALIZACAO']):
        escolas_loc = df_escolas[df_escolas['LOCALIZACAO'] == loc]
        taxa_pond = (escolas_loc['TAXA_ABANDONO'] * escolas_loc['TOTAL_ALUNOS']).sum() / escolas_loc['TOTAL_ALUNOS'].sum()
        abandono_localizacao.loc[i, 'TAXA_PONDERADA'] = taxa_pond
    
    print("\nTaxa de abandono por localização:")
    print(abandono_localizacao)
    
    # Gráfico de barras
    plt.figure(figsize=(10, 6))
    sns.barplot(x='LOCALIZACAO', y='TAXA_PONDERADA', 
               data=abandono_localizacao,
               palette=cores)
    
    plt.title('Taxa de Abandono por Localização', fontsize=16)
    plt.xlabel('Localização', fontsize=14)
    plt.ylabel('Taxa de Abandono (%)', fontsize=14)
    plt.grid(True, alpha=0.3, axis='y')
    
    # Adicionar valores nas barras
    for i, v in enumerate(abandono_localizacao['TAXA_PONDERADA']):
        plt.text(i, v + 0.5, f'{v:.2f}%', ha='center', fontsize=12)
    
    # Salvar a figura
    plt.savefig(os.path.join(PLOTS_DIR, 'abandono_por_localizacao.png'), bbox_inches='tight', dpi=300)
    plt.close()
    log_message("Gráfico de abandono por localização salvo com sucesso")

## 5. Análise de Correlações

if df_municipios is not None:
    log_message("Iniciando análise de correlações...")
    
    # 5.1 Selecionar variáveis numéricas relevantes
    var_numericas = ['TAXA_ABANDONO', 'TOTAL_ALUNOS', 'TOTAL_ESCOLAS', 
                     'PIB_PER_CAPITA', 'TAXA_DESEMPREGO', 'IDEB', 
                     'TAXA_POBREZA', 'INDICE_GINI']
    
    # Verificar quais variáveis existem no DataFrame
    var_existentes = [var for var in var_numericas if var in df_municipios.columns]
    
    if len(var_existentes) >= 2:
        # Calcular matriz de correlação
        corr_matrix = df_municipios[var_existentes].corr().round(3)
        print("\nMatriz de correlação:")
        print(corr_matrix)
        
        # Visualizar correlações como mapa de calor
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(corr_matrix))
        cmap = sns.diverging_palette(230, 20, as_cmap=True)
        
        sns.heatmap(corr_matrix, mask=mask, cmap=cmap, vmax=1, vmin=-1, center=0,
                    annot=True, fmt='.2f', square=True, linewidths=.5)
        
        plt.title('Correlação entre Variáveis', fontsize=16)
        plt.tight_layout()
        
        # Salvar o mapa de calor
        plt.savefig(os.path.join(PLOTS_DIR, 'mapa_correlacao.png'), bbox_inches='tight', dpi=300)
        plt.close()
        log_message("Mapa de correlação salvo com sucesso")
        
        # 5.2 Visualizar correlações com a taxa de abandono
        correlacoes_abandono = corr_matrix['TAXA_ABANDONO'].drop('TAXA_ABANDONO').sort_values(ascending=False)
        
        plt.figure(figsize=(12, 8))
        bars = plt.barh(
            correlacoes_abandono.index, 
            correlacoes_abandono.values,
            color=[cores[1] if x > 0 else cores[0] for x in correlacoes_abandono.values]
        )
        
        plt.title('Correlação com Taxa de Abandono', fontsize=16)
        plt.xlabel('Coeficiente de Correlação', fontsize=14)
        plt.grid(True, alpha=0.3, axis='x')
        plt.axvline(x=0, color='k', linestyle='-', alpha=0.3)
        
        # Salvar o gráfico
        plt.savefig(os.path.join(PLOTS_DIR, 'correlacoes_abandono.png'), bbox_inches='tight', dpi=300)
        plt.close()
        log_message("Gráfico de correlações com taxa de abandono salvo com sucesso")
        
        # 5.3 Scatterplots para as principais correlações
        top_correlacoes = correlacoes_abandono.abs().sort_values(ascending=False).head(3).index
        
        for var in top_correlacoes:
            plt.figure(figsize=(10, 8))
            sns.regplot(x=var, y='TAXA_ABANDONO', data=df_municipios, 
                      scatter_kws={'alpha':0.5}, line_kws={'color':cores[2]})
            
            plt.title(f'Relação entre {var} e Taxa de Abandono', fontsize=16)
            plt.xlabel(var, fontsize=14)
            plt.ylabel('Taxa de Abandono (%)', fontsize=14)
            plt.grid(True, alpha=0.3)
            
            # Calcular e mostrar correlação
            corr_valor = np.corrcoef(df_municipios[var], df_municipios['TAXA_ABANDONO'])[0, 1]
            plt.annotate(f'Correlação: {corr_valor:.4f}', 
                       xy=(0.05, 0.95), xycoords='axes fraction',
                       bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="gray", alpha=0.8))
            
            # Salvar o gráfico
            plt.savefig(os.path.join(PLOTS_DIR, f'scatter_{var}_abandono.png'), bbox_inches='tight', dpi=300)
            plt.close()
        
        log_message("Gráficos de dispersão salvos com sucesso")

## 6. Análise por Grupos e Categorias

if df_municipios is not None:
    log_message("Iniciando análise por grupos e categorias...")
    
    # 6.1 Análise por nível de pobreza
    if 'NIVEL_POBREZA' in df_municipios.columns:
        abandono_por_pobreza = df_municipios.groupby('NIVEL_POBREZA')['TAXA_ABANDONO'].agg(
            ['mean', 'median', 'std', 'count']).reset_index()
        
        print("\nTaxa de abandono por nível de pobreza:")
        print(abandono_por_pobreza)
        
        # Gráfico de barras
        plt.figure(figsize=(12, 8))
        sns.barplot(x='NIVEL_POBREZA', y='mean', data=abandono_por_pobreza, palette='Blues')
        
        plt.title('Taxa Média de Abandono por Nível de Pobreza', fontsize=16)
        plt.xlabel('Nível de Pobreza', fontsize=14)
        plt.ylabel('Taxa Média de Abandono (%)', fontsize=14)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Adicionar valores nas barras
        for i, v in enumerate(abandono_por_pobreza['mean']):
            plt.text(i, v + 0.5, f'{v:.2f}%', ha='center', fontsize=12)
        
        # Salvar o gráfico
        plt.savefig(os.path.join(PLOTS_DIR, 'abandono_por_nivel_pobreza.png'), bbox_inches='tight', dpi=300)
        plt.close()
        log_message("Gráfico de abandono por nível de pobreza salvo com sucesso")
    
    # 6.2 Análise por IDEB (categorizado)
    if 'IDEB' in df_municipios.columns:
        # Categorizar IDEB
        df_municipios['CATEGORIA_IDEB'] = pd.cut(
            df_municipios['IDEB'],
            bins=[0, 3, 4, 5, 10],
            labels=['Crítico (<3)', 'Baixo (3-4)', 'Intermediário (4-5)', 'Adequado (>5)']
        )
        
        abandono_por_ideb = df_municipios.groupby('CATEGORIA_IDEB')['TAXA_ABANDONO'].agg(
            ['mean', 'median', 'std', 'count']).reset_index()
        
        print("\nTaxa de abandono por categoria de IDEB:")
        print(abandono_por_ideb)
        
        # Gráfico de barras
        plt.figure(figsize=(12, 8))
        sns.barplot(x='CATEGORIA_IDEB', y='mean', data=abandono_por_ideb, palette='Greens')
        
        plt.title('Taxa Média de Abandono por Categoria de IDEB', fontsize=16)
        plt.xlabel('Categoria de IDEB', fontsize=14)
        plt.ylabel('Taxa Média de Abandono (%)', fontsize=14)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Adicionar valores nas barras
        for i, v in enumerate(abandono_por_ideb['mean']):
            plt.text(i, v + 0.5, f'{v:.2f}%', ha='center', fontsize=12)
        
        # Salvar o gráfico
        plt.savefig(os.path.join(PLOTS_DIR, 'abandono_por_categoria_ideb.png'), bbox_inches='tight', dpi=300)
        plt.close()
        log_message("Gráfico de abandono por categoria de IDEB salvo com sucesso")
    
    # 6.3 Análise por região geográfica (UF)
    if 'CO_UF' in df_municipios.columns:
        # Mapear códigos de UF para nomes (simplificado)
        mapa_uf = {
            11: 'RO', 12: 'AC', 13: 'AM', 14: 'RR', 15: 'PA', 16: 'AP', 17: 'TO',
            21: 'MA', 22: 'PI', 23: 'CE', 24: 'RN', 25: 'PB', 26: 'PE', 27: 'AL', 28: 'SE', 29: 'BA',
            31: 'MG', 32: 'ES', 33: 'RJ', 35: 'SP',
            41: 'PR', 42: 'SC', 43: 'RS',
            50: 'MS', 51: 'MT', 52: 'GO', 53: 'DF'
        }
        
        df_municipios['UF'] = df_municipios['CO_UF'].map(mapa_uf)
        
        abandono_por_uf = df_municipios.groupby('UF')['TAXA_ABANDONO'].agg(
            ['mean', 'median', 'std', 'count']).reset_index()
        
        abandono_por_uf = abandono_por_uf.sort_values('mean', ascending=False)
        
        # Gráfico de barras (top 10 UFs com maior abandono)
        plt.figure(figsize=(14, 8))
        sns.barplot(x='UF', y='mean', data=abandono_por_uf.head(10), palette='Reds')
        
        plt.title('Estados com Maiores Taxas de Abandono Escolar', fontsize=16)
        plt.xlabel('Unidade Federativa', fontsize=14)
        plt.ylabel('Taxa Média de Abandono (%)', fontsize=14)
        plt.grid(True, alpha=0.3, axis='y')
        
        # Adicionar valores nas barras
        for i, v in enumerate(abandono_por_uf.head(10)['mean']):
            plt.text(i, v + 0.5, f'{v:.2f}%', ha='center', fontsize=12)
        
        # Salvar o gráfico
        plt.savefig(os.path.join(PLOTS_DIR, 'abandono_por_uf_top10.png'), bbox_inches='tight', dpi=300)
        plt.close()
        log_message("Gráfico de abandono por UF salvo com sucesso")

## 7. Análise Bivariada e Multivariada

if df_municipios is not None:
    log_message("Iniciando análise bivariada e multivariada...")
    
    # 7.1 Relação entre pobreza, IDEB e abandono
    if all(var in df_municipios.columns for var in ['TAXA_POBREZA', 'IDEB', 'TAXA_ABANDONO']):
        plt.figure(figsize=(12, 8))
        
        sns.scatterplot(
            x='TAXA_POBREZA', 
            y='TAXA_ABANDONO',
            hue='IDEB',
            size='TOTAL_ALUNOS',
            sizes=(20, 200),
            palette='viridis',
            data=df_municipios,
            alpha=0.7
        )
        
        plt.title('Relação entre Pobreza, IDEB e Abandono Escolar', fontsize=16)
        plt.xlabel('Taxa de Pobreza (%)', fontsize=14)
        plt.ylabel('Taxa de Abandono (%)', fontsize=14)
        plt.grid(True, alpha=0.3)
        
        # Salvar o gráfico
        plt.savefig(os.path.join(PLOTS_DIR, 'relacao_pobreza_ideb_abandono.png'), bbox_inches='tight', dpi=300)
        plt.close()
        log_message("Gráfico de relação multivariada salvo com sucesso")
    
    # 7.2 Pairplot para as principais variáveis
    if all(var in df_municipios.columns for var in ['TAXA_ABANDONO', 'TAXA_POBREZA', 'IDEB', 'PIB_PER_CAPITA']):
        vars_pairplot = ['TAXA_ABANDONO', 'TAXA_POBREZA', 'IDEB', 'PIB_PER_CAPITA']
        
        # Criar amostra aleatória para pairplot (para melhor visualização)
        amostra = df_municipios.sample(min(300, len(df_municipios)), random_state=42)
        
        pairplot = sns.pairplot(
            amostra[vars_pairplot],
            diag_kind='kde',
            plot_kws={'alpha': 0.6, 's': 30, 'edgecolor': 'k', 'linewidth': 0.5},
            corner=True
        )
        
        pairplot.fig.suptitle('Relações entre Variáveis-Chave', y=1.02, fontsize=16)
        
        # Salvar o gráfico
        plt.savefig(os.path.join(PLOTS_DIR, 'pairplot_variaveis_chave.png'), bbox_inches='tight', dpi=300)
        plt.close()
        log_message("Pairplot de variáveis-chave salvo com sucesso")
    
    # 7.3 Análise de Regressão Linear Múltipla
    if all(var in df_municipios.columns for var in ['TAXA_ABANDONO', 'TAXA_POBREZA', 'IDEB', 'PIB_PER_CAPITA', 'TAXA_DESEMPREGO']):
        log_message("Realizando análise de regressão múltipla...")
        
        # Variáveis para o modelo
        X_vars = ['TAXA_POBREZA', 'IDEB', 'PIB_PER_CAPITA', 'TAXA_DESEMPREGO']
        y_var = 'TAXA_ABANDONO'
        
        # Preparar os dados
        X = df_municipios[X_vars]
        y = df_municipios[y_var]
        
        # Adicionar constante para o intercepto
        X = sm.add_constant(X)
        
        # Ajustar modelo
        model = sm.OLS(y, X).fit()
        
        # Exibir resumo do modelo
        print("\nResultados da Regressão Linear Múltipla:")
        print(model.summary())
        
        # Salvar coeficientes para uso posterior
        coefs = pd.DataFrame({
            'Variável': X_vars,
            'Coeficiente': model.params[1:],
            'P-valor': model.pvalues[1:],
            'Significativo': model.pvalues[1:] < 0.05
        })
        
        coefs.to_csv(os.path.join(RESULTS_DIR, 'coeficientes_regressao.csv'), index=False)
        log_message("Coeficientes de regressão salvos em arquivo CSV")
        
        # Gráfico de coeficientes
        plt.figure(figsize=(12, 8))
        coefs['Cor'] = coefs['Coeficiente'].apply(lambda x: cores[1] if x > 0 else cores[0])
        
        sns.barplot(x='Variável', y='Coeficiente', data=coefs, palette=coefs['Cor'])
        
        plt.title('Coeficientes de Regressão para Taxa de Abandono', fontsize=16)
        plt.xlabel('Variável', fontsize=14)
        plt.ylabel('Coeficiente', fontsize=14)
        plt.grid(True, alpha=0.3, axis='y')
        plt.axhline(y=0, color='k', linestyle='-', alpha=0.3)
        
        # Adicionar marcador para significância estatística
        for i, row in enumerate(coefs.itertuples()):
            if row.Significativo:
                plt.text(i, row.Coeficiente + (0.3 if row.Coeficiente > 0 else -0.3), 
                       '*', ha='center', fontsize=20)
        
        # Salvar o gráfico
        plt.savefig(os.path.join(PLOTS_DIR, 'coeficientes_regressao.png'), bbox_inches='tight', dpi=300)
        plt.close()
        log_message("Gráfico de coeficientes de regressão salvo com sucesso")

## 8. Análise de Distribuição Espacial

log_message("Visualizações espaciais serão geradas no notebook de análise espacial")

## 9. Resumo das Descobertas

log_message("Resumindo principais descobertas da análise exploratória...")

# Criar DataFrame para armazenar insights principais
insights = pd.DataFrame(columns=['Categoria', 'Descoberta', 'Implicação'])

# Adicionar insights (exemplos - seriam derivados da análise real)
insights = insights.append({
    'Categoria': 'Distribuição',
    'Descoberta': f'A taxa média de abandono é de {abandono_stats["mean"]:.2f}%, com grande variabilidade entre municípios (std = {abandono_stats["std"]:.2f}%)',
    'Implicação': 'Existe heterogeneidade significativa no fenômeno, sugerindo fatores locais relevantes'
}, ignore_index=True)

if 'correlacoes_abandono' in locals():
    top_var = correlacoes_abandono.abs().idxmax()
    top_corr = correlacoes_abandono.loc[top_var]
    
    insights = insights.append({
        'Categoria': 'Correlações',
        'Descoberta': f'A variável mais fortemente correlacionada com abandono é {top_var} (r = {top_corr:.2f})',
        'Implicação': f'{"Aumentos" if top_corr > 0 else "Reduções"} em {top_var} estão associados a {"aumentos" if top_corr > 0 else "reduções"} na taxa de abandono'
    }, ignore_index=True)

if 'abandono_por_pobreza' in locals():
    dif_pobreza = abandono_por_pobreza.loc[abandono_por_pobreza['NIVEL_POBREZA'] == 'Alto', 'mean'].values[0] - \
                 abandono_por_pobreza.loc[abandono_por_pobreza['NIVEL_POBREZA'] == 'Baixo', 'mean'].values[0]
    
    insights = insights.append({
        'Categoria': 'Desigualdade',
        'Descoberta': f'Municípios com alto nível de pobreza têm taxa de abandono {dif_pobreza:.2f}% maior que municípios com baixo nível',
        'Implicação': 'A desigualdade socioeconômica é um fator crítico no abandono escolar'
    }, ignore_index=True)

if 'model' in locals():
    r2 = model.rsquared
    var_sig = coefs[coefs['Significativo']]['Variável'].tolist()
    
    insights = insights.append({
        'Categoria': 'Modelagem',
        'Descoberta': f'O modelo explicativo captura {r2:.2%} da variação na taxa de abandono, com {len(var_sig)} variáveis significativas',
        'Implicação': 'Conjunto relativamente pequeno de fatores pode explicar grande parte do fenômeno'
    }, ignore_index=True)

# Salvar insights em arquivo CSV
insights.to_csv(os.path.join(RESULTS_DIR, 'insights_analise_exploratoria.csv'), index=False)
print("\nPrincipais insights da análise exploratória:")
print(insights)

log_message("Análise exploratória concluída com sucesso")
log_message("Próximos passos: Modelagem e Segmentação no notebook 4_modelagem_segmentacao.ipynb")
