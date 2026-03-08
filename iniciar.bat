@echo off
cd /d "%~dp0"

echo Metis - Extracao de Dados Imobiliarios
echo ========================================
echo.

python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ERRO: Python nao encontrado no PATH.
    echo Instale em: https://www.python.org/downloads/
    echo Marque a opcao "Add Python to PATH" na instalacao.
    echo.
    pause
    exit /b 1
)

echo Verificando dependencias...
python -c "import streamlit" > nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando dependencias pela primeira vez...
    echo Isso pode demorar alguns minutos.
    echo.
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo ERRO ao instalar dependencias.
        pause
        exit /b 1
    )
    echo.
    echo Dependencias instaladas com sucesso!
    echo.
)

echo Iniciando servidor...
echo Acesse: http://localhost:8501
echo Para encerrar: feche esta janela ou pressione Ctrl+C
echo.

start "" /b cmd /c "timeout /t 4 > nul && start http://localhost:8501"

python -m streamlit run app.py --server.port 8501 --server.headless true --browser.gatherUsageStats false

echo.
echo Sistema encerrado.
pause
