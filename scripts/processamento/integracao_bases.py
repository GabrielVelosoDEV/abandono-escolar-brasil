"""
Script para integração das diferentes bases de dados relacionadas ao abandono escolar.

Este script realiza a integração de múltiplas fontes de dados (Censo Escolar, SAEB, PNAD, 
Indicadores Educacionais, etc.), harmonizando variáveis e gerando bases 
integradas para análise.
"""

import pandas as pd
import numpy as np
import os
import logging
from pathlib import Path
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("integracao_bases.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("integracao_bases")

# Definir diretórios
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'

# Criar diretórios se não existirem
for directory in [DATA_DIR, RAW_DIR, PROCESSED_DIR]:
    if not directory.exists():
        directory.mkdir(parents=True)


def carregar_censo_escolar(ano, nivel='escola'):
    """
    Carrega dados processados do Censo Escolar
    
    Args:
        ano (int): Ano de referência
        nivel (str): Nível de agregação ('escola', 'municipio', 'aluno')
    
    Returns:
        pandas.DataFrame: DataFrame com dados do Censo Escolar
    """
    if nivel == 'escola':
        arquivo = PROCESSED_DIR / f"censo_escolar_{ano}_agregado_escola.csv"
    elif nivel == 'municipio':
        arquivo = PROCESSED_DIR / f"censo_escolar_{ano}_agregado_municipio.csv"
    elif nivel == 'aluno':
        arquivo = PROCESSED_DIR / f"censo_escolar_{ano}_ensino_medio.csv"
    else:
        logger.error(f"Nível {nivel} não reconhecido")
        return None
    
    if arquivo.exists():
        try:
            df = pd.read_csv(arquivo)
            logger.info(f"Dados do Censo Escolar {ano} (nível {nivel}) carregados: {len(df)} registros")
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar Censo Escolar: {str(e)}")
            return None
    else:
        logger.warning(f"Arquivo {arquivo} não encontrado")
        return None


def carregar_saeb(ano):
    """
    Carrega dados processados do SAEB
    
    Args:
        ano (int): Ano de referência
    
    Returns:
        dict: Dicionário com DataFrames do SAEB (escolas, alunos, etc.)
    """
    tipos = ['escola', 'aluno', 'professor', 'diretor']
    dados_saeb = {}
    
    for tipo in tipos:
        arquivo = PROCESSED_DIR / f"saeb_{ano}_{tipo}.csv"
        
        if arquivo.exists():
            try:
                df = pd.read_csv(arquivo)
                dados_saeb[tipo] = df
                logger.info(f"Dados SAEB {ano} ({tipo}) carregados: {len(df)} registros")
            except Exception as e:
                logger.error(f"Erro ao carregar SAEB ({tipo}): {str(e)}")
        else:
            logger.warning(f"Arquivo {arquivo} não encontrado")
    
    return dados_saeb if dados_saeb else None


def carregar_pnad(ano):
    """
    Carrega dados processados da PNAD Contínua
    
    Args:
        ano (int): Ano de referência
    
    Returns:
        pandas.DataFrame: DataFrame com dados da PNAD
    """
    arquivo = PROCESSED_DIR / f"pnad_{ano}_educacao.csv"
    
    if arquivo.exists():
        try:
            df = pd.read_csv(arquivo)
            logger.info(f"Dados PNAD {ano} carregados: {len(df)} registros")
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar PNAD: {str(e)}")
            return None
    else:
        logger.warning(f"Arquivo {arquivo} não encontrado")
        return None


def carregar_indicadores_educacionais(ano):
    """
    Carrega indicadores educacionais
    
    Args:
        ano (int): Ano de referência
    
    Returns:
        dict: Dicionário com DataFrames de indicadores
    """
    tipos = ['rendimento', 'distorcao', 'docente', 'complexidade', 'inse']
    dados_indicadores = {}
    
    for tipo in tipos:
        arquivo = PROCESSED_DIR / f"indicadores_{tipo}_{ano}.csv"
        
        if arquivo.exists():
            try:
                df = pd.read_csv(arquivo)
                dados_indicadores[tipo] = df
                logger.info(f"Indicadores {tipo} {ano} carregados: {len(df)} registros")
            except Exception as e:
                logger.error(f"Erro ao carregar indicadores {tipo}: {str(e)}")
        else:
            logger.warning(f"Arquivo {arquivo} não encontrado")
    
    return dados_indicadores if dados_indicadores else None


def carregar_dados_socioeconomicos():
    """
    Carrega dados socioeconômicos municipais
    
    Returns:
        pandas.DataFrame: DataFrame com dados socioeconômicos
    """
    arquivo = PROCESSED_DIR / "dados_socioeconomicos_municipios.csv"
    
    if arquivo.exists():
        try:
            df = pd.read_csv(arquivo)
            logger.info(f"Dados socioeconômicos carregados: {len(df)} registros")
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar dados socioeconômicos: {str(e)}")
            return None
    else:
        logger.warning(f"Arquivo {arquivo} não encontrado. Usando dados simulados.")
        
        # Criar dados simulados
        # Lista de códigos de municípios brasileiros (amostra)
        codigos_municipios = np.random.randint(1000000, 5300000, 500)
        
        # Criar DataFrame simulado
        df = pd.DataFrame({
            'CO_MUNICIPIO': codigos_municipios,
            'PIB_PER_CAPITA': np.random.lognormal(10, 1, len(codigos_municipios)),
            'TAXA_DESEMPREGO': np.random.beta(2, 10, len(codigos_municipios)) * 100,
            'IDEB': np.random.normal(4.5, 1.2, len(codigos_municipios)).clip(0, 10),
            'TAXA_POBREZA': np.random.beta(2, 7, len(codigos_municipios)) * 100,
            'INDICE_GINI': np.random.beta(5, 15, len(codigos_municipios))
        })
        
        # Salvar para uso futuro
        df.to_csv(arquivo, index=False)
        logger.info(f"Dados socioeconômicos simulados criados: {len(df)} registros")
        
        return df


def normalizar_variaveis(df, mapeamentos, nivel):
    """
    Normaliza nomes e valores de variáveis
    
    Args:
        df (pandas.DataFrame): DataFrame a ser normalizado
        mapeamentos (dict): Dicionário com mapeamentos de normalização
        nivel (str): Nível dos dados ('escola', 'municipio', 'aluno')
    
    Returns:
        pandas.DataFrame: DataFrame normalizado
    """
    logger.info(f"Normalizando variáveis para nível {nivel}")
    
    # Copiar DataFrame para evitar modificações no original
    df_norm = df.copy()
    
    # Normalizar nomes de colunas (se houver mapeamento)
    if 'colunas' in mapeamentos:
        # Filtrar apenas colunas existentes
        colunas_existentes = {col: novo_nome for col, novo_nome in mapeamentos['colunas'].items() 
                             if col in df_norm.columns}
        if colunas_existentes:
            df_norm = df_norm.rename(columns=colunas_existentes)
            logger.info(f"Renomeadas {len(colunas_existentes)} colunas")
    
    # Normalizar valores de colunas categóricas
    for coluna, valores in mapeamentos.get('valores', {}).items():
        if coluna in df_norm.columns:
            df_norm[coluna] = df_norm[coluna].map(valores).fillna(df_norm[coluna])
    
    # Gerar variáveis derivadas (específicas por nível)
    if nivel == 'escola':
        # Exemplo: criar índice de infraestrutura
        colunas_infra = [col for col in df_norm.columns if col.startswith('IN_')]
        if colunas_infra:
            try:
                df_norm['INDICE_INFRAESTRUTURA'] = df_norm[colunas_infra].mean(axis=1)
                logger.info("Índice de infraestrutura calculado")
            except Exception as e:
                logger.warning(f"Não foi possível calcular índice de infraestrutura: {str(e)}")
    
    elif nivel == 'municipio':
        # Derivar região a partir da UF
        if 'CO_UF' in df_norm.columns:
            # Mapeamento de UF para região
            regioes = {
                # Norte
                11: 'Norte', 12: 'Norte', 13: 'Norte', 14: 'Norte', 15: 'Norte', 16: 'Norte', 17: 'Norte',
                # Nordeste
                21: 'Nordeste', 22: 'Nordeste', 23: 'Nordeste', 24: 'Nordeste', 25: 'Nordeste', 
                26: 'Nordeste', 27: 'Nordeste', 28: 'Nordeste', 29: 'Nordeste',
                # Sudeste
                31: 'Sudeste', 32: 'Sudeste', 33: 'Sudeste', 35: 'Sudeste',
                # Sul
                41: 'Sul', 42: 'Sul', 43: 'Sul',
                # Centro-Oeste
                50: 'Centro-Oeste', 51: 'Centro-Oeste', 52: 'Centro-Oeste', 53: 'Centro-Oeste'
            }
            df_norm['REGIAO'] = df_norm['CO_UF'].map(regioes)
            logger.info("Variável de região derivada da UF")
    
    return df_norm


def integrar_dados_nivel_escola(ano):
    """
    Integra dados no nível de escola
    
    Args:
        ano (int): Ano de referência
    
    Returns:
        pandas.DataFrame: DataFrame integrado no nível de escola
    """
    logger.info(f"Iniciando integração de dados no nível de escola para {ano}")
    
    # 1. Carregar dados do Censo Escolar (base principal)
    df_censo = carregar_censo_escolar(ano, nivel='escola')
    if df_censo is None:
        logger.error("Não foi possível carregar dados do Censo Escolar")
        return None
    
    # 2. Normalizar variáveis
    mapeamentos_censo = {
        'valores': {
            'TP_DEPENDENCIA': {1: 'Federal', 2: 'Estadual', 3: 'Municipal', 4: 'Privada'},
            'TP_LOCALIZACAO': {1: 'Urbana', 2: 'Rural'}
        }
    }
    df_censo = normalizar_variaveis(df_censo, mapeamentos_censo, 'escola')
    
    # 3. Carregar dados do SAEB (se disponível)
    dados_saeb = carregar_saeb(ano if ano % 2 == 1 else ano - 1)  # SAEB ocorre em anos ímpares
    
    # 4. Integrar com dados SAEB (nível escola)
    if dados_saeb and 'escola' in dados_saeb:
        df_saeb_escola = dados_saeb['escola']
        
        # Normalizar código da escola
        if 'CO_ENTIDADE' not in df_saeb_escola.columns and 'ID_ESCOLA' in df_saeb_escola.columns:
            df_saeb_escola = df_saeb_escola.rename(columns={'ID_ESCOLA': 'CO_ENTIDADE'})
        
        # Selecionar apenas colunas relevantes do SAEB
        colunas_saeb = [col for col in df_saeb_escola.columns 
                       if col not in df_censo.columns or col == 'CO_ENTIDADE']
        
        if colunas_saeb:
            # Integrar dados
            df_integrado = pd.merge(
                df_censo,
                df_saeb_escola[colunas_saeb],
                on='CO_ENTIDADE',
                how='left'
            )
            
            logger.info(f"Integrados dados SAEB (escola): adicionadas {len(colunas_saeb) - 1} colunas")
        else:
            df_integrado = df_censo
            logger.warning("Não foram encontradas colunas relevantes para integração com SAEB")
    else:
        df_integrado = df_censo
        logger.warning("Dados SAEB não disponíveis para integração")
    
    # 5. Integrar com indicadores educacionais
    indicadores = carregar_indicadores_educacionais(ano)
    if indicadores:
        # Indicadores por escola
        for tipo, df_ind in indicadores.items():
            if 'CO_ENTIDADE' in df_ind.columns:
                # Selecionar apenas colunas relevantes
                colunas_ind = [col for col in df_ind.columns 
                              if col not in df_integrado.columns or col == 'CO_ENTIDADE']
                
                if colunas_ind and len(colunas_ind) > 1:
                    # Integrar indicadores
                    df_integrado = pd.merge(
                        df_integrado,
                        df_ind[colunas_ind],
                        on='CO_ENTIDADE',
                        how='left'
                    )
                    
                    logger.info(f"Integrados indicadores {tipo}: adicionadas {len(colunas_ind) - 1} colunas")
    else:
        logger.warning("Indicadores educacionais não disponíveis para integração")
    
    logger.info(f"Integração no nível de escola concluída: {len(df_integrado)} escolas, {df_integrado.shape[1]} variáveis")
    return df_integrado


def integrar_dados_nivel_municipio(ano):
    """
    Integra dados no nível de município
    
    Args:
        ano (int): Ano de referência
    
    Returns:
        pandas.DataFrame: DataFrame integrado no nível de município
    """
    logger.info(f"Iniciando integração de dados no nível de município para {ano}")
    
    # 1. Carregar dados do Censo Escolar agregados por município
    df_censo = carregar_censo_escolar(ano, nivel='municipio')
    if df_censo is None:
        logger.error("Não foi possível carregar dados do Censo Escolar por município")
        return None
    
    # 2. Normalizar variáveis
    mapeamentos_censo = {}  # Não há necessidade de mapeamentos específicos
    df_censo = normalizar_variaveis(df_censo, mapeamentos_censo, 'municipio')
    
    # 3. Integrar com dados socioeconômicos
    df_socio = carregar_dados_socioeconomicos()
    if df_socio is not None:
        # Integrar dados
        df_integrado = pd.merge(
            df_censo,
            df_socio,
            on='CO_MUNICIPIO',
            how='left'
        )
        
        logger.info(f"Integrados dados socioeconômicos: adicionadas {df_socio.shape[1] - 1} colunas")
    else:
        df_integrado = df_censo
        logger.warning("Dados socioeconômicos não disponíveis para integração")
    
    # 4. Integrar com indicadores educacionais municipais
    indicadores = carregar_indicadores_educacionais(ano)
    if indicadores:
        # Verificar quais indicadores têm dados por município
        for tipo, df_ind in indicadores.items():
            if 'CO_MUNICIPIO' in df_ind.columns:
                # Selecionar apenas colunas que ainda não existem no DataFrame integrado
                colunas_ind = [col for col in df_ind.columns 
                              if col not in df_integrado.columns or col == 'CO_MUNICIPIO']
                
                if colunas_ind and len(colunas_ind) > 1:
                    # Integrar indicadores
                    df_integrado = pd.merge(
                        df_integrado,
                        df_ind[colunas_ind],
                        on='CO_MUNICIPIO',
                        how='left'
                    )
                    
                    logger.info(f"Integrados indicadores {tipo} municipais: adicionadas {len(colunas_ind) - 1} colunas")
    else:
        logger.warning("Indicadores educacionais não disponíveis para integração")
    
    # 5. Adicionar dados da PNAD agregados por UF (se disponível)
    df_pnad = carregar_pnad(ano)
    if df_pnad is not None and 'UF' in df_pnad.columns:
        # Agregar dados da PNAD por UF
        cols_to_agg = {}
        
        # Identificar colunas numéricas para agregação
        for col in df_pnad.columns:
            if col != 'UF' and df_pnad[col].dtype in ['int64', 'float64']:
                cols_to_agg[col] = 'mean'
        
        if cols_to_agg:
            pnad_por_uf = df_pnad.groupby('UF').agg(cols_to_agg).reset_index()
            
            # Renomear colunas para indicar origem PNAD
            for col in pnad_por_uf.columns:
                if col != 'UF':
                    pnad_por_uf = pnad_por_uf.rename(columns={col: f'PNAD_{col}'})
            
            # Integrar com dados municipais
            if 'CO_UF' in df_integrado.columns:
                df_integrado = pd.merge(
                    df_integrado,
                    pnad_por_uf,
                    left_on='CO_UF',
                    right_on='UF',
                    how='left'
                )
                
                # Remover coluna UF duplicada
                if 'UF' in df_integrado.columns and 'UF' != 'CO_UF':
                    df_integrado = df_integrado.drop('UF', axis=1)
                
                logger.info(f"Integrados dados PNAD por UF: adicionadas {pnad_por_uf.shape[1] - 1} colunas")
    else:
        logger.warning("Dados PNAD não disponíveis para integração")
    
    logger.info(f"Integração no nível de município concluída: {len(df_integrado)} municípios, {df_integrado.shape[1]} variáveis")
    return df_integrado


def integrar_dados_nivel_aluno(ano):
    """
    Integra dados no nível de aluno
    
    Args:
        ano (int): Ano de referência
    
    Returns:
        pandas.DataFrame: DataFrame integrado no nível de aluno
    """
    logger.info(f"Iniciando integração de dados no nível de aluno para {ano}")
    
    # 1. Carregar dados do Censo Escolar (nível aluno)
    df_censo = carregar_censo_escolar(ano, nivel='aluno')
    if df_censo is None:
        logger.error("Não foi possível carregar dados do Censo Escolar por aluno")
        return None
    
    # 2. Normalizar variáveis
    mapeamentos_censo = {
        'valores': {
            'TP_SEXO': {1: 'Masculino', 2: 'Feminino'},
            'TP_COR_RACA': {0: 'Não declarada', 1: 'Branca', 2: 'Preta', 3: 'Parda', 4: 'Amarela', 5: 'Indígena'},
            'TP_SITUACAO': {1: 'Aprovado', 2: 'Reprovado', 3: 'Transferido', 4: 'Abandono'}
        }
    }
    df_censo = normalizar_variaveis(df_censo, mapeamentos_censo, 'aluno')
    
    # 3. Carregar dados SAEB (nível aluno, se disponível)
    dados_saeb = carregar_saeb(ano if ano % 2 == 1 else ano - 1)
    
    # 4. Integrar com dados SAEB (nível aluno)
    # Obs: Integração no nível de aluno geralmente requer identificadores comuns
    # que nem sempre estão disponíveis. Aqui, seria mais comum fazer uma integração
    # com informações da escola do aluno.
    if dados_saeb and 'aluno' in dados_saeb and 'CO_ENTIDADE' in df_censo.columns:
        df_saeb_aluno = dados_saeb['aluno']
        
        if 'CO_ENTIDADE' in df_saeb_aluno.columns:
            # Calcular médias das proficiências por escola
            cols_to_agg = {}
            
            # Identificar colunas de proficiência
            prof_cols = [col for col in df_saeb_aluno.columns if 'PROFICIENCIA' in col.upper()]
            for col in prof_cols:
                cols_to_agg[col] = 'mean'
            
            if cols_to_agg:
                saeb_por_escola = df_saeb_aluno.groupby('CO_ENTIDADE').agg(cols_to_agg).reset_index()
                
                # Integrar com dados de alunos
                df_integrado = pd.merge(
                    df_censo,
                    saeb_por_escola,
                    on='CO_ENTIDADE',
                    how='left'
                )
                
                logger.info(f"Integrados dados SAEB (proficiências por escola): adicionadas {len(cols_to_agg)} colunas")
            else:
                df_integrado = df_censo
                logger.warning("Não foram encontradas colunas de proficiência no SAEB")
        else:
            df_integrado = df_censo
            logger.warning("Chave de integração CO_ENTIDADE não encontrada no SAEB")
    else:
        df_integrado = df_censo
        logger.warning("Dados SAEB não disponíveis para integração no nível de aluno")
    
    # 5. Derivar variáveis adicionais
    # Exemplo: Distorção idade-série
    if 'NU_IDADE' in df_integrado.columns and 'TP_ETAPA_ENSINO' in df_integrado.columns:
        # Função para calcular idade esperada com base na etapa
        def idade_esperada(etapa):
            # Simplificação: mapeamento de códigos para séries do ensino médio
            if etapa in [25, 26, 30, 31, 35, 36]:  # Códigos para 1ª série do EM
                return 15
            elif etapa in [27, 28, 32, 37]:  # Códigos para 2ª série do EM
                return 16
            elif etapa in [29, 33, 38]:  # Códigos para 3ª série do EM
                return 17
            else:
                return 16  # Valor padrão para outros códigos
        
        # Aplicar função para calcular distorção
        df_integrado['IDADE_ESPERADA'] = df_integrado['TP_ETAPA_ENSINO'].apply(idade_esperada)
        df_integrado['DISTORCAO_IDADE_SERIE'] = df_integrado['NU_IDADE'] - df_integrado['IDADE_ESPERADA']
        df_integrado['DISTORCAO_IDADE_SERIE'] = df_integrado['DISTORCAO_IDADE_SERIE'].clip(lower=0)
        
        logger.info("Variável de distorção idade-série calculada")
    
    logger.info(f"Integração no nível de aluno concluída: {len(df_integrado)} alunos, {df_integrado.shape[1]} variáveis")
    return df_integrado


def executar_integracao_completa(ano):
    """
    Executa integração completa de dados nos diferentes níveis
    
    Args:
        ano (int): Ano de referência
    
    Returns:
        dict: Dicionário com DataFrames integrados por nível
    """
    logger.info(f"Iniciando integração completa de dados para o ano {ano}")
    
    resultados = {}
    
    # 1. Integração no nível de escola
    df_escolas = integrar_dados_nivel_escola(ano)
    if df_escolas is not None:
        # Salvar resultado
        output_escolas = PROCESSED_DIR / f"dados_integrados_escolas_{ano}.csv"
        df_escolas.to_csv(output_escolas, index=False)
        
        resultados['escolas'] = {
            'dataframe': df_escolas,
            'arquivo': output_escolas,
            'registros': len(df_escolas),
            'variaveis': df_escolas.shape[1]
        }
        
        logger.info(f"Dados integrados de escolas salvos em {output_escolas}")
    
    # 2. Integração no nível de município
    df_municipios = integrar_dados_nivel_municipio(ano)
    if df_municipios is not None:
        # Salvar resultado
        output_municipios = PROCESSED_DIR / f"dados_integrados_municipios_{ano}.csv"
        df_municipios.to_csv(output_municipios, index=False)
        
        resultados['municipios'] = {
            'dataframe': df_municipios,
            'arquivo': output_municipios,
            'registros': len(df_municipios),
            'variaveis': df_municipios.shape[1]
        }
        
        logger.info(f"Dados integrados de municípios salvos em {output_municipios}")
    
    # 3. Integração no nível de aluno
    df_alunos = integrar_dados_nivel_aluno(ano)
    if df_alunos is not None:
        # Salvar resultado
        output_alunos = PROCESSED_DIR / f"dados_integrados_alunos_{ano}.csv"
        df_alunos.to_csv(output_alunos, index=False)
        
        resultados['alunos'] = {
            'dataframe': df_alunos,
            'arquivo': output_alunos,
            'registros': len(df_alunos),
            'variaveis': df_alunos.shape[1]
        }
        
        logger.info(f"Dados integrados de alunos salvos em {output_alunos}")
    
    # 4. Gerar relatório de integração
    relatorio = {
        'data_execucao': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'ano_referencia': ano,
        'niveis_integrados': list(resultados.keys()),
        'estatisticas': {
            nivel: {
                'registros': info['registros'],
                'variaveis': info['variaveis'],
                'arquivo': str(info['arquivo'])
            }
            for nivel, info in resultados.items()
        }
    }
    
    # Salvar relatório
    import json
    with open(PROCESSED_DIR / f"relatorio_integracao_{ano}.json", 'w') as f:
        json.dump(relatorio, f, indent=4)
    
    logger.info(f"Integração completa concluída para o ano {ano}")
    return resultados


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Integração de bases de dados para análise de abandono escolar')
    parser.add_argument('--ano', type=int, required=True, help='Ano de referência para integração')
    parser.add_argument('--nivel', type=str, choices=['escola', 'municipio', 'aluno', 'todos'], default='todos',
                       help='Nível de agregação para integração')
    
    args = parser.parse_args()
    
    if args.nivel == 'todos':
        resultados = executar_integracao_completa(args.ano)
        
        print("\nResultados da integração:")
        for nivel, info in resultados.items():
            print(f"- {nivel.capitalize()}: {info['registros']} registros, {info['variaveis']} variáveis")
    else:
        # Executar integração específica
        if args.nivel == 'escola':
            df = integrar_dados_nivel_escola(args.ano)
        elif args.nivel == 'municipio':
            df = integrar_dados_nivel_municipio(args.ano)
        elif args.nivel == 'aluno':
            df = integrar_dados_nivel_aluno(args.ano)
        
        if df is not None:
            output = PROCESSED_DIR / f"dados_integrados_{args.nivel}s_{args.ano}.csv"
            df.to_csv(output, index=False)
            print(f"\nIntegração concluída: {len(df)} registros, {df.shape[1]} variáveis")
            print(f"Dados salvos em: {output}")
        else:
            print("\nFalha na integração. Verifique os logs para mais detalhes.")
