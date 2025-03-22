# Notebook: Integração de Fontes de Dados para Análise do Abandono Escolar

## 1. Introdução

Este notebook implementa a integração de múltiplas fontes de dados educacionais para análise do abandono escolar no ensino médio brasileiro. O objetivo é criar uma base de dados unificada que permita análises multidimensionais do fenômeno.

## 2. Configuração do Ambiente

# Importar bibliotecas necessárias
import pandas as pd
import numpy as np
import os
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Definir diretórios
BASE_DIR = os.path.dirname(os.path.abspath('__file__'))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RAW_DIR = os.path.join(DATA_DIR, 'raw')
PROCESSED_DIR = os.path.join(DATA_DIR, 'processed')
RESULTS_DIR = os.path.join(DATA_DIR, 'results')

# Criar diretórios se não existirem
for directory in [DATA_DIR, RAW_DIR, PROCESSED_DIR, RESULTS_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# Função para registrar log
def log_message(message, level="INFO"):
    """Registra mensagens de log com timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {level}: {message}")

log_message("Ambiente configurado com sucesso")

## 3. Carregamento dos Dados Coletados

# Definir ano de referência
ano_referencia = 2022

# Carregar dados do Censo Escolar
arquivo_censo = os.path.join(PROCESSED_DIR, f"amostra_censo_escolar_{ano_referencia}_ensino_medio.csv")
try:
    if os.path.exists(arquivo_censo):
        df_censo = pd.read_csv(arquivo_censo)
        log_message(f"Dados do Censo Escolar carregados: {df_censo.shape[0]} registros")
    else:
        log_message(f"Arquivo {arquivo_censo} não encontrado. Usando dados simulados.", "WARNING")
        # Criar dados simulados para demonstração
        np.random.seed(42)
        n_registros = 5000
        
        df_censo = pd.DataFrame({
            'NU_ANO_CENSO': [ano_referencia] * n_registros,
            'CO_UF': np.random.randint(11, 53, n_registros),
            'CO_MUNICIPIO': np.random.randint(1000000, 9999999, n_registros),
            'CO_ENTIDADE': np.random.randint(10000, 99999, n_registros),
            'TP_DEPENDENCIA': np.random.choice([1, 2, 3, 4], n_registros),  # 1=Federal, 2=Estadual, 3=Municipal, 4=Privada
            'TP_LOCALIZACAO': np.random.choice([1, 2], n_registros),  # 1=Urbana, 2=Rural
            'TP_SEXO': np.random.choice([1, 2], n_registros),  # 1=Masculino, 2=Feminino
            'TP_COR_RACA': np.random.choice([0, 1, 2, 3, 4, 5], n_registros),  # 0=Não declarada, 1=Branca, 2=Preta, etc.
            'NU_IDADE': np.random.randint(14, 21, n_registros),
            'TP_ETAPA_ENSINO': np.random.choice(range(25, 38), n_registros),
            'TP_SITUACAO': np.random.choice([1, 2, 3, 4], n_registros, p=[0.7, 0.15, 0.05, 0.1])  # 1=Aprovado, 2=Reprovado, 3=Transferido, 4=Abandono
        })
        
        log_message("Dados simulados do Censo Escolar criados para demonstração")
except Exception as e:
    log_message(f"Erro ao carregar dados do Censo Escolar: {str(e)}", "ERROR")
    df_censo = None

# Carregar dados do SAEB (similar para as outras fontes)...

## 4. Padronização e Normalização

# 4.1 Padronizar variáveis-chave no Censo Escolar
if df_censo is not None:
    log_message("Padronizando variáveis do Censo Escolar...")
    
    # Criar variável de abandono
    df_censo['ABANDONO'] = (df_censo['TP_SITUACAO'] == 4).astype(int)
    
    # Mapear códigos para categorias
    df_censo['DEPENDENCIA'] = df_censo['TP_DEPENDENCIA'].map({
        1: 'Federal', 
        2: 'Estadual', 
        3: 'Municipal', 
        4: 'Privada'
    })
    
    df_censo['LOCALIZACAO'] = df_censo['TP_LOCALIZACAO'].map({
        1: 'Urbana', 
        2: 'Rural'
    })
    
    df_censo['SEXO'] = df_censo['TP_SEXO'].map({
        1: 'Masculino', 
        2: 'Feminino'
    })
    
    df_censo['COR_RACA'] = df_censo['TP_COR_RACA'].map({
        0: 'Não declarada',
        1: 'Branca', 
        2: 'Preta', 
        3: 'Parda', 
        4: 'Amarela', 
        5: 'Indígena'
    })
    
    # Calcular distorção idade-série
    def calcular_distorcao(row):
        idade = row['NU_IDADE']
        serie = row['TP_ETAPA_ENSINO']
        
        # Simplificação para demonstração
        # Mapeando códigos para séries do ensino médio
        if serie in [25, 26, 30, 31, 35, 36]:  # Códigos para 1ª série do EM
            idade_esperada = 15
        elif serie in [27, 28, 32, 37]:  # Códigos para 2ª série do EM
            idade_esperada = 16
        elif serie in [29, 33, 38]:  # Códigos para 3ª série do EM
            idade_esperada = 17
        else:
            idade_esperada = 16  # Valor padrão para outros códigos
        
        return max(0, idade - idade_esperada)
    
    df_censo['DISTORCAO_IDADE_SERIE'] = df_censo.apply(calcular_distorcao, axis=1)
    
    log_message("Variáveis do Censo Escolar padronizadas com sucesso")

# 4.2 Padronizar variáveis em outras fontes...

## 5. Integração das Fontes

# 5.1 Agregar dados do Censo Escolar por escola
if df_censo is not None:
    log_message("Agregando dados do Censo Escolar por escola...")
    
    df_escola = df_censo.groupby('CO_ENTIDADE').agg({
        'CO_MUNICIPIO': 'first',
        'CO_UF': 'first',
        'DEPENDENCIA': 'first',
        'LOCALIZACAO': 'first',
        'ABANDONO': 'mean',  # Taxa de abandono
        'NU_ANO_CENSO': 'count'  # Total de alunos
    }).reset_index()
    
    # Renomear colunas
    df_escola = df_escola.rename(columns={
        'ABANDONO': 'TAXA_ABANDONO',
        'NU_ANO_CENSO': 'TOTAL_ALUNOS'
    })
    
    # Converter taxa de abandono para percentual
    df_escola['TAXA_ABANDONO'] = df_escola['TAXA_ABANDONO'] * 100
    
    log_message(f"Dados agregados para {df_escola.shape[0]} escolas")

# 5.2 Agregar dados do Censo Escolar por município
if df_censo is not None:
    log_message("Agregando dados do Censo Escolar por município...")
    
    df_municipio = df_censo.groupby('CO_MUNICIPIO').agg({
        'CO_UF': 'first',
        'ABANDONO': 'mean',  # Taxa de abandono
        'NU_ANO_CENSO': 'count',  # Total de alunos
        'CO_ENTIDADE': 'nunique'  # Número de escolas
    }).reset_index()
    
    # Renomear colunas
    df_municipio = df_municipio.rename(columns={
        'ABANDONO': 'TAXA_ABANDONO',
        'NU_ANO_CENSO': 'TOTAL_ALUNOS',
        'CO_ENTIDADE': 'TOTAL_ESCOLAS'
    })
    
    # Converter taxa de abandono para percentual
    df_municipio['TAXA_ABANDONO'] = df_municipio['TAXA_ABANDONO'] * 100
    
    log_message(f"Dados agregados para {df_municipio.shape[0]} municípios")

# 5.3 Integrar com dados socioeconômicos (simulados para demonstração)
log_message("Gerando dados socioeconômicos simulados para integração...")

if 'df_municipio' in locals() and df_municipio is not None:
    # Criar dados socioeconômicos simulados
    municipios_unicos = df_municipio['CO_MUNICIPIO'].unique()
    n_municipios = len(municipios_unicos)
    
    np.random.seed(42)
    dados_socioeconomicos = {
        'CO_MUNICIPIO': municipios_unicos,
        'PIB_PER_CAPITA': np.random.lognormal(10, 1, n_municipios),
        'TAXA_DESEMPREGO': np.random.beta(2, 10, n_municipios) * 100,
        'IDEB': np.random.normal(4.5, 1.2, n_municipios).clip(0, 10),
        'TAXA_POBREZA': np.random.beta(2, 7, n_municipios) * 100,
        'INDICE_GINI': np.random.beta(5, 15, n_municipios)
    }
    
    df_socioeconomico = pd.DataFrame(dados_socioeconomicos)
    
    # Integrar com dados municipais
    df_municipio_integrado = pd.merge(
        df_municipio,
        df_socioeconomico,
        on='CO_MUNICIPIO',
        how='left'
    )
    
    log_message(f"Dados socioeconômicos integrados para {df_municipio_integrado.shape[0]} municípios")
    
    # Salvar dados integrados
    df_municipio_integrado.to_csv(os.path.join(PROCESSED_DIR, f"municipios_integrado_{ano_referencia}.csv"), index=False)

# 5.4 Integrar outras fontes...

## 6. Verificação da Qualidade da Integração

# 6.1 Verificar valores ausentes
if 'df_municipio_integrado' in locals() and df_municipio_integrado is not None:
    log_message("Verificando valores ausentes nos dados integrados...")
    
    missing_counts = df_municipio_integrado.isnull().sum()
    missing_percent = (missing_counts / len(df_municipio_integrado) * 100).round(2)
    
    missing_df = pd.DataFrame({
        'Contagem': missing_counts,
        'Percentual (%)': missing_percent
    })
    
    print("\nValores ausentes por coluna:")
    print(missing_df[missing_df['Contagem'] > 0])
    
    # Tratar valores ausentes
    if missing_df['Contagem'].sum() > 0:
        log_message("Tratando valores ausentes...")
        
        # Estratégia: preencher com a média para variáveis numéricas
        numeric_cols = df_municipio_integrado.select_dtypes(include=['float64', 'int64']).columns
        for col in numeric_cols:
            if df_municipio_integrado[col].isnull().sum() > 0:
                df_municipio_integrado[col] = df_municipio_integrado[col].fillna(df_municipio_integrado[col].mean())
        
        log_message("Valores ausentes tratados")

# 6.2 Verificar consistência dos dados
if 'df_municipio_integrado' in locals() and df_municipio_integrado is not None:
    log_message("Verificando consistência dos dados integrados...")
    
    # Verificar se há taxa de abandono fora do intervalo [0, 100]
    taxa_invalida = ((df_municipio_integrado['TAXA_ABANDONO'] < 0) | 
                    (df_municipio_integrado['TAXA_ABANDONO'] > 100)).sum()
    
    if taxa_invalida > 0:
        log_message(f"Encontradas {taxa_invalida} taxas de abandono inválidas. Corrigindo...", "WARNING")
        df_municipio_integrado['TAXA_ABANDONO'] = df_municipio_integrado['TAXA_ABANDONO'].clip(0, 100)
    
    # Verificar correlações esperadas
    corr_taxa_pobreza = df_municipio_integrado[['TAXA_ABANDONO', 'TAXA_POBREZA']].corr().iloc[0, 1]
    corr_ideb = df_municipio_integrado[['TAXA_ABANDONO', 'IDEB']].corr().iloc[0, 1]
    
    log_message(f"Correlação entre taxa de abandono e pobreza: {corr_taxa_pobreza:.4f}")
    log_message(f"Correlação entre taxa de abandono e IDEB: {corr_ideb:.4f}")
    
    if corr_taxa_pobreza < 0 or corr_ideb > 0:
        log_message("Correlações apresentam direção inesperada. Verificar dados.", "WARNING")

## 7. Criação de Features Adicionais

if 'df_municipio_integrado' in locals() and df_municipio_integrado is not None:
    log_message("Criando features adicionais...")
    
    # Categorização da taxa de abandono
    df_municipio_integrado['CATEGORIA_ABANDONO'] = pd.cut(
        df_municipio_integrado['TAXA_ABANDONO'],
        bins=[0, 5, 10, 15, 100],
        labels=['Baixo (0-5%)', 'Médio (5-10%)', 'Alto (10-15%)', 'Muito Alto (>15%)']
    )
    
    # Categorização socioeconômica
    df_municipio_integrado['NIVEL_POBREZA'] = pd.qcut(
        df_municipio_integrado['TAXA_POBREZA'],
        q=4,
        labels=['Baixo', 'Médio-Baixo', 'Médio-Alto', 'Alto']
    )
    
    # Índice composto de vulnerabilidade
    df_municipio_integrado['INDICE_VULNERABILIDADE'] = (
        df_municipio_integrado['TAXA_POBREZA'] / 100 +
        df_municipio_integrado['TAXA_DESEMPREGO'] / 100 +
        df_municipio_integrado['INDICE_GINI'] -
        df_municipio_integrado['IDEB'] / 10
    )
    
    log_message("Features adicionais criadas com sucesso")

## 8. Exportação dos Dados Integrados

# 8.1 Exportar dados para análise exploratória
if 'df_municipio_integrado' in locals() and df_municipio_integrado is not None:
    output_file = os.path.join(PROCESSED_DIR, f"dados_integrados_municipios_{ano_referencia}.csv")
    df_municipio_integrado.to_csv(output_file, index=False)
    log_message(f"Dados integrados por município exportados para: {output_file}")

if 'df_escola' in locals() and df_escola is not None:
    output_file = os.path.join(PROCESSED_DIR, f"dados_integrados_escolas_{ano_referencia}.csv")
    df_escola.to_csv(output_file, index=False)
    log_message(f"Dados integrados por escola exportados para: {output_file}")

# 8.2 Exportar dicionário de dados
if 'df_municipio_integrado' in locals() and df_municipio_integrado is not None:
    # Criar dicionário de dados
    dicionario = pd.DataFrame({
        'Variável': df_municipio_integrado.columns,
        'Tipo': df_municipio_integrado.dtypes.astype(str),
        'Descrição': [
            'Código do município (IBGE)',
            'Código da UF',
            'Taxa de abandono escolar (%)',
            'Total de alunos no ensino médio',
            'Total de escolas com ensino médio',
            'PIB per capita (R$)',
            'Taxa de desemprego (%)',
            'Índice de Desenvolvimento da Educação Básica',
            'Taxa de pobreza (%)',
            'Índice de Gini (desigualdade)',
            'Categoria de abandono escolar',
            'Nível de pobreza (quartis)',
            'Índice composto de vulnerabilidade'
        ]
    })
    
    output_file = os.path.join(PROCESSED_DIR, "dicionario_dados_integrados.csv")
    dicionario.to_csv(output_file, index=False)
    log_message(f"Dicionário de dados exportado para: {output_file}")

## 9. Resumo e Próximos Passos

log_message("=== Resumo da Integração de Dados ===")
if 'df_municipio_integrado' in locals() and df_municipio_integrado is not None:
    log_message(f"Dados integrados para {df_municipio_integrado.shape[0]} municípios")
    log_message(f"Total de variáveis disponíveis: {df_municipio_integrado.shape[1]}")
    log_message(f"Taxa média de abandono: {df_municipio_integrado['TAXA_ABANDONO'].mean():.2f}%")
    log_message(f"Distribuição por categoria de abandono:")
    print(df_municipio_integrado['CATEGORIA_ABANDONO'].value_counts(normalize=True).mul(100).round(1))

log_message("Próximos passos: Análise Exploratória de Dados no notebook 3_analise_exploratoria.ipynb")
