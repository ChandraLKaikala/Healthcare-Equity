"""
Custom Databricks SQL client - Direct HTTP API, NO OAuth, NO SDK imports
"""
import os
import requests
import json
from typing import List, Tuple
from dotenv import load_dotenv

# Load credentials
env_path = os.path.join(os.path.dirname(__file__), '.env.databricks')
load_dotenv(env_path)

HOST = os.getenv('DATABRICKS_HOST')
TOKEN = os.getenv('DATABRICKS_TOKEN')
HTTP_PATH = os.getenv('DATABRICKS_HTTP_PATH')


class DatabricksCursor:
    """Cursor-like object for Databricks HTTP API"""

    def __init__(self, conn):
        self.conn = conn
        self._results = []
        self._columns = []
        self.description = None
        self._index = 0

    def execute(self, query: str):
        """Execute query via Databricks SQL API"""
        headers = {
            "Authorization": f"Bearer {self.conn.token}",
            "Content-Type": "application/json"
        }

        payload = {
            "statement": query,
            "warehouse_id": self.conn.warehouse_id,
            "wait_timeout": "10s"
        }

        try:
            response = requests.post(
                self.conn.base_url,
                json=payload,
                headers=headers,
                timeout=60,
                verify=True
            )

            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}: {response.text[:200]}")

            result = response.json()

            # Parse Databricks API response
            # Columns are in manifest.schema.columns
            if "manifest" in result and "schema" in result["manifest"]:
                schema = result["manifest"]["schema"]
                if "columns" in schema:
                    cols = schema["columns"]
                    self._columns = [col.get("name", f"col_{i}") for i, col in enumerate(cols)]
                    self.description = [(name,) for name in self._columns]
                else:
                    self.description = []
            else:
                self.description = []

            # Extract data rows from result
            if "result" in result and "data_array" in result["result"]:
                self._results = result["result"]["data_array"]
            else:
                self._results = []

            self._index = 0
            return self

        except Exception as e:
            # Make error info available
            raise Exception(f"Databricks query error: {str(e)[:300]}")

    def fetchone(self):
        """Return first row"""
        if self._index < len(self._results):
            row = self._results[self._index]
            self._index += 1
            return tuple(row) if isinstance(row, list) else row
        return None

    def fetchall(self):
        """Return all rows"""
        results = []
        while self._index < len(self._results):
            row = self._results[self._index]
            results.append(tuple(row) if isinstance(row, list) else row)
            self._index += 1
        return results

    def close(self):
        """Cleanup"""
        pass


class DatabricksConnection:
    """Databricks connection using HTTP API directly - NO SDK = NO OAUTH"""

    def __init__(self):
        if not TOKEN or not HOST or not HTTP_PATH:
            raise Exception("Missing Databricks credentials in .env.databricks")

        self.host = HOST.replace('https://', '').rstrip('/')
        self.token = TOKEN
        self.http_path = HTTP_PATH.rstrip('/')
        self.base_url = f"https://{self.host}/api/2.0/sql/statements"
        self.warehouse_id = self._extract_warehouse_id()

    def _extract_warehouse_id(self):
        """Extract warehouse ID from HTTP path like /sql/1.0/warehouses/abc123"""
        parts = self.http_path.split('/')
        return parts[-1] if parts else None

    def cursor(self):
        """Return cursor object"""
        return DatabricksCursor(self)

    def close(self):
        """Cleanup"""
        pass


def get_databricks_connection():
    """Factory function - returns connection"""
    return DatabricksConnection()
