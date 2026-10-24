Projeto Monitor B3 - separação front/back

Como rodar (Windows PowerShell):

1. Criar e ativar um venv (opcional):

python -m venv .venv; .\.venv\Scripts\Activate.ps1

2. Instalar dependências:

pip install -r requirements.txt

3. Rodar servidor:

python server.py

4. Abrir no navegador:

http://127.0.0.1:5000/

Observações:
- O servidor cria `dados.db` automaticamente.
- Para simplicidade o login retorna um objeto de usuário sem tokens; o frontend armazena o usuário em memória.
- Produção: adicione autenticação real, HTTPS e validações.
