import random
from typing import Dict, List, Tuple, Any
from schema_parser import ColumnSchema, TableSchema


def resolve_foreign_keys(table: TableSchema, row_values: List[Dict[str, Any]], generated_rows: Dict[str, List[Dict[str, Any]]]) -> None:
    for fk_column in [col for col in table.columns if col.foreign_key]:
        parent_table, parent_column = fk_column.foreign_key
        parent_rows = generated_rows.get(parent_table, [])
        if not parent_rows:
            continue
        parent_values = [row[parent_column] for row in parent_rows if parent_column in row]
        if not parent_values:
            continue
        for row in row_values:
            row[fk_column.name] = random.choice(parent_values)


def collect_parent_values(parent_table: str, parent_column: str, generated_rows: Dict[str, List[Dict[str, Any]]]) -> List[Any]:
    rows = generated_rows.get(parent_table, [])
    return [row[parent_column] for row in rows if parent_column in row]
