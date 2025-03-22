# Arquivos do sistema
.DS_Store
Thumbs.db

# Ambientes Python
__pycache__/
*.py[cod]
*$py.class
.ipynb_checkpoints/
venv/
env/
.env
.venv
.python-version

# Arquivos de distribuição/pacotes
dist/
build/
*.egg-info/

# Arquivos grandes (adicione conforme necessário)
*.csv
*.xlsx
*.xls
*.zip
*.rar

# Exceções (dados de amostra que queremos manter)
!data/raw/*_amostra.csv
!data/raw/geo/*.geojson
!data/looker_data/*.csv

# Logs e caches
*.log
.cache/
logs/
*.dump

# Arquivos temporários
temp/
tmp/
.temp/
.tmp/

# Arquivos de configuração específicos do IDE/Editor
.idea/
.vscode/
*.swp
*.swo
.project
.pydevproject
.settings/

# Arquivos de ambiente e segredos
*.env
.secrets
secrets.json

# Arquivos de saída específicos
output/
exports/
results/*.pkl

# Diretórios virtuais de ambiente
venv/
env/
ENV/
