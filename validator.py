from typing import Dict, List, Tuple
import pandas as pd
from schema_parser import SchemaMetadata, TableSchema


def validate_data(schema: SchemaMetadata, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, List[str]]:
    issues: Dict[str, List[str]] = {}
    for table_name, table in schema.tables.items():
        df = dataframes.get(table_name)
        if df is None:
            issues[table_name] = ["Table data missing"]
            continue
        table_issues = []
        for column in table.columns:
            if not column.nullable:
                if df[column.name].isnull().any():
                    table_issues.append(f"Required column '{column.name}' contains null values")
            if column.primary_key:
                if df[column.name].isnull().any():
                    table_issues.append(f"Primary key '{column.name}' contains null values")
                if df[column.name].duplicated().any():
                    table_issues.append(f"Primary key '{column.name}' has duplicate values")
            if column.unique:
                non_null_values = df[column.name].dropna()
                if non_null_values.duplicated().any():
                    table_issues.append(f"Unique column '{column.name}' has duplicate values")
            if column.foreign_key:
                parent_table, parent_column = column.foreign_key
                parent_df = dataframes.get(parent_table)
                if parent_df is None:
                    table_issues.append(f"Missing parent table '{parent_table}' for FK '{column.name}'")
                else:
                    invalid = ~df[column.name].isin(parent_df[parent_column])
                    if invalid.any():
                        table_issues.append(f"Foreign key '{column.name}' contains invalid references")
        if table_issues:
            issues[table_name] = table_issues
    return issues


def auto_fix_data(schema: SchemaMetadata, dataframes: Dict[str, pd.DataFrame]) -> Tuple[Dict[str, pd.DataFrame], Dict[str, List[str]]]:
    issues = validate_data(schema, dataframes)
    if not issues:
        return dataframes, {}
    repaired = {}
    for table_name, table in schema.tables.items():
        df = dataframes.get(table_name)
        if df is None:
            continue
        df = df.copy()
        for column in table.columns:
            if column.primary_key:
                if df[column.name].isnull().any() or df[column.name].duplicated().any():
                    values = list(range(1, len(df) + 1))
                    df[column.name] = values
            if column.unique and not column.primary_key and df[column.name].duplicated().any():
                column_type = column.type.upper()
                if "INT" in column_type or "BIGINT" in column_type or "SMALLINT" in column_type:
                    df[column.name] = list(range(1, len(df) + 1))
                elif "FLOAT" in column_type or "DOUBLE" in column_type or "NUMERIC" in column_type or "DECIMAL" in column_type or "REAL" in column_type:
                    df[column.name] = [float(idx + 1) for idx in range(len(df))]
                else:
                    df[column.name] = [f"{value}_{idx + 1}" if pd.notna(value) else value for idx, value in enumerate(df[column.name])]
            if column.foreign_key:
                parent_table, parent_column = column.foreign_key
                parent_df = dataframes.get(parent_table)
                if parent_df is not None and not parent_df.empty:
                    df[column.name] = parent_df[parent_column].sample(n=len(df), replace=True).reset_index(drop=True)
        repaired[table_name] = df
    repaired_issues = validate_data(schema, repaired)
    return repaired, repaired_issues


def build_validation_summary(issues: Dict[str, List[str]]) -> Dict[str, object]:
    total_issues = sum(len(v) for v in issues.values())
    return {
        "passed": total_issues == 0,
        "issue_count": total_issues,
        "details": issues,
    }
