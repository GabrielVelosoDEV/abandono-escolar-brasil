# Guia de Contribuição

Obrigado pelo interesse em contribuir para o projeto "Análise Multidimensional do Abandono Escolar no Ensino Médio Brasileiro"! Este documento fornece diretrizes para contribuir com o projeto.

## Índice

1. [Código de Conduta](#código-de-conduta)
2. [Como Contribuir](#como-contribuir)
3. [Reportando Bugs](#reportando-bugs)
4. [Sugestões de Melhorias](#sugestões-de-melhorias)
5. [Diretrizes de Código](#diretrizes-de-código)
6. [Processo de Pull Request](#processo-de-pull-request)
7. [Estrutura do Projeto](#estrutura-do-projeto)
8. [Licença](#licença)

## Código de Conduta

Este projeto e todos os participantes estão sujeitos a um Código de Conduta. Ao participar, espera-se que você mantenha este código. Por favor, reporte comportamentos inaceitáveis para o mantenedor do projeto.

Comprometa-se a:
- Usar linguagem acolhedora e inclusiva
- Respeitar diferentes pontos de vista e experiências
- Aceitar críticas construtivas
- Focar no que é melhor para a comunidade
- Mostrar empatia com outros membros da comunidade

## Como Contribuir

Existem várias maneiras de contribuir para o projeto:

1. **Atualizações de Dados**: Contribua com novas fontes de dados ou atualizações das existentes
2. **Melhorias em Análises**: Sugira novas abordagens analíticas ou refine as existentes
3. **Otimização de Código**: Melhore o desempenho e a legibilidade do código existente
4. **Documentação**: Melhore a documentação técnica ou conceitual
5. **Visualizações**: Desenvolva novas visualizações ou aprimore as existentes
6. **Interface do Usuário**: Melhore a usabilidade do dashboard e outras interfaces
7. **Testes**: Adicione ou melhore testes

## Reportando Bugs

Ao reportar bugs, por favor inclua:

1. Descrição clara e concisa do problema
2. Passos detalhados para reproduzir o problema
3. Comportamento esperado e comportamento observado
4. Capturas de tela, se aplicável
5. Ambiente (sistema operacional, versão do Python, etc.)

Use o modelo de issue para bugs.

## Sugestões de Melhorias

Para sugerir melhorias:

1. Descreva claramente a melhoria proposta
2. Explique como ela beneficia o projeto
3. Forneça exemplos, se possível
4. Indique se você está disposto a implementar a melhoria

Use o modelo de issue para sugestões de recursos.

## Diretrizes de Código

### Python

- Siga a PEP 8 para estilo de código Python
- Documente funções e classes usando docstrings (formato NumPy ou Google)
- Utilize tipos de anotações quando apropriado
- Mantenha o código modular e reutilizável
- Escreva testes para novas funcionalidades

### Notebooks Jupyter

- Mantenha células de código concisas e focadas
- Inclua markdown explicativo entre células de código
- Evite resultados muito longos em outputs
- Use nomes de variáveis significativos

### Visualizações

- Mantenha consistência de cores e estilos
- Priorize clareza e compreensibilidade
- Inclua títulos, legendas e anotações apropriadas
- Considere acessibilidade (como escolhas de cores para daltônicos)

## Processo de Pull Request

1. Faça um fork do repositório
2. Crie um branch para sua feature (`git checkout -b feature/nome-da-feature`)
3. Comite suas mudanças (`git commit -m 'Adicionar: breve descrição'`)
4. Faça push para o branch (`git push origin feature/nome-da-feature`)
5. Abra um Pull Request

### Diretrizes para Pull Requests

- Forneça uma descrição clara do que a mudança faz
- Inclua qualquer issue relacionada usando referências (#numero-da-issue)
- Certifique-se de que o código passa em todos os testes
- Atualize a documentação relevante
- Espere feedback e esteja disposto a fazer ajustes

## Estrutura do Projeto

Familiarize-se com a estrutura do projeto antes de contribuir:

```
abandono-escolar-brasil/
│
├── README.md                           # Visão geral do projeto
│
├── docs/                               # Documentação detalhada
│   ├── problema.md                     # Dissertação sobre o problema
│   ├── fontes_dados.md                 # Documentação das fontes de dados
│   ├── metodologia_analise.md          # Detalhamento da metodologia
│   ├── resultados_insights.md          # Relatório de insights
│   └── limitacoes_recomendacoes.md     # Limitações e recomendações
│
├── notebooks/                          # Notebooks de análise
│   ├── 1_coleta_dados.ipynb            # Notebook de coleta
│   ├── 2_integracao_fontes.ipynb       # Notebook de integração
│   ├── 3_analise_exploratoria.ipynb    # Notebook de análise exploratória
│   ├── 4_modelagem_segmentacao.ipynb   # Notebook de modelagem
│   └── 5_visualizacao_dados.ipynb      # Notebook de visualização
│
├── scripts/                            # Scripts Python
│   ├── coleta/                         # Scripts de coleta
│   ├── processamento/                  # Scripts de processamento
│   ├── analise/                        # Scripts de análise
│   └── visualizacao/                   # Scripts de visualização
│
├── data/                               # Dados
│   ├── raw/                            # Dados brutos (amostras)
│   ├── processed/                      # Dados processados
│   ├── results/                        # Resultados das análises
│   └── looker_data/                    # Dados para o Looker
│
├── visualizacoes/                      # Visualizações estáticas
│   ├── mapas/                          # Mapas temáticos
│   ├── graficos/                       # Gráficos estatísticos
│   └── dashboard/                      # Capturas do dashboard
│
├── dashboard/                          # Recursos do dashboard
│   ├── abandono_escolar_dashboard.pdf  # Dashboard em PDF
│   ├── instrucoes_acesso.md            # Instruções para acessar o dashboard
│   └── link_dashboard.md               # Link para o dashboard
│
├── apresentacao/                       # Material de apresentação
│   ├── slides.pdf                      # Slides de apresentação
│   └── infografico_executivo.pdf       # Infográfico de resultados
│
├── .gitignore                          # Configuração de arquivos ignorados
├── CONTRIBUTING.md                     # Este guia de contribuição
└── LICENSE                             # Licença MIT
```

## Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes. Ao contribuir, você concorda em licenciar suas contribuições sob a mesma licença.

---

Agradecemos sua contribuição para melhorar a compreensão e o enfrentamento do abandono escolar no Brasil. Juntos, podemos desenvolver ferramentas e conhecimentos que ajudem a aprimorar as políticas educacionais e reduzir desigualdades.
