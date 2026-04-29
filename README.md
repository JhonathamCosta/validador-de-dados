# Data Validation Kernel

Este projeto é uma base extensível para criar validadores de dados específicos por domínio.

O repositório público contém o kernel, adapters, contratos, UI inicial e um domínio de exemplo. As regras reais devem preferencialmente ficar fora deste repositório, em pacotes de domínio carregados pelo kernel via contrato e manifest `domain.json`.

## Objetivo

Validar bases operacionais usando regras pequenas, plugáveis e auditáveis.

O foco inicial é permitir:

- carregar uma ou mais bases em um `bundle` canônico;
- executar regras por domínio;
- devolver resultados padronizados;
- manter evidências para análise e correção;
- evoluir para histórico, auditoria e automação.

## Princípio de arquitetura

Regra de negócio não deve depender de UI.

A UI pode ser Streamlit, CLI, web app ou outro front-end. O núcleo de validação deve continuar funcionando sem conhecer a interface.

```text
adapters/  -> leitura de dados externos
domains/   -> regras de negócio por domínio
core/      -> contratos, execução e consolidação
storage/   -> histórico e evidências
ui/        -> cascas de interação
```

## Estrutura atual

```text
core/
  application.py
  contracts/
    input_adapter.py
    rule.py
  engine/
    runner.py
    rule_executor.py
  models/
    rule_result.py
    validation_report.py
  services/
    build_result.py

adapters/
  inputs/
    base.py
    csv.py
    json.py

domains/
  exemplo/
    examples/
      dados_exemplo.json
      referencias_exemplo.json
    registry.py
    rules/
      missing_code.py

ui/
  streamlit_app/
    app.py

docs/
  README.md
  USAGE.md
```

## Instalação e configuração

### Pré-requisitos

- Python 3.10+;
- `pip` disponível no ambiente.

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd validador-de-dados
```

Se você já está com o repositório aberto localmente, pode seguir para o próximo passo.

### 2. Criar e ativar ambiente virtual

No Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

No Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependências

```bash
pip install -r requirements.txt
```

Dependências atuais do projeto:

- `streamlit`;
- `XlsxWriter`;
- `openpyxl`;
- `pytest`.

### 4. Executar a interface

```bash
streamlit run ui/streamlit_app/app.py
```

Depois disso, abra a URL exibida pelo Streamlit no navegador.

Para personalizar o nome exibido no frontend, edite `ui/streamlit_app/metadata.json`.
Um exemplo pronto foi adicionado em `ui/streamlit_app/metadata.example.json`.

### 5. Estrutura mínima para desenvolvimento

Ao subir o projeto localmente:

- as regras de negócio ficam em `domains/`;
- os adapters de entrada ficam em `adapters/inputs/`;
- a UI atual fica em `ui/streamlit_app/`;
- exemplos de arquivos do domínio versionado ficam em `domains/exemplo/examples/`.

### 6. Configuração de novos domínios

Para adaptar o projeto ao seu caso de uso, prefira criar o domínio fora do repositório do kernel:

```text
meu-dominio-real/
  domain.json
  __init__.py
  registry.py
  rules/
    __init__.py
    minha_regra.py
```

Depois aponte o kernel para esse domínio:

```env
VALIDATOR_DOMAIN_PATHS=C:\caminho\para\meu-dominio-real
VALIDATOR_ENABLE_BUILTIN_DOMAINS=false
```

Ou, se preferir definir direto no PowerShell:

```powershell
$env:VALIDATOR_DOMAIN_PATHS="C:\caminho\para\meu-dominio-real"
streamlit run ui/streamlit_app/app.py
```

O arquivo `.env.example` traz a chave esperada para desenvolvimento local.

O domínio `exemplo` interno fica habilitado por padrão para facilitar testes apos o clone. Use `VALIDATOR_ENABLE_BUILTIN_DOMAINS=false` quando quiser listar apenas domínios externos.

Domínios embutidos ainda podem existir em `domains/`, mas o caminho recomendado para regras reais é manter a personalização separada do kernel.

Mais detalhes de uso e extensão estão em `docs/USAGE.md`.

## Entry point recomendado

Use `core.application.run_validation_job(...)` como ponto único para front-end, CLI ou automação.

```python
from adapters.inputs.csv import CsvInputAdapter
from core.application import run_validation_job

