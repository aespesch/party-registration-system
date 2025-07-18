@echo off
REM ===============================================================
REM Sincronizador Robusto para o repositorio GitHub
REM Uso: sync.bat [mensagem_commit]
REM 
REM Melhorias implementadas:
REM - Verificacao de erros em cada etapa
REM - Validacao de conectividade com GitHub
REM - Verificacao de branch atual
REM - Timestamp automatico em commits
REM - Confirmacao pos-push
REM - Melhor tratamento de conflitos
REM ===============================================================

setlocal

REM Configuracoes
set REPO_DIR=D:\USER\Toni\ITA90\Python\streamlit\party-registration-system
set VENV_PATH=.\streamlit\Scripts\activate.bat
set TARGET_BRANCH=main

echo =============================================
echo    Sincronizador GitHub - Versao 2.0
echo =============================================
echo.

REM Passo 1: Navegar para o diretorio e ativar ambiente virtual
echo [1/8] Acessando diretorio do projeto...
d:
cd /d "%REPO_DIR%" 2>nul
if %errorlevel% neq 0 (
    echo ERRO: Nao foi possivel acessar o diretorio: %REPO_DIR%
    pause
    exit /b 1
)

echo [2/8] Ativando ambiente virtual...
if exist "%VENV_PATH%" (
    call "%VENV_PATH%"
    echo Ambiente virtual ativado com sucesso.
) else (
    echo AVISO: Arquivo do ambiente virtual nao encontrado: %VENV_PATH%
    echo Continuando sem ambiente virtual...
)

REM Passo 2: Verificar se estamos em um repositorio Git valido
echo [3/8] Verificando repositorio Git...
git status >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Este diretorio nao e um repositorio Git valido.
    pause
    exit /b 1
)

REM Verificar branch atual
for /f "tokens=*" %%i in ('git branch --show-current 2^>nul') do set CURRENT_BRANCH=%%i
if "%CURRENT_BRANCH%"=="" (
    echo AVISO: Nao foi possivel determinar a branch atual.
    set CURRENT_BRANCH=main
)
echo Branch atual: %CURRENT_BRANCH%

if "%CURRENT_BRANCH%" neq "%TARGET_BRANCH%" (
    echo AVISO: Voce esta na branch '%CURRENT_BRANCH%' mas o target e '%TARGET_BRANCH%'
    set /p "continue=Deseja continuar? (s/N): "
    if /i "%continue%" neq "s" (
        echo Operacao cancelada.
        pause
        exit /b 0
    )
)

REM Passo 3: Verificar conectividade com GitHub
echo [4/8] Testando conectividade com GitHub...
git ls-remote origin HEAD >nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Nao foi possivel conectar ao repositorio remoto.
    echo Verifique sua conexao com a internet e credenciais do Git.
    pause
    exit /b 1
)
echo Conectividade com GitHub OK.

REM Passo 4: Baixar atualizacoes do repositorio
echo [5/8] Baixando alteracoes do GitHub...
git fetch origin
if %errorlevel% neq 0 (
    echo ERRO: Falha ao fazer fetch do repositorio remoto.
    pause
    exit /b 1
)

git pull origin %CURRENT_BRANCH%
if %errorlevel% neq 0 (
    echo ERRO: Falha no git pull. Pode haver conflitos que precisam ser resolvidos manualmente.
    echo Execute 'git status' para ver os detalhes.
    pause
    exit /b 1
)
echo Pull realizado com sucesso.

REM Passo 5: Verificar e preparar alteracoes locais
echo [6/8] Verificando alteracoes locais...

echo.
echo Status atual do repositorio:
git status --porcelain
echo.

REM Adicionar todas as alteracoes
git add --all
if %errorlevel% neq 0 (
    echo ERRO: Falha ao adicionar arquivos ao staging.
    pause
    exit /b 1
)

REM Verificar se ha mudancas para commit
git diff-index --quiet HEAD
if %errorlevel% equ 0 (
    echo Nenhuma alteracao local para enviar.
    goto :show_logs
) else (
    echo Alteracoes detectadas. Preparando commit...
    
    REM Determinar mensagem do commit
    if "%~1"=="" (
        REM Gerar timestamp para mensagem automatica
        for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set DATE_PART=%%c-%%b-%%a
        for /f "tokens=1-2 delims=: " %%a in ('time /t') do set TIME_PART=%%a:%%b
        set DEFAULT_MSG=Update em %DATE_PART% as %TIME_PART%
        
        echo.
        echo Mensagem padrao: %DEFAULT_MSG%
        set /p "commit_msg=Digite a mensagem do commit (Enter para usar padrao): "
        if "%commit_msg%"=="" set commit_msg=%DEFAULT_MSG%
    ) else (
        set commit_msg=%*
    )
    
    REM Realizar commit
    echo [7/8] Fazendo commit: "%commit_msg%"
    git commit -m "%commit_msg%"
    if %errorlevel% neq 0 (
        echo ERRO: Falha ao fazer commit.
        pause
        exit /b 1
    )
    
    REM Realizar push
    echo [8/8] Enviando alteracoes para o GitHub...
    git push origin %CURRENT_BRANCH%
    if %errorlevel% neq 0 (
        echo ERRO: Falha ao fazer push. Verifique suas credenciais e conectividade.
        pause
        exit /b 1
    )
    
    echo Push realizado com sucesso!
    
    REM Verificar se o push foi realmente efetivado
    echo.
    echo Verificando se o push foi efetivado...
    timeout /t 3 /nobreak >nul
    git fetch origin
    
    REM Obter hash do ultimo commit local
    for /f "tokens=*" %%i in ('git log --format^=%%H -n 1') do set LOCAL_COMMIT=%%i
    
    REM Obter hash do ultimo commit remoto
    for /f "tokens=*" %%i in ('git log --format^=%%H -n 1 origin/%CURRENT_BRANCH%') do set REMOTE_COMMIT=%%i
    
    if "%LOCAL_COMMIT%"=="%REMOTE_COMMIT%" (
        echo Confirmado: O commit foi sincronizado com sucesso no GitHub.
    ) else (
        echo ATENCAO: Ha uma discrepancia entre os commits locais e remotos.
        echo Pode haver um delay na sincronizacao ou um problema de conectividade.
        echo Local:  %LOCAL_COMMIT%
        echo Remoto: %REMOTE_COMMIT%
    )
)

:show_logs
REM Exibir logs comparativos
echo.
echo =============== RESUMO DOS COMMITS ===============
echo.
echo Ultimos 5 commits LOCAIS:
git log --oneline -5
echo.
echo Ultimos 5 commits REMOTOS:
git log --oneline origin/%CURRENT_BRANCH% -5
echo.
echo ==================================================

REM Sugestao para verificacao no browser
echo.
echo DICA: Para confirmar no GitHub web:
echo    1. Abra: https://github.com/[seu-usuario]/party-registration-system
echo    2. Pressione Ctrl+F5 para atualizar completamente a pagina
echo    3. Verifique se o ultimo commit aparece na timeline
echo.

echo Sincronizacao completa!
echo Pressione qualquer tecla para continuar...
pause >nul