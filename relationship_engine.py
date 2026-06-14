import networkx as nx
from typing import Dict, List, Tuple
from schema_parser import SchemaMetadata, ColumnSchema


def build_dependency_graph(schema: SchemaMetadata) -> nx.DiGraph:
    graph = nx.DiGraph()
    for table in schema.tables.values():
        graph.add_node(table.name)
    for table in schema.tables.values():
        for column in table.columns:
            if column.foreign_key:
                parent_table, _ = column.foreign_key
                graph.add_edge(parent_table, table.name)
    return graph


def detect_relationships(schema: SchemaMetadata) -> List[str]:
    relations: List[str] = []
    for table in schema.tables.values():
        for column in table.columns:
            if column.foreign_key:
                parent_table, _ = column.foreign_key
                type_hint = "1:1" if column.unique else "1:N"
                relations.append(f"{parent_table} → {table.name} ({type_hint})")
    return relations


def summarize_graph(schema: SchemaMetadata) -> Dict[str, object]:
    graph = build_dependency_graph(schema)
    relationships = detect_relationships(schema)
    return {
        "graph": graph,
        "relationship_map": relationships,
        "relationship_count": len(relationships),
        "dependency_order": list(nx.topological_sort(graph)) if nx.is_directed_acyclic_graph(graph) else list(graph.nodes),
    }