report = run_validation_job(
    domain_id="exemplo",
    source={
        "dados": "dados.csv",
        "referencias": "referencias.csv",
    },
    adapter={
        "dados": CsvInputAdapter(bundle_key="dados"),
        "referencias": CsvInputAdapter(bundle_key="referencias"),
    },
    context={"user": "admin"},
)
```

Esse entry point evita que a interface conheça detalhes de `registry`, `runner` ou `rule_executor`.

## Contratos centrais

### Regra

Cada regra deve expor:

- `name`;
- `rule_id`, quando existir identificador estável;
- `run(bundle, context)`;
- retorno em `dict` com, no mínimo, `count`.

Campos comuns de retorno:

```python
{
    "count": 0,
    "details": [],
    "message": "Nenhuma inconsistência encontrada.",
    "severity": "LOW",
    "status": "PASS",
}
```

### RuleResult

Modelo canônico em `core/models/rule_result.py`:

- `rule_id`;
- `rule_name`;
- `status`: `PASS | FAIL | WARNING | ERROR`;
- `severity`: `LOW | MEDIUM | HIGH | CRITICAL`;
- `count`;
- `message`;
- `details`;
- `duration_ms`.

### ValidationReport

Modelo canônico em `core/models/validation_report.py`:

- `template_id`;
- `total_rules`;
- `total_pass`;
- `total_fail`;
- `total_warning`;
- `total_error`;
- `results`;
- `duration_ms`.

## Fluxo de execução

```text
arquivo/base externa
        ↓
input adapter
        ↓
bundle canônico
        ↓
registry do domínio
        ↓
rule executor
        ↓
build report
        ↓
ValidationReport
```

## Validações suportadas

### 1. Estrutural

Valida colunas, tipos, campos nulos, formatos e esquema mínimo.

### 2. Semântica intra-base

Valida coerência dentro da mesma base, como duplicidades, faixas inválidas e combinações incoerentes.

### 3. Relacional/inter-base

Valida dependência entre duas ou mais bases.

Exemplo:

```python
def run(self, bundle, context):
    apontamentos = bundle.get("dados", [])
    fazendas = bundle.get("fazendas", [])

    fazendas_validas = {row["codigo"] for row in fazendas}

    invalidos = [
        row
        for row in apontamentos
        if row.get("fazenda") not in fazendas_validas
    ]

    return {
        "count": len(invalidos),
        "details": invalidos,
        "message": "Existem apontamentos com fazenda inválida.",
        "severity": "HIGH",
    }
```

## Saída operacional recomendada

Cada execução deve permitir leitura rápida por quem opera o processo:

1. resumo executivo;
2. resumo por regra;
3. evidência detalhada por chave de negócio;
4. ação sugerida para correção.

## Executar a UI atual

```bash
streamlit run ui/streamlit_app/app.py
```

Fluxo atual:

1. selecionar domínio;
2. informar usuário;
3. enviar arquivos exigidos pelo domínio;
4. executar validação;
5. visualizar resumo;
6. baixar relatório JSON.

## Stack sugerida

- Python;
- Pandas;
- Pandera para validação estrutural;
- DuckDB ou SQLite para histórico local;
- Parquet para snapshots e evidências;
- Streamlit para a primeira interface.

## Roadmap

### MVP

- Um domínio real;
- 3 a 5 regras úteis;
- execução por UI ou script;
- exportação em JSON.

### Kernel reutilizável

- contratos mais rígidos;
- registry de domínios;
- testes por contrato;
- histórico estruturado.

### Automação

- agendamento;
- reprocessamento;
- alertas;
- comparação entre execuções.

### Produto interno

- autenticação;
- permissões;
- auditoria;
- dashboard operacional.

## Estado atual

- Core executa validação ponta a ponta com `ValidationReport`;
- regras retornam `RuleResult` via `rule_executor`;
- estrutura inicial de `adapters` e `domains` criada;
- Streamlit v1 criado em `ui/streamlit_app/app.py`;
- próximo ganho objetivo: persistência de histórico com SQLite ou DuckDB.

## Documentação

- Guia de uso: `docs/USAGE.md`;
- índice de documentação: `docs/README.md`;
- instruções para agentes: `AGENT.md`.

## Licença

Uso interno, ainda a definir.
