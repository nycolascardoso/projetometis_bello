# Projeto Metis ? Extração de Imóveis e IPTU (Caçador)

## Pré-requisitos
- Python 3.11/3.12 com venv
- Microsoft Edge instalado
- Selenium (usa Selenium Manager por padr?o; sem path do driver)
- EasyOCR (baixa modelos no 1? uso) e Tesseract (para fluxo IPTU)

Instalação rápida:

```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -r requirements.txt
# opcional (carrega modelos PyTorch CPU da CDN oficial):
# pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
# Tesseract (Windows): winget install -e --id UB-Mannheim.TesseractOCR
```

## Ordem de execução
1. Imóveis (preenche URLs e códigos)
```
python -m extracao_imoveis.main
```
2. IPTU (usa a coluna K=Sim da aba "Link de Imóveis")
```
python -m extracao_iptu.main
```

## Planilha esperada (Banco_de_Imoveis.xlsx)
- Aba "Consultar": A=CNPJ/CPF, B=Status, C=última Atualiza??o, D=Tipo de Doc., E=Processar (Sim/Não)
- Aba "Link de Imóveis": alimentada pelo Passo 1; coluna K = "Extrair IPTU?" (Sim/Não)
- Aba "Banco de Dados": recebe os carnês IPTU no Passo 2

## Observações
- Na primeira execução o EasyOCR baixa modelos; a importação pode demorar.
- O código agora tenta abrir o Edge via Selenium Manager; se falhar, usa DRIVER_PATH como fallback.
- Encerramento do navegador protegido caso o driver não tenha sido inicializado.
