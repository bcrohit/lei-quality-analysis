import os
import re
import pycountry
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

def fetch_data_from_db(table_name='test'):
    """
    Returns: pandas DataFrame
    """
    username = os.environ.get('POSTGRES_USERNAME')
    username = 'postgres'
    password = os.environ.get('POSTGRES_PASSWORD')
    host = os.environ.get('POSTGRES_HOST')
    port = os.environ.get('POSTGRES_PORT')
    database = os.environ.get('POSTGRES_DB')

    query = f"SELECT * FROM {table_name}"
    engine = create_engine(f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}")

    with engine.connect() as conn:        
        rows = conn.execute(text(query))
        rows = rows.fetchall()
        df = pd.DataFrame(rows)
    
    return df

def format_dataframe(df):
    """
    Format column names for visuality.
    """
    columns = []

    for col in df.columns[:-7]:
        col = col.replace("entity.", "")  # remove redundant prefix
        col = re.sub(r'\.addressLines\.(\d+)', r' → Address Line \1', col)
        col = col.replace(".", " → ")  # convert dots to arrows
        col = re.sub(r'([a-z])([A-Z])', r'\1 \2', col)  # split camelCase
        col = col.replace("→ ", "→ ")  # clean spacing
        col = col.title()
        col = col.replace("Lei", "LEI")  # remove redundant prefix
        columns.append(col)

    columns.extend(df.columns[-7:])
    df.columns=columns
    return df

def get_display_name(row):
    """Extract preferred name (fallback if null)"""
    name = 'Legal Name → Name'
    en_name = 'Transliterated Other Names → 1 → Name'
    return row[en_name] if pd.notna(row[en_name]) else row[name]

def iso2_to_iso3(code):
    """ Convert ISO-2 to ISO-3 """
    try:
        return pycountry.countries.get(alpha_2=code).alpha_3
    except:
        return None