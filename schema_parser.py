import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

@dataclass
class ColumnSchema:
    name: str
    type: str
    primary_key: bool = False
    foreign_key: Optional[Tuple[str, str]] = None
    unique: bool = False
    nullable: bool = True
    raw: str = ""

@dataclass
class TableSchema:
    name: str
    columns: List[ColumnSchema] = field(default_factory=list)
    raw_sql: str = ""

@dataclass
class SchemaMetadata:
    tables: Dict[str, TableSchema] = field(default_factory=dict)


def _clean_sql(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.S)
    sql = re.sub(r"--.*?$", "", sql, flags=re.M)
    return sql.strip()


def _split_columns(definition: str) -> List[str]:
    chunks = []
    current = []
    depth = 0
    for char in definition:
        if char == "(" and current and current[-1] != "\\":
            depth += 1
        elif char == ")" and current and current[-1] != "\\":
            depth = max(depth - 1, 0)
        if char == "," and depth == 0:
            item = "".join(current).strip()
            if item:
                chunks.append(item)
            current = []
        else:
            current.append(char)
    item = "".join(current).strip()
    if item:
        chunks.append(item)
    return chunks


def _parse_column_definition(line: str) -> Optional[ColumnSchema]:
    parts = re.split(r"\s+", line, maxsplit=2)
    if not parts or parts[0].upper() in {"PRIMARY", "FOREIGN", "UNIQUE", "CONSTRAINT", "CHECK"}:
        return None
    column_name = parts[0].strip('`"[]')
    remainder = parts[1:] if len(parts) > 1 else [""]
    column_type = remainder[0] if remainder else "TEXT"
    raw = line
    primary_key = bool(re.search(r"PRIMARY\s+KEY", line, flags=re.I))
    unique = bool(re.search(r"\bUNIQUE\b", line, flags=re.I))
    nullable = not bool(re.search(r"NOT\s+NULL", line, flags=re.I))
    foreign_key = None
    ref_match = re.search(r"REFERENCES\s+([\w\.\"]+)\s*\(([^\)]+)\)", line, flags=re.I)
    if ref_match:
        parent_table = ref_match.group(1).strip('`"[]')
        parent_column = ref_match.group(2).strip('`"[] ')
        foreign_key = (parent_table, parent_column)
    return ColumnSchema(
        name=column_name,
        type=column_type,
        primary_key=primary_key,
        foreign_key=foreign_key,
        unique=unique,
        nullable=nullable,
        raw=raw,
    )


def _extract_table_constraints(lines: List[str], table: TableSchema) -> None:
    for line in lines:
        if re.search(r"PRIMARY\s+KEY", line, flags=re.I) and not line.strip().upper().startswith("PRIMARY KEY"):
            continue
        if re.search(r"PRIMARY\s+KEY\s*\(([^\)]+)\)", line, flags=re.I):
            cols = [c.strip('`"[] ') for c in re.split(r",", re.search(r"PRIMARY\s+KEY\s*\(([^\)]+)\)", line, flags=re.I).group(1))]
            for column in table.columns:
                if column.name in cols:
                    column.primary_key = True
                    column.nullable = False
        fk_match = re.search(r"FOREIGN\s+KEY\s*\(([^\)]+)\)\s*REFERENCES\s+([\w\.\"]+)\s*\(([^\)]+)\)", line, flags=re.I)
        if fk_match:
            local_cols = [c.strip('`"[] ') for c in re.split(r",", fk_match.group(1))]
            parent_table = fk_match.group(2).strip('`"[]')
            parent_cols = [c.strip('`"[] ') for c in re.split(r",", fk_match.group(3))]
            for local_col, parent_col in zip(local_cols, parent_cols):
                for column in table.columns:
                    if column.name == local_col:
                        column.foreign_key = (parent_table, parent_col)
                        column.nullable = column.nullable


def parse_schema(sql_text: str) -> SchemaMetadata:
    sql_text = _clean_sql(sql_text)
    metadata = SchemaMetadata()
    statements = re.split(r"(?i)CREATE\s+TABLE", sql_text)
    for statement in statements:
        if not statement.strip():
            continue
        header, body = statement.split("(", 1)
        table_name = header.strip().split()[0].strip('`"[]')
        body = body.rsplit(")", 1)[0]
        raw_sql = f"CREATE TABLE {header}({body})"
        table = TableSchema(name=table_name, raw_sql=raw_sql)
        lines = _split_columns(body)
        for line in lines:
            col = _parse_column_definition(line)
            if col:
                table.columns.append(col)
        _extract_table_constraints(lines, table)
        metadata.tables[table_name] = table
    return metadata


def summarize_schema(metadata: SchemaMetadata) -> Dict[str, object]:
    tables = list(metadata.tables.keys())
    columns = sum(len(table.columns) for table in metadata.tables.values())
    total_pks = sum(1 for table in metadata.tables.values() for col in table.columns if col.primary_key)
    total_fks = sum(1 for table in metadata.tables.values() for col in table.columns if col.foreign_key)
    return {
        "tables": tables,
        "total_tables": len(tables),
        "total_columns": columns,
        "total_primary_keys": total_pks,
        "total_foreign_keys": total_fks,
    }
