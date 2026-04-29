import json
import sys
from dataclasses import asdict
from datetime import date, datetime
from io import BytesIO
from pathlib import Path
from uuid import uuid4

import streamlit as st
import xlsxwriter

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from adapters.inputs.csv import CsvInputAdapter
from adapters.inputs.excel import ExcelInputAdapter
from adapters.inputs.json import JsonInputAdapter
from core.application import run_validation_job
from domains import get_domain_input_specs, get_registered_domain_ids

APP_METADATA_PATH = Path(__file__).with_name("metadata.json")
APP_METADATA_EXAMPLE_PATH = Path(__file__).with_name("metadata.example.json")
DEFAULT_APP_METADATA = {
    "title": "Data Validation Kernel",
    "caption": "Upload de base, execucao de regras e relatorio padronizado.",
}
UPLOAD_DIR = Path(".runtime_uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def _load_app_metadata():
    for metadata_path in [APP_METADATA_PATH, APP_METADATA_EXAMPLE_PATH]:
        if not metadata_path.exists():
            continue

        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        return {
            "title": data.get("title") or DEFAULT_APP_METADATA["title"],
            "caption": data.get("caption") or DEFAULT_APP_METADATA["caption"],
        }

    return DEFAULT_APP_METADATA.copy()


def _save_uploaded_file(uploaded_file) -> Path:
    suffix = Path(uploaded_file.name).suffix.lower()
    target = UPLOAD_DIR / f"{uuid4().hex}{suffix}"
    target.write_bytes(uploaded_file.getbuffer())
    return target


def _build_adapter(file_suffix: str, bundle_key: str):
    if file_suffix == ".csv":
        return CsvInputAdapter(bundle_key=bundle_key)
    if file_suffix in [".xlsx", ".xlsm"]:
        return ExcelInputAdapter(bundle_key=bundle_key)
    if file_suffix == ".json":
        return JsonInputAdapter(bundle_key=bundle_key)
    raise ValueError("Formato nao suportado. Use CSV, JSON ou XLSX.")


def _result_rows(report):
    rows = []
    for result in report.results:
        rows.append(
            {
                "rule_id": result.rule_id,
                "rule_name": result.rule_name,
                "status": result.status,
                "severity": result.severity,
                "count": result.count,
                "duration_ms": round(result.duration_ms or 0.0, 2),
                "message": result.message or "",
            }
        )
    return rows


def _json_default(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def _build_excel_report(report) -> bytes:
    output = BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})

    header_format = workbook.add_format({"bold": True, "bg_color": "#D9E2F3", "border": 1})
    text_wrap_format = workbook.add_format({"text_wrap": True, "valign": "top"})
    number_format = workbook.add_format({"num_format": "0.00"})

    summary_sheet = workbook.add_worksheet("Resumo")
    summary_rows = [
        ("template_id", report.template_id),
        ("total_rules", report.total_rules),
        ("total_pass", report.total_pass),
        ("total_fail", report.total_fail),
        ("total_warning", report.total_warning),
        ("total_error", report.total_error),
        ("duration_ms", report.duration_ms),
    ]
    summary_sheet.write_row(0, 0, ["campo", "valor"], header_format)
    for row_index, (field_name, value) in enumerate(summary_rows, start=1):
        summary_sheet.write(row_index, 0, field_name)
        if isinstance(value, float):
            summary_sheet.write_number(row_index, 1, value, number_format)
        else:
            summary_sheet.write(row_index, 1, value)
    summary_sheet.set_column("A:A", 20)
    summary_sheet.set_column("B:B", 18)

    results_sheet = workbook.add_worksheet("Resultados")
    results_headers = ["rule_id", "rule_name", "status", "severity", "count", "duration_ms", "message", "details"]
    results_sheet.write_row(0, 0, results_headers, header_format)

    for row_index, result in enumerate(report.results, start=1):
        results_sheet.write(row_index, 0, result.rule_id)
        results_sheet.write(row_index, 1, result.rule_name)
        results_sheet.write(row_index, 2, result.status)
        results_sheet.write(row_index, 3, result.severity)
        results_sheet.write_number(row_index, 4, result.count)
        results_sheet.write_number(row_index, 5, round(result.duration_ms or 0.0, 2), number_format)
        results_sheet.write(row_index, 6, result.message or "", text_wrap_format)
        results_sheet.write(
            row_index,
            7,
            json.dumps(result.details, ensure_ascii=False, default=_json_default),
            text_wrap_format,
        )

    results_sheet.set_column("A:A", 18)
    results_sheet.set_column("B:B", 28)
    results_sheet.set_column("C:E", 12)
    results_sheet.set_column("F:F", 14)
    results_sheet.set_column("G:G", 40)
    results_sheet.set_column("H:H", 60)

    workbook.close()
    output.seek(0)
    return output.getvalue()


