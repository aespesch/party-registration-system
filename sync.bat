@echo off
:: Sincronizador para o repositório GitHub
:: Uso: sync.bat [mensagem_commit]

:: Passo 1: Acessar o diretório e ativar o ambiente virtual
d:
cd D:\USER\Toni\ITA90\Python\streamlit\party-registration-system
call .\streamlit\Scripts\activate.bat

:: Passo 2: Baixar atualizações do repositório
echo Baixando alterações do GitHub...
git pull origin main

:: Passo 3: Preparar e enviar alterações locais
git add --all

:: Verificar se há mudanças para commit
git diff-index --quiet HEAD
if %errorlevel% equ 0 (
    echo Nenhuma alteração local para enviar.
) else (
    if "%1"=="" (
        set /p commit_msg="Digite a mensagem do commit: "
    ) else (
        set commit_msg=%*
    )
    git commit -m "%commit_msg%"
    git push origin main
    echo Alterações enviadas para o GitHub.
)

echo -------------------------------
echo local
git log --oneline -5
echo -------------------------------
echo remote
git log --oneline origin/main -5

echo Sincronização completa!
pause