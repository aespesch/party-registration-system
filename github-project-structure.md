# Estrutura do Projeto: party-registration-system

```
party-registration-system/
│
├── app.py                    # Arquivo principal da aplicação
├── requirements.txt          # Dependências Python necessárias
├── .gitignore               # Arquivos que o Git deve ignorar
├── README.md                # Documentação do projeto
├── config.py                # Configurações (preços, chave PIX, etc.)
├── data/                    # Pasta para dados
│   └── participants.csv     # Lista de participantes
└── utils/                   # Funções auxiliares
    ├── __init__.py         # Torna a pasta um módulo Python
    ├── pix_generator.py    # Geração de QR Code PIX
    └── email_sender.py     # Envio de e-mails (opcional)
```

## Passo 1: Criar o Repositório no GitHub

1. Acesse github.com e faça login
2. Clique no botão verde "New" ou no "+" no canto superior direito
3. Nome do repositório: `party-registration-system`
4. Descrição: "Sistema de confirmação de presença e pagamento para festa"
5. Marque como "Public" (necessário para o plano gratuito do Streamlit Cloud)
6. NÃO inicialize com README (vamos criar nosso próprio)
7. Clique em "Create repository"

## Passo 2: Configurar o Projeto Localmente

No seu computador, crie uma pasta para o projeto e abra o terminal nela:

```bash
# Criar a pasta do projeto
mkdir party-registration-system
cd party-registration-system

# Inicializar o Git
git init

# Conectar ao repositório remoto (substitua SEU_USUARIO pelo seu username do GitHub)
git remote add origin https://github.com/SEU_USUARIO/party-registration-system.git
```

## Passo 3: Criar os Arquivos do Projeto

Agora vamos criar cada arquivo necessário. Vou explicar a função de cada um: