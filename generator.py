import random
import re
from typing import Dict, Any, List
import pandas as pd
from faker import Faker
from schema_parser import SchemaMetadata, TableSchema, ColumnSchema
from relationship_engine import summarize_graph, build_dependency_graph
from fk_manager import resolve_foreign_keys

faker = Faker("en_IN")
faker.seed_instance(42)
random.seed(42)

INDIAN_FIRST_NAMES = [
    "Varalakshmi", "Rahul", "Priya", "Arjun", "Ananya", "Karthik",
    "Sneha", "Rohit", "Divya", "Vikram", "Meera", "Suresh",
]
INDIAN_LAST_NAMES = [
    "TC", "Sharma", "Reddy", "Kumar", "Iyer", "Nair", "Patel",
    "Gupta", "Rao", "Menon", "Das", "Singh",
]
EMAIL_DOMAINS = ["gmail.com", "yahoo.com", "outlook.com", "rediffmail.com"]
INDIAN_LOCATIONS = [
    ("Bengaluru", "Karnataka", "560001", "MG Road"),
    ("Hyderabad", "Telangana", "500081", "Jubilee Hills"),
    ("Chennai", "Tamil Nadu", "600001", "Anna Salai"),
    ("Mumbai", "Maharashtra", "400001", "Bandra Kurla Complex"),
    ("Pune", "Maharashtra", "411001", "Koregaon Park"),
    ("Delhi", "Delhi", "110001", "Connaught Place"),
    ("Kolkata", "West Bengal", "700001", "Park Street"),
    ("Ahmedabad", "Gujarat", "380001", "CG Road"),
]
COMPANIES = ["Infosys", "TCS", "Wipro", "HCL", "Tech Mahindra", "Reliance", "HDFC Bank", "Airtel"]
DEPARTMENTS = ["HR", "Finance", "Engineering", "Marketing", "Sales", "Operations", "Legal", "Support"]
DESIGNATIONS = ["Software Engineer", "Data Analyst", "QA Engineer", "Project Manager", "HR Manager", "Business Analyst"]
PRODUCTS = ["Laptop", "Smartphone", "Headphones", "Smart Watch", "Wireless Mouse", "Office Chair", "Monitor"]
PRODUCT_CATEGORIES = ["Electronics", "Accessories", "Office Supplies", "Wearables", "Home Appliances"]
COURSES = ["Data Structures", "Database Systems", "Machine Learning", "Business Analytics", "Cloud Computing"]
ACCOUNT_TYPES = ["Savings", "Current", "Salary", "NRI"]
TRANSACTION_TYPES = ["Credit", "Debit", "UPI", "NEFT", "IMPS"]
ORDER_STAGES = ["New", "Processing", "Shipped", "Delivered", "Cancelled"]
CUISINES = ["South Indian", "North Indian", "Biryani", "Chinese", "Continental"]
ROOM_TYPES = ["Deluxe", "Executive", "Suite", "Standard"]
MEDICAL_SPECIALTIES = ["Cardiology", "Dermatology", "Orthopedics", "Pediatrics", "General Medicine"]


def _tokens(name: str) -> List[str]:
    return [token for token in re.split(r"[^a-z0-9]+", name.lower()) if token]


