# Projeto Metis ? Extra??o de Im?veis e IPTU (Ca?ador)

## Pr?-requisitos
- Python 3.11/3.12 com venv
- Microsoft Edge instalado
- Selenium (usa Selenium Manager por padr?o; sem path do driver)
- EasyOCR (baixa modelos no 1? uso) e Tesseract (para fluxo IPTU)

Instala??o r?pida:

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
# opcional (carrega modelos PyTorch CPU da CDN oficial):
# pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
# Tesseract (Windows): winget install -e --id UB-Mannheim.TesseractOCR
```

## Ordem de execu??o
1. Im?veis (preenche URLs e c?digos)
```
python -m extracao_imoveis.main
```
2. IPTU (usa a coluna K=Sim da aba "Link de Im?veis")
```
python -m extracao_iptu.main
```

## Planilha esperada (Banco_de_Imoveis.xlsx)
- Aba "Consultar": A=CNPJ/CPF, B=Status, C=?ltima Atualiza??o, D=Tipo de Doc., E=Processar (Sim/N?o)
- Aba "Link de Im?veis": alimentada pelo Passo 1; coluna K = "Extrair IPTU?" (Sim/N?o)
- Aba "Banco de Dados": recebe os carn?s IPTU no Passo 2

## Observa??es
- Na primeira execu??o o EasyOCR baixa modelos; a importa??o pode demorar.
- O c?digo agora tenta abrir o Edge via Selenium Manager; se falhar, usa DRIVER_PATH como fallback.
- Encerramento do navegador protegido caso o driver n?o tenha sido inicializado.
