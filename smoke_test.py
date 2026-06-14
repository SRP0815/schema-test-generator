from generator import build_dataframes, generate_data
from schema_parser import parse_schema
from validator import validate_data


SCHEMAS = {
    "indian_orders": """
CREATE TABLE customers(
    customer_id INT PRIMARY KEY,
    customer_name VARCHAR(120) NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    phone VARCHAR(20),
    city VARCHAR(80),
    state VARCHAR(80),
    country VARCHAR(80),
    address VARCHAR(200),
    pincode VARCHAR(10),
    pan_number VARCHAR(10),
    gst_number VARCHAR(15),
    aadhaar_number VARCHAR(12)
);
CREATE TABLE products(
    product_id INT PRIMARY KEY,
    product_name VARCHAR(120) NOT NULL,
    category VARCHAR(80),
    price DECIMAL(10,2)
);
CREATE TABLE orders(
    order_id INT PRIMARY KEY,
    customer_id INT NOT NULL REFERENCES customers(customer_id),
    product_id INT NOT NULL REFERENCES products(product_id),
    order_date DATE,
    amount DECIMAL(10,2)
);
""",
    "banking": """
CREATE TABLE accounts(
    account_id INT PRIMARY KEY,
    account_number VARCHAR(32) UNIQUE NOT NULL,
    ifsc_code VARCHAR(20),
    account_type VARCHAR(50),
    balance DECIMAL(12,2)
);
CREATE TABLE clients(
    client_id INT PRIMARY KEY,
    client_name VARCHAR(120) NOT NULL,
    client_email VARCHAR(120),
    phone VARCHAR(20),
    created_at DATE
);
CREATE TABLE transactions(
    transaction_id INT PRIMARY KEY,
    account_id INT NOT NULL REFERENCES accounts(account_id),
    transaction_date DATE,
    amount DECIMAL(10,2),
    transaction_type VARCHAR(50)
);
""",
}


def main() -> None:
    for name, sql in SCHEMAS.items():
        schema = parse_schema(sql)
        rows = generate_data(schema, {table_name: 25 for table_name in schema.tables}, "Normal Dataset")
        dataframes = build_dataframes(schema, rows)
        issues = validate_data(schema, dataframes)
        if issues:
            raise AssertionError(f"{name} failed validation: {issues}")
        print(f"{name}: passed")


if __name__ == "__main__":
    main()
