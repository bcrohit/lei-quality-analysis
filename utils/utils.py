import os
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