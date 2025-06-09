import os
import pandas as pd
import requests
from sqlalchemy import create_engine, text, inspect
from dotenv import load_dotenv

os.chdir(os.path.dirname(os.getcwd()))
load_dotenv()

username = os.environ.get('POSTGRES_USERNAME')
password = os.environ.get('POSTGRES_PASSWORD')
host = os.environ.get('POSTGRES_HOST')
port = os.environ.get('POSTGRES_PORT')
database = os.environ.get('POSTGRES_DB')

GLEIF_API_URL = "https://api.gleif.org/api/v1/lei-records"
REMOVE_KEYS = ['bic', 'mic', 'ocid', 'qcc', 'spglobal', 'conformityFlag']

# DB connection
engine = create_engine(f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")
table_name = "test"

def extract_leaf_nodes(data, parent_key=''):
    leaves = {}
    
    if isinstance(data, dict):
        for key, value in data.items():
            full_key = f"{parent_key}.{key}" if parent_key else key
            leaves.update(extract_leaf_nodes(value, full_key))
    
    elif isinstance(data, list):
        for idx, item in enumerate(data, 1):
            full_key = f"{parent_key}.{idx}"
            leaves.update(extract_leaf_nodes(item, full_key))
    
    else:
        # Base case: leaf node
        leaves[parent_key] = data
    
    return leaves


def fetch_lei_records(limit=100):
    params = {"page[size]": limit}
    response = requests.get(GLEIF_API_URL, params=params)

    lei_records = []
    
    if response.status_code == 200:
        data = response.json()["data"]
        for i, item in enumerate(data, 1):
            attributes = item['attributes']
            [attributes.pop(key) for key in REMOVE_KEYS]

            lei = extract_leaf_nodes(attributes)
            lei_records.append(lei)
            
        return lei_records
    else:
        raise Exception(f"GLEIF API error: {response.status_code}")

df = pd.DataFrame(fetch_lei_records())

with engine.connect() as conn:
    inspector = inspect(engine)
    existing_columns = set()

    # Create table if not exists
    if table_name not in inspector.get_table_names():
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        print("Created table with initial schema.")
        exit()

    existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
    
    # Add missing columns
    new_columns = set(df.columns) - existing_columns
    for col in new_columns:
        conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" TEXT;'))

    # Fetch existing LEIs from the table
    result = conn.execute(text(f'SELECT lei FROM "{table_name}";'))
    existing_lei_set = {row[0] for row in result}

    # Filter out rows already present
    df_new = df[~df["lei"].isin(existing_lei_set)]

    # Insert only new rows
    if not df_new.empty:
        df_new.to_sql(table_name, engine, if_exists="append", index=False)
        print(f"Inserted {len(df_new)} new rows.")
    else:
        print("No new records to insert.")