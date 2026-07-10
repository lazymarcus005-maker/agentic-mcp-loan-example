from __future__ import annotations

from typing import Any

import pyodbc


class SqlRunner:
    """Executes read-only stored procedures against LoanDataDB and returns plain dict rows."""

    def __init__(self, connection_string: str) -> None:
        self._connection_string = connection_string

    def run_procedure(self, procedure_name: str, params: dict[str, Any] | None = None) -> Any:
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        placeholders = ", ".join(f"@{key}=?" for key in clean_params)
        sql = f"EXEC {procedure_name} {placeholders}".strip()

        with pyodbc.connect(self._connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, list(clean_params.values()))

            result_sets = [self._fetch_current(cursor)]
            while cursor.nextset():
                result_sets.append(self._fetch_current(cursor))

        return result_sets[0] if len(result_sets) == 1 else result_sets

    @staticmethod
    def _fetch_current(cursor: pyodbc.Cursor) -> list[dict[str, Any]]:
        if cursor.description is None:
            return []
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]
