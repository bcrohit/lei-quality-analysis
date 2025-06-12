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

if __name__ == '__main__':
    
    with engine.connect() as conn:
        inspector = inspect(engine)

        # Create table if it does not exist
        if table_name not in inspector.get_table_names():
            df.to_sql(table_name, engine, if_exists="replace", index=False)
            print("Created table with initial schema.")
            exit()

        # Add missing columns (only if needed)
        existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
        new_columns = set(df.columns) - existing_columns
        for col in new_columns:
            conn.execute(text(f'ALTER TABLE "{table_name}" ADD COLUMN "{col}" TEXT;'))
            conn.commit()

        # Create a temporary table with incoming data
        tmp_table = f"{table_name}_tmp"
        df.to_sql(tmp_table, engine, if_exists="replace", index=False)

        # Insert only new LEIs from temp table using LEFT JOIN
        insert_sql = f"""
            INSERT INTO "{table_name}" ({', '.join(f'"{col}"' for col in df.columns)})
            SELECT {', '.join(f't."{col}"' for col in df.columns)}
            FROM "{tmp_table}" t
            LEFT JOIN "{table_name}" main ON t.lei = main.lei
            WHERE main.lei IS NULL;
        """

        result = conn.execute(text(insert_sql))
        conn.commit()
        print(f"Inserted {result.rowcount} new rows.")

        # Drop the temporary table
        conn.execute(text(f'DROP TABLE IF EXISTS "{tmp_table}";'))
        conn.commit()