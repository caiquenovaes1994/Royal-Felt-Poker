@echo off
chcp 65001 >nul
title Royal Felt - Texas Hold'em Poker

echo ========================================================
echo         ♠  ROYAL FELT - TEXAS HOLD'EM POKER  ♠
echo ========================================================
echo.

:: 1. Verificar se Python esta instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Python nao foi encontrado no sistema!
    echo.
    set /p "INSTALAR_PYTHON=Deseja instalar o Python automaticamente via winget? (S/N): "
    if /i "%INSTALAR_PYTHON%"=="S" (
        echo.
        echo [*] Instalando Python via winget...
        winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
        if %errorlevel% equ 0 (
            echo.
            echo [*] Instalacao do Python finalizada com sucesso!
            echo [*] Para carregar o Python no PATH, este inicializador precisa ser reiniciado.
            echo.
            set /p "REINICIAR=Deseja reiniciar o inicializador automaticamente agora? (S/N): "
            if /i "%REINICIAR%"=="S" (
                echo.
                echo [*] Reiniciando o inicializador em uma nova janela...
                timeout /t 1 /nobreak >nul
                start "" "%~f0"
                exit
            ) else (
                echo.
                echo [*] Quando desejar jogar, feche esta janela e execute o iniciar_jogo.bat manualmente.
                echo Pressione qualquer tecla para sair...
                pause >nul
                exit /b 0
            )
        ) else (
            echo.
            echo [ERRO] Nao foi possivel concluir a instalacao via winget.
            echo Por favor, instale o Python 3.10+ e adicione ao PATH.
            echo Pressione qualquer tecla para sair...
            pause >nul
            exit /b 1
        )
    ) else (
        echo.
        echo Por favor, instale o Python 3.10+ e adicione ao PATH.
        echo Pressione qualquer tecla para sair...
        pause >nul
        exit /b 1
    )
)

:: 2. Instalar dependencias se necessario
echo [*] Verificando dependencias...
pip install -r requirements.txt --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo [AVISO] Houve um aviso na verificacao de dependencias, prosseguindo...
)

echo [*] Iniciando servidor do jogo...
echo [*] Acesse no seu navegador: http://127.0.0.1:8000/
echo.

:: 3. Abrir navegador automaticamente apos 2 segundos em segundo plano
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:8000/"

:: 4. Executar servidor Python
python server.py

if %errorlevel% neq 0 (
    echo.
    echo [ERRO] O servidor encerrou com erro.
    pause
)
