# Guia de Uso

Este documento cobre:
- como executar a ferramenta
- como rodar uma validacao via codigo
- como criar novas regras
- como criar novos dominios

## 1. Como usar a ferramenta

### 1.1 Executar a interface Streamlit
No diretorio raiz do projeto:

```bash
streamlit run ui/streamlit_app/app.py
```

Metadados visuais da UI:
- o arquivo `ui/streamlit_app/metadata.json` controla o `title` e a `caption` exibidos no frontend;
- o arquivo `ui/streamlit_app/metadata.example.json` serve como modelo para novos ambientes;
- se `metadata.json` nao existir, a aplicacao tenta usar o arquivo de exemplo e, por ultimo, os valores padrao do codigo.

Exemplo de configuracao:

```json
{
    "title": "Meu Validador de Dados",
    "caption": "Painel interno para execucao das regras de validacao."
}
```

Fluxo da tela:
1. Selecione o dominio.
2. Informe o usuario (opcional, default `admin`).
3. Envie um arquivo `CSV`, `JSON` ou `XLSX`.
4. Clique em `Validar`.
5. Veja o resumo e baixe o relatorio em `JSON` ou `Excel`.

### 1.2 Executar via codigo (sem UI)
Use a camada de aplicacao `run_validation_job`:

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

print(report.total_fail)
```

## 2. Adapters disponiveis

Arquivos em `adapters/inputs/`:
- `CsvInputAdapter`
- `JsonInputAdapter`
- `ExcelInputAdapter`

Todos retornam um `bundle` no formato:

```python
{
    "dados": [
        {"coluna_a": "...", "coluna_b": "..."},
        ...
    ]
}
```

Se quiser outra chave, ajuste `bundle_key` ao instanciar o adapter.

Dominio de exemplo versionado no repositorio:

`domains/exemplo/`

Arquivos de entrada desse dominio:

`domains/exemplo/examples/dados_exemplo.json`

`domains/exemplo/examples/referencias_exemplo.json`

## 3. Como criar novas validacoes (rules)

### 3.1 Criar arquivo da regra
Crie um arquivo em:

`domains/<dominio>/rules/<nome_da_regra>.py`

Exemplo:

```python
class CheckMissingFarmRule:
    name = "missing_farm"
    rule_id = "missing_farm"

    def run(self, bundle, context):
        rows = bundle.get("dados", [])
        missing = [row for row in rows if not row.get("fazenda")]

        return {
            "count": len(missing),
            "details": missing,
            "severity": "HIGH",
            "message": "Fazenda ausente encontrada." if missing else None,
        }
```

### 3.2 Contrato obrigatorio da regra
A regra deve ter:
- `name`
- (recomendado) `rule_id`
- `run(bundle, context) -> dict`

Retorno minimo:
- `count`

Campos recomendados:
- `details`
- `severity`
- `message`
- `status` (opcional; se nao informado, o executor infere `PASS`/`FAIL` por `count`)

### 3.3 Registrar regra no dominio
No `registry.py` do dominio:

```python
from .rules.missing_farm import CheckMissingFarmRule

def get_rules():
    return [CheckMissingFarmRule()]
```

Se o dominio precisar de uploads dinamicos, ele tambem pode expor:

```python
def get_input_specs():
    return [
        {
            "key": "dados",
            "label": "Dados principais",
            "required": True,
            "formats": ["csv", "json", "xlsx", "xlsm"],
        },
        {
            "key": "referencias",
            "label": "Base de referencias",
            "required": True,
            "formats": ["csv", "json", "xlsx", "xlsm"],
        },
    ]
```

### 3.4 Quando a validacao precisa de duas bases ou mais
O `bundle` nao precisa conter apenas uma lista. Ele pode carregar varias bases ao mesmo tempo:

```python
bundle = {
    "dados": [
        {"matricula": "1001", "fazenda": "F001"},
    ],
    "fazendas": [
        {"codigo": "F001", "nome": "Boa Vista"},
        {"codigo": "F002", "nome": "Santa Rita"},
    ],
}
```

A regra pode consumir mais de uma chave:

```python
class CheckFarmExistsRule:
    name = "farm_exists"
    rule_id = "farm_exists"

    def run(self, bundle, context):
        apontamentos = bundle.get("dados", [])
        fazendas = bundle.get("fazendas", [])
        fazendas_validas = {row["codigo"] for row in fazendas}

        invalidos = [
            row for row in apontamentos
            if row.get("fazenda") and row["fazenda"] not in fazendas_validas
        ]

        return {
            "count": len(invalidos),
            "details": invalidos,
            "severity": "HIGH",
            "message": "Ha fazendas informadas fora da base de referencia." if invalidos else None,
        }
```

No estado atual do projeto, a UI usa esse metadado para abrir os uploads dinamicamente e a camada de aplicacao consolida tudo em um unico `bundle`.

## 4. Como criar novos dominios

### 4.1 Estrutura de pastas
Crie:

```text
domains/
  novo_dominio/
    __init__.py
    registry.py
    rules/
      __init__.py
      minha_regra.py
```

### 4.2 Implementar `registry.py`

```python
from .rules.minha_regra import MinhaRegra

def get_rules():
    return [MinhaRegra()]
```

### 4.3 Expor o dominio no registro global
Edite `domains/__init__.py` e adicione:

```python
from .novo_dominio.registry import get_rules as get_novo_dominio_rules

DOMAIN_REGISTRY = {
    "novo_dominio": get_novo_dominio_rules,
}
```

Depois disso, o dominio aparece automaticamente no select do Streamlit.

## 5. Boas praticas

- Mantenha regras pequenas e com responsabilidade unica.
- Use `rule_id` estavel para rastreabilidade.
- Nao coloque logica de regra na UI.
- Padronize o `bundle_key` por dominio (ex.: `dados`).
- Crie testes para cada regra critica.

## 6. Checklist rapido para subir um novo dominio

1. Criar pasta `domains/<dominio>/`.
2. Criar pelo menos 1 regra em `rules/`.
3. Implementar `get_rules()` no `registry.py`.
4. Registrar dominio em `domains/__init__.py`.
5. Executar via Streamlit ou `run_validation_job`.
6. Validar o resultado (`PASS/FAIL/ERROR`) no relatorio.
