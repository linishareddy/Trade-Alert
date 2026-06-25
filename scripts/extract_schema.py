import asyncio
import json
import os
import ssl
import sys

# Add the backend directory to sys.path to allow importing from config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

# Import settings to get the DB connection string and SSL settings
from config.settings import settings


def _build_connect_args() -> dict:
    if not settings.DB_SSL:
        return {}
    if settings.DB_SSL_CA_FILE:
        ctx = ssl.create_default_context(cafile=settings.DB_SSL_CA_FILE)
    else:
        # Aiven-managed Postgres; skip CA verify when no ca.pem path is configured
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    return {"ssl": ctx}


async def extract_schema():
    print(f"Connecting to database: {settings.DATABASE_URL.split('@')[-1]}")
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        connect_args=_build_connect_args(),
    )
    
    schema_info = {"tables": []}
    
    def inspect_db(conn):
        inspector = inspect(conn)
        tables = inspector.get_table_names(schema="public")
        
        for table in tables:
            try:
                table_comment = inspector.get_table_comment(table, schema="public")
                table_desc = table_comment.get("text")
            except NotImplementedError:
                table_desc = None
                
            table_info = {
                "name": table,
                "description": table_desc,
                "columns": [],
                "primary_keys": [],
                "foreign_keys": [],
                "indexes": []
            }
            
            # Extract columns
            for col in inspector.get_columns(table, schema="public"):
                table_info["columns"].append({
                    "name": col["name"],
                    "description": col.get("comment"),
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": col.get("default")
                })
            
            # Extract primary keys
            pk_constraint = inspector.get_pk_constraint(table, schema="public")
            if pk_constraint and "constrained_columns" in pk_constraint:
                table_info["primary_keys"] = pk_constraint["constrained_columns"]
                
            # Extract foreign keys
            for fk in inspector.get_foreign_keys(table, schema="public"):
                table_info["foreign_keys"].append({
                    "name": fk["name"],
                    "constrained_columns": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"]
                })
                
            # Extract indexes
            for idx in inspector.get_indexes(table, schema="public"):
                table_info["indexes"].append({
                    "name": idx["name"],
                    "column_names": idx["column_names"],
                    "unique": idx["unique"]
                })
                
            schema_info["tables"].append(table_info)

    try:
        async with engine.connect() as conn:
            print("Inspecting public schema...")
            await conn.run_sync(inspect_db)
            
        output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.json")
        with open(output_file, "w") as f:
            json.dump(schema_info, f, indent=4)
            
        print(f"Schema successfully extracted and saved to: {output_file}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(extract_schema())
