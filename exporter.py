import csv
import io
import zipfile
from typing import Dict, Tuple
import pandas as pd
from schema_parser import SchemaMetadata


def generate_csv_bytes(dataframes: Dict[str, pd.DataFrame]) -> Dict[str, bytes]:
    results: Dict[str, bytes] = {}
    for name, df in dataframes.items():
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        results[f"{name}.csv"] = buffer.getvalue().encode("utf-8")
    return results


def generate_sql_inserts(schema: SchemaMetadata, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, str]:
    inserts: Dict[str, str] = {}
    for name, df in dataframes.items():
        table = schema.tables.get(name)
        if table is None:
            continue
        lines = []
        for _, row in df.iterrows():
            columns = [f"\"{col}\"" for col in df.columns]
            values = []
            for value in row:
                if pd.isna(value):
                    values.append("NULL")
                elif isinstance(value, (int, float)) and not isinstance(value, bool):
                    values.append(str(value))
                else:
                    escaped = str(value).replace("'", "''")
                    values.append(f"'{escaped}'")
            lines.append(f"INSERT INTO \"{name}\" ({', '.join(columns)}) VALUES ({', '.join(values)});")
        inserts[f"{name}.sql"] = "\n".join(lines)
    return inserts


def build_zip_package(schema: SchemaMetadata, dataframes: Dict[str, pd.DataFrame], validation_summary: Dict[str, object]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for filename, content in generate_csv_bytes(dataframes).items():
            zf.writestr(filename, content)
        for filename, sql_text in generate_sql_inserts(schema, dataframes).items():
            zf.writestr(filename, sql_text)
        report_text = ["SCHEMA AWARE TEST DATA GENERATOR REPORT", ""]
        report_text.append(f"Tables: {len(schema.tables)}")
        report_text.append(f"Rows Generated: {sum(len(df) for df in dataframes.values())}")
        report_text.append(f"Validation Passed: {validation_summary.get('passed', False)}")
        report_text.append(f"Issue Count: {validation_summary.get('issue_count', 0)}")
        report_text.append("\nDetailed validation results:")
        for table, issues in validation_summary.get("details", {}).items():
            report_text.append(f"- {table}: {len(issues)} issues")
            for issue in issues:
                report_text.append(f"  - {issue}")
        zf.writestr("schema_summary_report.txt", "\n".join(report_text))
    return buffer.getvalue()
