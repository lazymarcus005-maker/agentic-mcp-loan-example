from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def get_connection_string() -> str:
    server = os.environ["MSSQL_SERVER"]
    database = os.environ.get("MSSQL_DATABASE", "LoanDataDB")
    user = os.environ.get("MSSQL_USER")
    password = os.environ.get("MSSQL_PASSWORD")
    driver = os.environ.get("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server")
    encrypt = os.environ.get("MSSQL_ENCRYPT", "yes")
    trust_cert = os.environ.get("MSSQL_TRUST_SERVER_CERTIFICATE", "yes")

    auth = f"UID={user};PWD={password}" if user and password else "Trusted_Connection=yes"

    return (
        f"DRIVER={{{driver}}};SERVER={server};DATABASE={database};"
        f"{auth};Encrypt={encrypt};TrustServerCertificate={trust_cert}"
    )


def get_mcp_host() -> str:
    return os.environ.get("MCP_HOST", "0.0.0.0")


def get_mcp_port() -> int:
    return int(os.environ.get("MCP_PORT", "8080"))