def _has_any(text: str, keywords: List[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _choice(values: List[Any], index: int) -> Any:
    return values[index % len(values)]


def _location(index: int) -> tuple:
    return INDIAN_LOCATIONS[index % len(INDIAN_LOCATIONS)]


def _person_parts(index: int) -> tuple:
    return _choice(INDIAN_FIRST_NAMES, index), _choice(INDIAN_LAST_NAMES, index)


def _person_name(index: int) -> str:
    first, last = _person_parts(index)
    return f"{first} {last}"


def _email(index: int) -> str:
    first, last = _person_parts(index)
    domain = _choice(EMAIL_DOMAINS, index)
    return f"{first.lower()}.{last.lower().replace(' ', '')}{index + 1 if index >= len(INDIAN_FIRST_NAMES) else ''}@{domain}"


def _phone(index: int) -> str:
    prefixes = [90, 91, 92, 93, 94, 95, 96, 97, 98, 99]
    return f"{_choice(prefixes, index)}{63009274 + index:08d}"[:10]


def _gst_number(index: int) -> str:
    state_codes = ["29", "36", "33", "27", "07", "19", "24"]
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    prefix = "".join(letters[(index + offset) % len(letters)] for offset in range(5))
    return f"{_choice(state_codes, index)}{prefix}{1234 + index:04d}{letters[index % len(letters)]}1Z{5 + index % 5}"


def _pan_number(index: int) -> str:
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    prefix = "".join(letters[(index + offset) % len(letters)] for offset in range(5))
    return f"{prefix}{1234 + index:04d}{letters[index % len(letters)]}"


def _aadhaar_like(index: int) -> str:
    return f"{123456789012 + index:012d}"


def _account_number(index: int) -> str:
    return f"{50100000000000 + index:014d}"


def _ifsc_code(index: int) -> str:
    bank_codes = ["HDFC", "ICIC", "SBIN", "UTIB", "KKBK"]
    return f"{_choice(bank_codes, index)}0{110001 + index:06d}"


def _varchar_limit(column_type: str, default: int = 50) -> int:
    match = re.search(r"(?:VAR)?CHAR\s*\((\d+)\)", column_type.upper())
    if not match:
        return default
    try:
        return min(int(match.group(1)), default)
    except Exception:
        return default


def _fit(value: Any, column: ColumnSchema) -> Any:
    if not isinstance(value, str):
        return value
    t = column.type.upper()
    if "CHAR" in t or "TEXT" in t or "VARCHAR" in t:
        return value[:_varchar_limit(t, len(value))]
    return value


def _semantic_value(column: ColumnSchema, table_name: str, index: int) -> Any:
    name = column.name.lower()
    table = table_name.lower()
    full_context = f"{table}.{name}"
    token_set = set(_tokens(full_context))

    if "email" in token_set or name.endswith("_email"):
        return _email(index)
    if token_set.intersection({"phone", "mobile", "contact", "telephone", "whatsapp"}):
        return _phone(index)
    if token_set.intersection({"gst", "gstin"}):
        return _gst_number(index)
    if "pan" in token_set:
        return _pan_number(index)
    if token_set.intersection({"aadhaar", "aadhar", "uidai"}):
        return _aadhaar_like(index)
    if "ifsc" in token_set:
        return _ifsc_code(index)
    if token_set.intersection({"account", "acct"}) and "number" in token_set:
        return _account_number(index)
    if "isbn" in token_set:
        return f"978-81-{1000 + index:04d}-{100 + index:03d}-0"
    if "room" in token_set and "number" in token_set:
        return f"{100 + index}"
    if token_set.intersection({"pincode", "pin", "postcode", "postal", "zip"}):
        return _location(index)[2]
    if "city" in token_set:
        return _location(index)[0]
    if "state" in token_set:
        return _location(index)[1]
    if "country" in token_set or "nationality" in token_set:
        return "India"
    if token_set.intersection({"address", "addr", "location"}):
        city, _, _, road = _location(index)
        return f"{12 + index} {road}, {city}"

    if token_set.intersection({"salary", "ctc", "payroll"}):
        return _choice([45000, 65000, 85000, 120000, 150000], index)
    if token_set.intersection({"price", "mrp", "rate"}):
        return _choice([59999, 24999, 1499, 3999, 899, 129999], index)
    if token_set.intersection({"amount", "total", "balance", "cost", "payment", "fee"}):
        return round(_choice([2500.75, 999.00, 15499.50, 75000.00, 1200.25, 48500.75], index), 2)
    if token_set.intersection({"quantity", "qty", "stock", "units"}):
        return _choice([1, 2, 3, 5, 10, 25, 50], index)

    if token_set.intersection({"dob", "birth"}):
        return faker.date_of_birth(minimum_age=18, maximum_age=75).isoformat()
    if token_set.intersection({"date", "created", "updated", "signup", "hire", "order", "invoice", "delivery", "appointment", "loan", "due", "check"}):
        return faker.date_between(start_date="-2y", end_date="today").isoformat()
    if token_set.intersection({"department", "dept"}):
        return _choice(DEPARTMENTS, index)
    if token_set.intersection({"designation", "role", "position", "job", "title"}):
        if "book" in table and "title" in token_set:
            return _choice(["The Guide", "Train to Pakistan", "Malgudi Days", "The White Tiger"], index)
        return _choice(DESIGNATIONS, index)
    if token_set.intersection({"company", "organization", "organisation", "org", "employer"}):
        return _choice(COMPANIES, index)
    if token_set.intersection({"product", "item", "sku"}):
        return f"SKU-{1000 + index}" if "sku" in token_set else _choice(PRODUCTS, index)
    if token_set.intersection({"category"}):
        return _choice(PRODUCT_CATEGORIES, index)
    if token_set.intersection({"course", "subject"}):
        return _choice(COURSES, index)
    if token_set.intersection({"account"}) and "type" in token_set:
        return _choice(ACCOUNT_TYPES, index)
    if token_set.intersection({"transaction"}) and "type" in token_set:
        return _choice(TRANSACTION_TYPES, index)
    if token_set.intersection({"stage", "status"}):
        return _choice(ORDER_STAGES, index)
    if "cuisine" in token_set:
        return _choice(CUISINES, index)
    if "room" in token_set and "type" in token_set:
        return _choice(ROOM_TYPES, index)
    if token_set.intersection({"specialty", "speciality"}):
        return _choice(MEDICAL_SPECIALTIES, index)
    if token_set.intersection({"grade"}):
        return _choice(["A", "B+", "B", "C+", "A+"], index)
    if token_set.intersection({"source"}):
        return _choice(["Website", "Referral", "LinkedIn", "Walk-in", "Email Campaign"], index)

    if "first" in token_set:
        return _person_parts(index)[0]
    if "last" in token_set:
        return _person_parts(index)[1]
    if "author" in token_set:
        return _person_name(index)
    if "name" in token_set:
        if _has_any(table, ["product", "item", "inventory"]):
            return _choice(PRODUCTS, index)
        if _has_any(table, ["company", "vendor", "supplier", "organization", "organisation"]):
            return _choice(COMPANIES, index)
        if "department" in table:
            return _choice(DEPARTMENTS, index)
        if "course" in table:
            return _choice(COURSES, index)
        if "restaurant" in table:
            return _choice(["A2B", "Paradise Biryani", "Saravana Bhavan", "Barbeque Nation"], index)
        if "room" in table:
            return f"{100 + index}"
        return _person_name(index)

    return None


def _ensure_type(value: Any, column: ColumnSchema) -> Any:
    if pd.isna(value):
        return None
    t = column.type.upper()
    if "INT" in t or "BIGINT" in t or "SMALLINT" in t:
        try:
            return int(value)
        except Exception:
            return 0
    if "FLOAT" in t or "DOUBLE" in t or "NUMERIC" in t or "DECIMAL" in t or "REAL" in t:
        try:
            return float(value)
        except Exception:
            return 0.0
    return str(value)


def _generate_value(column: ColumnSchema, index: int, table_name: str = "", optional: bool = False) -> Any:
    name = column.name.lower()
    t = column.type.upper()
    if optional and random.random() < 0.12:
        return None
    if column.primary_key:
        if "UUID" in t:
            return faker.uuid4()
        if "CHAR" in t or "TEXT" in t or "VARCHAR" in t:
            return f"{column.name[:3].upper()}_{index + 1}"
        return index + 1
    semantic = _semantic_value(column, table_name, index)
    if semantic is not None:
        return _fit(semantic, column)
    if "ID" == name or name.endswith("_id"):
        return index + 1
    if "DATE" in t or "TIMESTAMP" in t or "TIME" in t:
        return faker.date_between(start_date="-2y", end_date="today").isoformat()
    if "PRICE" in t or "DECIMAL" in t or "NUMERIC" in t:
        return round(random.uniform(500, 150000), 2)
    if "BOOL" in t or t == "BOOLEAN":
        return random.choice([True, False])
    if "INT" in t or "BIGINT" in t:
        return random.randint(1, 100)
    if "CHAR" in t or "TEXT" in t or "VARCHAR" in t:
        limit = _varchar_limit(t)
        return faker.sentence(nb_words=3)[:limit]
    return faker.word()


def generate_rows_for_table(table: TableSchema, count: int, generated_rows: Dict[str, List[Dict[str, Any]]], dataset_type: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for i in range(count):
        row: Dict[str, Any] = {}
        for column in table.columns:
            if column.foreign_key:
                parent_table, parent_column = column.foreign_key
                parent_values = [parent_row[parent_column] for parent_row in generated_rows.get(parent_table, []) if parent_column in parent_row]
                if parent_values:
                    row[column.name] = random.choice(parent_values)
                    continue
            allow_null = dataset_type == "Edge Case Dataset" and column.nullable
            row[column.name] = _generate_value(column, i, table.name, optional=allow_null)
        rows.append(row)
    if any(col.primary_key for col in table.columns):
        for col in table.columns:
            if col.primary_key and "INT" in col.type.upper():
                for idx, row in enumerate(rows):
                    row[col.name] = idx + 1
    return rows


def generate_data(schema: SchemaMetadata, table_counts: Dict[str, int], dataset_type: str) -> Dict[str, Any]:
    graph_info = summarize_graph(schema)
    order = graph_info["dependency_order"]
    generated_rows: Dict[str, List[Dict[str, Any]]] = {}
    for table_name in order:
        table = schema.tables[table_name]
        count = max(1, table_counts.get(table_name, 10))
        rows = generate_rows_for_table(table, count, generated_rows, dataset_type)
        if any(col.foreign_key for col in table.columns):
            resolve_foreign_keys(table, rows, generated_rows)
        generated_rows[table_name] = rows
    return generated_rows


def build_dataframes(schema: SchemaMetadata, generated_rows: Dict[str, List[Dict[str, Any]]]) -> Dict[str, pd.DataFrame]:
    result: Dict[str, pd.DataFrame] = {}
    for name, rows in generated_rows.items():
        result[name] = pd.DataFrame(rows)
    return result
