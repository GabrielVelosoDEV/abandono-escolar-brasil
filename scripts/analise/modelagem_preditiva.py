"""
Script para desenvolvimento de modelos preditivos para abandono escolar.

Este script implementa algoritmos de machine learning para prever o risco
de abandono escolar e identificar os fatores mais relevantes para a predição.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report,
    roc_curve, precision_recall_curve, average_precision_score
)
import joblib
import os
import logging
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("modelagem_preditiva.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("modelagem_preditiva")

# Definir diretórios
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / 'data'
PROCESSED_DIR = DATA_DIR / 'processed'
RESULTS_DIR = DATA_DIR / 'results'
MODELS_DIR = RESULTS_DIR / 'models'
PLOTS_DIR = BASE_DIR / 'visualizacoes' / 'graficos'

# Criar diretórios se não existirem
for directory in [DATA_DIR, PROCESSED_DIR, RESULTS_DIR, MODELS_DIR, PLOTS_DIR]:
    if not directory.exists():
        directory.mkdir(parents=True)


def carregar_dados_alunos(ano_referencia):
    """
    Carrega dados no nível de alunos para modelagem preditiva
    
    Args:
        ano_referencia (int): Ano de referência dos dados
        
    Returns:
        pandas.DataFrame: DataFrame com dados de alunos
    """
    arquivo = PROCESSED_DIR / f"dados_alunos_{ano_referencia}.csv"
    
    if arquivo.exists():
        try:
            df = pd.read_csv(arquivo)
            logger.info(f"Dados de {len(df)} alunos carregados com sucesso")
            return df
        except Exception as e:
            logger.error(f"Erro ao carregar arquivo {arquivo}: {str(e)}")
            return None
    else:
        logger.warning(f"Arquivo {arquivo} não encontrado. Usando dados simulados.")
        
        # Criar dados simulados para demonstração
        n_alunos = 10000
        np.random.seed(42)
        
        # Simular variáveis independentes (features)
        df_simulado = pd.DataFrame({
            'ID_ALUNO': range(1, n_alunos + 1),
            'SEXO': np.random.choice([0, 1], n_alunos),  # 0=Masculino, 1=Feminino
            'IDADE': np.random.randint(14, 22, n_alunos),
            'RACA_COR': np.random.choice([1, 2, 3, 4, 5], n_alunos),  # 1=Branca, 2=Preta, 3=Parda...
            'RENDA_FAMILIAR': np.random.choice([1, 2, 3, 4, 5], n_alunos, p=[0.2, 0.3, 0.25, 0.15, 0.1]),  # Quintis
            'ESCOLARIDADE_MAE': np.random.choice([1, 2, 3, 4, 5], n_alunos),  # 1=Sem escolaridade até 5=Superior
            'TRABALHA': np.random.choice([0, 1], n_alunos, p=[0.7, 0.3]),
            'HORAS_TRABALHO': np.random.choice([0, 10, 20, 30, 40], n_alunos, p=[0.7, 0.05, 0.1, 0.1, 0.05]),
            'REPROVACOES': np.random.choice([0, 1, 2, 3, 4], n_alunos, p=[0.6, 0.2, 0.1, 0.07, 0.03]),
            'DESEMPENHO_MEDIO': np.random.normal(6, 2, n_alunos).clip(0, 10),
            'FREQUENCIA': np.random.beta(5, 2, n_alunos) * 100,
            'DISTANCIA_ESCOLA_KM': np.random.exponential(5, n_alunos),
            'ENGAJAMENTO': np.random.normal(5, 2, n_alunos).clip(0, 10),
            'ATIVIDADES_EXTRACURRICULARES': np.random.choice([0, 1, 2, 3], n_alunos, p=[0.5, 0.3, 0.15, 0.05])
        })
        
        # Adicionar variável de distorção idade-série
        df_simulado['DISTORCAO_IDADE_SERIE'] = np.where(df_simulado['IDADE'] >= 18, 1, 0)
        
        # Criar variável de abandono com base em fatores de risco
        # Combinar múltiplos fatores com pesos diferentes
        abandono_prob = (
            0.05 +  # Base rate
            0.07 * df_simulado['TRABALHA'] +
            0.03 * (df_simulado['HORAS_TRABALHO'] / 40) +
            0.05 * df_simulado['REPROVACOES'] +
            0.05 * df_simulado['DISTORCAO_IDADE_SERIE'] -
            0.01 * (df_simulado['DESEMPENHO_MEDIO'] / 10) -
            0.01 * (df_simulado['FREQUENCIA'] / 100) -
            0.01 * (df_simulado['ENGAJAMENTO'] / 10) -
            0.01 * df_simulado['ATIVIDADES_EXTRACURRICULARES'] +
            0.03 * (df_simulado['DISTANCIA_ESCOLA_KM'] / 20) -
            0.02 * (df_simulado['ESCOLARIDADE_MAE'] / 5) -
            0.02 * (df_simulado['RENDA_FAMILIAR'] / 5) +
            np.random.normal(0, 0.05, n_alunos)  # Ruído aleatório
        ).clip(0, 1)
        
        # Determinar abandono com base na probabilidade
        df_simulado['ABANDONO'] = np.random.binomial(1, abandono_prob)
        
        # Salvar dados simulados para uso futuro
        df_simulado.to_csv(arquivo, index=False)
        logger.info(f"Criados dados simulados para {len(df_simulado)} alunos")
        
        return df_simulado


def preprocessar_dados(df, target_var='ABANDONO'):
    """
    Pré-processa os dados para modelagem
    
    Args:
        df (pandas.DataFrame): DataFrame com os dados
        target_var (str): Nome da variável alvo
        
    Returns:
        tuple: (X, y, preprocessor) - Features, target e preprocessador
    """
    logger.info("Iniciando pré-processamento dos dados")
    
    # Verificar se a variável alvo existe
    if target_var not in df.columns:
        logger.error(f"Variável alvo {target_var} não encontrada no DataFrame")
        return None, None, None
    
    # Separar features e target
    y = df[target_var]
    X = df.drop([target_var, 'ID_ALUNO'] if 'ID_ALUNO' in df.columns else target_var, axis=1)
    
    # Identificar tipos de colunas
    numeric_features = X.select_dtypes(include=['int64', 'float64']).columns.tolist()
    categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Preprocessador para pipeline
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ]
    )
    
    logger.info(f"Pré-processamento configurado para {len(numeric_features)} variáveis numéricas e {len(categorical_features)} categóricas")
    
    return X, y, preprocessor


def treinar_modelo(X, y, preprocessor, test_size=0.2, random_state=42):
    """
    Treina e avalia um modelo preditivo de abandono escolar
    
    Args:
        X (pandas.DataFrame): Features
        y (pandas.Series): Variável alvo
        preprocessor (ColumnTransformer): Pré-processador de dados
        test_size (float): Proporção para conjunto de teste
        random_state (int): Seed para reprodutibilidade
        
    Returns:
        dict: Dicionário com modelos treinados e métricas
    """
    logger.info("Iniciando treinamento de modelos")
    
    # Dividir dados em treino e teste
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    
    logger.info(f"Dados divididos: {len(X_train)} amostras de treino, {len(X_test)} amostras de teste")
    
    # Definir modelos a serem treinados
    modelos = {
        'random_forest': Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', RandomForestClassifier(random_state=random_state))
        ]),
        
        'gradient_boosting': Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', GradientBoostingClassifier(random_state=random_state))
        ]),
        
        'logistic_regression': Pipeline([
            ('preprocessor', preprocessor),
            ('classifier', LogisticRegression(random_state=random_state, max_iter=1000))
        ])
    }
    
    # Parâmetros para otimização via grid search
    param_grids = {
        'random_forest': {
            'classifier__n_estimators': [100, 200],
            'classifier__max_depth': [None, 10, 20],
            'classifier__min_samples_split': [2, 5]
        },
        
        'gradient_boosting': {
            'classifier__n_estimators': [100, 200],
            'classifier__learning_rate': [0.01, 0.1],
            'classifier__max_depth': [3, 5]
        },
        
        'logistic_regression': {
            'classifier__C': [0.1, 1.0, 10.0],
            'classifier__penalty': ['l2']
        }
    }
    
    # Resultados
    resultados = {
        'modelos': {},
        'metricas': {},
        'melhores_parametros': {},
        'importancia_features': {}
    }
    
    # Treinar cada modelo com grid search
    for nome_modelo, pipeline in modelos.items():
        logger.info(f"Treinando modelo: {nome_modelo}")
        
        # Definir grid search
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)
        grid_search = GridSearchCV(
            pipeline,
            param_grids[nome_modelo],
            cv=cv,
            scoring='roc_auc',
            n_jobs=-1
        )
        
        # Ajustar grid search
        try:
            grid_search.fit(X_train, y_train)
            
            # Melhor modelo
            melhor_modelo = grid_search.best_estimator_
            resultados['modelos'][nome_modelo] = melhor_modelo
            resultados['melhores_parametros'][nome_modelo] = grid_search.best_params_
            
            # Fazer previsões
            y_pred = melhor_modelo.predict(X_test)
            y_proba = melhor_modelo.predict_proba(X_test)[:, 1]
            
            # Calcular métricas
            metricas = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred),
                'recall': recall_score(y_test, y_pred),
                'f1': f1_score(y_test, y_pred),
                'auc': roc_auc_score(y_test, y_proba),
                'average_precision': average_precision_score(y_test, y_proba),
                'confusion_matrix': confusion_matrix(y_test, y_pred).tolist()
            }
            
            resultados['metricas'][nome_modelo] = metricas
            
            logger.info(f"Modelo {nome_modelo}: AUC = {metricas['auc']:.4f}, F1 = {metricas['f1']:.4f}")
            
            # Extrair importância das features (se aplicável)
            if hasattr(melhor_modelo[-1], 'feature_importances_'):
                # Obter nomes das features após processamento
                if hasattr(melhor_modelo[0], 'get_feature_names_out'):
                    feature_names = melhor_modelo[0].get_feature_names_out()
                else:
                    feature_names = [f"feature_{i}" for i in range(melhor_modelo[-1].feature_importances_.shape[0])]
                
                # Calcular importância
                importancia = pd.DataFrame({
                    'feature': feature_names,
                    'importance': melhor_modelo[-1].feature_importances_
                }).sort_values('importance', ascending=False)
                
                resultados['importancia_features'][nome_modelo] = importancia
            
            # Para regressão logística, usar coeficientes como importância
            elif hasattr(melhor_modelo[-1], 'coef_'):
                if hasattr(melhor_modelo[0], 'get_feature_names_out'):
                    feature_names = melhor_modelo[0].get_feature_names_out()
                else:
                    feature_names = [f"feature_{i}" for i in range(melhor_modelo[-1].coef_.shape[1])]
                
                importancia = pd.DataFrame({
                    'feature': feature_names,
                    'importance': np.abs(melhor_modelo[-1].coef_[0])
                }).sort_values('importance', ascending=False)
                
                resultados['importancia_features'][nome_modelo] = importancia
        
        except Exception as e:
            logger.error(f"Erro ao treinar modelo {nome_modelo}: {str(e)}")
    
    # Adicionar dados de teste aos resultados para visualizações
    resultados['dados_teste'] = {
        'X_test': X_test,
        'y_test': y_test
    }
    
    return resultados


def visualizar_resultados(resultados, output_dir=PLOTS_DIR):
    """
    Gera visualizações dos resultados dos modelos
    
    Args:
        resultados (dict): Dicionário com modelos e métricas
        output_dir (Path): Diretório para salvar visualizações
        
    Returns:
        dict: Caminhos para as visualizações geradas
    """
    logger.info("Gerando visualizações dos resultados")
    
    visualizacoes = {}
    
    try:
        # 1. Gráfico de métricas comparativas
        modelos = list(resultados['metricas'].keys())
        metricas = ['accuracy', 'precision', 'recall', 'f1', 'auc']
        
        metricas_df = pd.DataFrame(index=modelos, columns=metricas)
        for modelo in modelos:
            for metrica in metricas:
                metricas_df.loc[modelo, metrica] = resultados['metricas'][modelo][metrica]
        
        # Gráfico de barras para comparação de métricas
        plt.figure(figsize=(12, 8))
        metricas_df.plot(kind='bar', figsize=(12, 8))
        plt.title('Comparação de Métricas entre Modelos', fontsize=16)
        plt.xlabel('Modelo', fontsize=14)
        plt.ylabel('Valor', fontsize=14)
        plt.grid(True, alpha=0.3, axis='y')
        plt.ylim(0, 1)
        plt.legend(title='Métrica')
        plt.tight_layout()
        
        caminho = output_dir / 'comparacao_metricas.png'
        plt.savefig(caminho, bbox_inches='tight', dpi=300)
        plt.close()
        
        visualizacoes['comparacao_metricas'] = caminho
        
        # 2. Curvas ROC
        plt.figure(figsize=(12, 8))
        
        for modelo_nome, modelo in resultados['modelos'].items():
            if modelo is not None:
                y_test = resultados['dados_teste']['y_test']
                X_test = resultados['dados_teste']['X_test']
                
                y_proba = modelo.predict_proba(X_test)[:, 1]
                fpr, tpr, _ = roc_curve(y_test, y_proba)
                auc = roc_auc_score(y_test, y_proba)
                
                plt.plot(fpr, tpr, lw=2, label=f'{modelo_nome} (AUC = {auc:.3f})')
        
        plt.plot([0, 1], [0, 1], color='gray', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('Taxa de Falsos Positivos', fontsize=14)
        plt.ylabel('Taxa de Verdadeiros Positivos', fontsize=14)
        plt.title('Curva ROC dos Modelos', fontsize=16)
        plt.legend(loc="lower right")
        plt.grid(True, alpha=0.3)
        
        caminho = output_dir / 'curvas_roc.png'
        plt.savefig(caminho, bbox_inches='tight', dpi=300)
        plt.close()
        
        visualizacoes['curvas_roc'] = caminho
        
        # 3. Gráfico de importância das features
        # Usar o melhor modelo (maior AUC)
        melhor_modelo = max(resultados['metricas'].items(), key=lambda x: x[1]['auc'])[0]
        
        if melhor_modelo in resultados['importancia_features']:
            importancia = resultados['importancia_features'][melhor_modelo]
            
            # Plotar top 15 features
            n_features = min(15, len(importancia))
            top_features = importancia.head(n_features)
            
            plt.figure(figsize=(12, 10))
            bars = plt.barh(
                top_features['feature'], 
                top_features['importance'],
                color='#1e88e5'
            )
            
            plt.title(f'Importância das Features - {melhor_modelo}', fontsize=16)
            plt.xlabel('Importância', fontsize=14)
            plt.ylabel('Feature', fontsize=14)
            plt.grid(True, alpha=0.3, axis='x')
            plt.gca().invert_yaxis()  # Inverter para visualizar em ordem decrescente
            
            caminho = output_dir / 'importancia_features.png'
            plt.savefig(caminho, bbox_inches='tight', dpi=300)
            plt.close()
            
            visualizacoes['importancia_features'] = caminho
            
            # 4. Gráfico de confusão para o melhor modelo
            cm = resultados['metricas'][melhor_modelo]['confusion_matrix']
            
            plt.figure(figsize=(10, 8))
            sns.heatmap(
                cm, 
                annot=True, 
                fmt='d', 
                cmap='Blues',
                xticklabels=['Não Abandono', 'Abandono'],
                yticklabels=['Não Abandono', 'Abandono']
            )
            plt.title(f'Matriz de Confusão - {melhor_modelo}', fontsize=16)
            plt.xlabel('Predição', fontsize=14)
            plt.ylabel('Valor Real', fontsize=14)
            
            caminho = output_dir / 'matriz_confusao.png'
            plt.savefig(caminho, bbox_inches='tight', dpi=300)
            plt.close()
            
            visualizacoes['matriz_confusao'] = caminho
    
    except Exception as e:
        logger.error(f"Erro ao gerar visualizações: {str(e)}")
    
    logger.info(f"Geradas {len(visualizacoes)} visualizações")
    return visualizacoes


def salvar_modelos(resultados, output_dir=MODELS_DIR):
    """
    Salva os modelos treinados e metadados
    
    Args:
        resultados (dict): Dicionário com modelos e métricas
        output_dir (Path): Diretório para salvar os modelos
        
    Returns:
        dict: Caminhos para os modelos salvos
    """
    logger.info("Salvando modelos treinados")
    
    modelos_salvos = {}
    
    # Determinar o melhor modelo
    try:
        melhor_modelo_nome = max(resultados['metricas'].items(), key=lambda x: x[1]['auc'])[0]
        logger.info(f"Melhor modelo: {melhor_modelo_nome}")
        
        # Salvar cada modelo
        for nome, modelo in resultados['modelos'].items():
            modelo_path = output_dir / f"modelo_{nome}.joblib"
            joblib.dump(modelo, modelo_path)
            modelos_salvos[nome] = modelo_path
            logger.info(f"Modelo {nome} salvo em {modelo_path}")
        
        # Salvar metadados do melhor modelo
        metadados = {
            'nome': melhor_modelo_nome,
            'metricas': resultados['metricas'][melhor_modelo_nome],
            'parametros': resultados['melhores_parametros'][melhor_modelo_nome],
            'data_treinamento': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Se disponível, incluir importância das features
        if melhor_modelo_nome in resultados['importancia_features']:
            importancia_df = resultados['importancia_features'][melhor_modelo_nome]
            importancia_path = output_dir / "importancia_features.csv"
            importancia_df.to_csv(importancia_path, index=False)
            metadados['importancia_features_path'] = importancia_path
        
        # Salvar metadados em formato JSON
        import json
        with open(output_dir / "metadados_modelo.json", 'w') as f:
            # Converter alguns tipos não serializáveis
            json_safe = {k: (v if k != 'confusion_matrix' else v) for k, v in metadados['metricas'].items()}
            metadados['metricas'] = json_safe
            
            # Converter caminhos para strings
            if 'importancia_features_path' in metadados:
                metadados['importancia_features_path'] = str(metadados['importancia_features_path'])
            
            json.dump(metadados, f, indent=4)
        
        logger.info(f"Metadados salvos em {output_dir / 'metadados_modelo.json'}")
        
        # Retornar informações
        modelos_salvos['metadados'] = output_dir / "metadados_modelo.json"
        modelos_salvos['melhor_modelo'] = {
            'nome': melhor_modelo_nome,
            'caminho': modelos_salvos[melhor_modelo_nome]
        }
    
    except Exception as e:
        logger.error(f"Erro ao salvar modelos: {str(e)}")
    
    return modelos_salvos


def treinar_modelo_abandono(ano_referencia, target_var='ABANDONO'):
    """
    Função principal para treinar modelo preditivo de abandono escolar
    
    Args:
        ano_referencia (int): Ano de referência dos dados
        target_var (str): Nome da variável alvo
        
    Returns:
        dict: Resultados do treinamento e caminhos dos artefatos gerados
    """
    logger.info(f"Iniciando treinamento de modelo para predição de {target_var}, ano {ano_referencia}")
    
    # 1. Carregar dados
    df = carregar_dados_alunos(ano_referencia)
    if df is None:
        logger.error("Não foi possível carregar os dados de alunos")
        return None
    
    # 2. Pré-processar dados
    X, y, preprocessor = preprocessar_dados(df, target_var=target_var)
    if X is None:
        logger.error("Falha no pré-processamento dos dados")
        return None
    
    # 3. Treinar modelos
    resultados = treinar_modelo(X, y, preprocessor)
    if not resultados or 'modelos' not in resultados or not resultados['modelos']:
        logger.error("Falha no treinamento dos modelos")
        return None
    
    # 4. Gerar visualizações
    visualizacoes = visualizar_resultados(resultados)
    
    # 5. Salvar modelos
    modelos_salvos = salvar_modelos(resultados)
    
    # 6. Consolidar resultados
    resultado_final = {
        'status': 'sucesso',
        'modelos': modelos_salvos,
        'visualizacoes': visualizacoes,
        'metricas': {nome: metrics for nome, metrics in resultados['metricas'].items()},
        'feature_importances': {
            nome: importancia.to_dict('records') 
            for nome, importancia in resultados['importancia_features'].items()
        } if 'importancia_features' in resultados else {}
    }
    
    # Salvar resultado final
    try:
        import json
        with open(RESULTS_DIR / f"resultado_modelagem_{ano_referencia}.json", 'w') as f:
            # Converter alguns tipos não serializáveis
            serializable = {
                'status': resultado_final['status'],
                'modelos': {k: str(v) for k, v in resultado_final['modelos'].items()},
                'visualizacoes': {k: str(v) for k, v in resultado_final['visualizacoes'].items()},
                'metricas': resultado_final['metricas'],
                'feature_importances': resultado_final['feature_importances']
            }
            
            # Converter arrays em listas para serialização JSON
            for modelo in serializable['metricas']:
                if 'confusion_matrix' in serializable['metricas'][modelo]:
                    cm = serializable['metricas'][modelo]['confusion_matrix']
                    if not isinstance(cm, list):
                        serializable['metricas'][modelo]['confusion_matrix'] = cm.tolist()
            
            json.dump(serializable, f, indent=4)
    except Exception as e:
        logger.error(f"Erro ao salvar resultado final: {str(e)}")
    
    logger.info("Treinamento de modelo concluído com sucesso")
    return resultado_final


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Treinamento de modelo preditivo para abandono escolar')
    parser.add_argument('--ano', type=int, required=True, help='Ano de referência dos dados')
    parser.add_argument('--target', type=str, default='ABANDONO', help='Variável alvo para modelagem')
    
    args = parser.parse_args()
    
    resultado = treinar_modelo_abandono(args.ano, target_var=args.target)
    
    if resultado and resultado['status'] == 'sucesso':
        melhor_modelo = max(resultado['metricas'].items(), key=lambda x: x[1]['auc'])[0]
        metrics = resultado['metricas'][melhor_modelo]
        
        print("\nResultados do treinamento:")
        print(f"Melhor modelo: {melhor_modelo}")
        print(f"AUC: {metrics['auc']:.4f}")
        print(f"Acurácia: {metrics['accuracy']:.4f}")
        print(f"Precisão: {metrics['precision']:.4f}")
        print(f"Recall: {metrics['recall']:.4f}")
        print(f"F1-Score: {metrics['f1']:.4f}")
    else:
        print("Falha no treinamento do modelo")