def main():
    app_metadata = _load_app_metadata()

    st.set_page_config(page_title=app_metadata["title"], layout="wide")
    st.title(app_metadata["title"])
    st.caption(app_metadata["caption"])

    domain_options = get_registered_domain_ids()
    if not domain_options:
        st.error("Nenhum dominio registrado.")
        return

    col1, col2 = st.columns(2)
    with col1:
        domain_id = st.selectbox("Dominio", options=domain_options)
    with col2:
        user_name = st.text_input("Usuario", value="admin")

    input_specs = get_domain_input_specs(domain_id)
    uploaded_files = {}
    for spec in input_specs:
        formats = spec.get("formats", ["csv", "json", "xlsx", "xlsm"])
        uploaded_files[spec["key"]] = st.file_uploader(
            spec.get("label", spec["key"]),
            type=formats,
            key=f"{domain_id}_{spec['key']}",
        )

    run_clicked = st.button("Validar", type="primary", use_container_width=True)
    if not run_clicked:
        return

    missing_required_inputs = [
        spec.get("label", spec["key"])
        for spec in input_specs
        if spec.get("required", True) and uploaded_files.get(spec["key"]) is None
    ]
    if missing_required_inputs:
        st.warning(f"Envie os arquivos obrigatorios: {', '.join(missing_required_inputs)}.")
        return

    progress = st.progress(0, text="Preparando validacao...")

    try:
        with st.status("Executando validacao...", expanded=True) as status:
            status.write("Selecionando adapters das origens...")
            adapters = {}
            sources = {}
            for spec in input_specs:
                uploaded_file = uploaded_files.get(spec["key"])
                if uploaded_file is None:
                    continue

                suffix = Path(uploaded_file.name).suffix.lower()
                adapters[spec["key"]] = _build_adapter(suffix, bundle_key=spec["key"])
            progress.progress(20, text="Adapters selecionados")

            status.write("Salvando arquivos enviados...")
            for spec in input_specs:
                uploaded_file = uploaded_files.get(spec["key"])
                if uploaded_file is None:
                    continue
                sources[spec["key"]] = str(_save_uploaded_file(uploaded_file))
            progress.progress(45, text="Arquivos salvos")

            status.write("Rodando regras do dominio...")
            report = run_validation_job(
                domain_id=domain_id,
                source=sources,
                adapter=adapters,
                context={"user": user_name},
            )
            progress.progress(85, text="Regras executadas")

            status.write("Consolidando relatorio...")
            progress.progress(100, text="Validacao concluida")
            status.update(label="Validacao finalizada com sucesso", state="complete")
    except Exception as exc:
        progress.empty()
        st.error(f"Falha na validacao: {exc}")
        return

    progress.empty()
    st.subheader("Resumo da execucao")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Total regras", report.total_rules)
    m2.metric("PASS", report.total_pass)
    m3.metric("FAIL", report.total_fail)
    m4.metric("WARNING", report.total_warning)
    m5.metric("ERROR", report.total_error)

    st.caption(f"Template: {report.template_id} | Duracao: {report.duration_ms:.2f} ms")

    st.subheader("Resultados por regra")
    st.dataframe(_result_rows(report), use_container_width=True)

    report_dict = asdict(report)
    report_json = json.dumps(report_dict, ensure_ascii=False, indent=2, default=_json_default)
    report_excel = _build_excel_report(report)

    download_col_json, download_col_excel = st.columns(2)
    with download_col_json:
        st.download_button(
            label="Baixar relatorio (JSON)",
            data=report_json.encode("utf-8"),
            file_name=f"validation_report_{domain_id}.json",
            mime="application/json",
            use_container_width=True,
        )
    with download_col_excel:
        st.download_button(
            label="Baixar relatorio (Excel)",
            data=report_excel,
            file_name=f"validation_report_{domain_id}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    with st.expander("Detalhes completos (JSON)"):
        st.code(report_json, language="json")


if __name__ == "__main__":
    main()
