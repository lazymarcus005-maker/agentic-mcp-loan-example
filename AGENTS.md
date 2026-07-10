# Repository Guidelines

## Project Structure & Module Organization

This repository contains a Docker-composed loan Q&A system:

- `agenticai_v2/`: FastAPI chat app that connects an LLM to the MCP SQL service. Source lives in `agenticai_v2/agenticai_v2/`, templates in `templates/`, browser assets in `static/`, prompts in `prompts/`, and setup images in `assets/`.
- `mcp_mssql/`: Python MCP server exposing read-only loan query tools backed by SQL Server. Source lives in `mcp_mssql/mcp_mssql/`.
- `database/`: SQL Server container build files and `LoanDataDB.bak` restore asset.
- `docker-compose.yml`: runs SQL Server, the MCP service, and the web app.

## Build, Test, and Development Commands

- `docker compose up --build`: build and run the stack at `http://localhost:5082`.
- `docker compose down`: stop and remove stack containers.
- `cd agenticai_v2; pip install -e .`: install the chat app locally for development.
- `cd agenticai_v2; agenticai-v2`: run the chat app console script.
- `cd mcp_mssql; pip install -e .`: install the MCP server locally.
- `cd mcp_mssql; mcp-mssql-loan-query`: run the MCP server console script.

Create `agenticai_v2/.env` before running the composed app; include required LLM provider API keys and app settings.

## Coding Style & Naming Conventions

Use Python 3.11+ and PEP 8: 4-space indentation, `snake_case` for modules/functions/variables, `PascalCase` for classes, and uppercase constants. Keep configuration reads in `config.py`, service orchestration in `app.py` or `server.py`, and database execution in `sql_runner.py`. Keep frontend files split under `static/css/`, `static/js/`, and `templates/`.

## Testing Guidelines

No automated test suite is currently present. When adding tests, prefer `pytest`, place tests under package-local `tests/`, and name files `test_*.py`. Cover configuration parsing, SQL runner behavior, MCP tool responses, and FastAPI routes. Until tests exist, verify with `docker compose up --build` and manual chat queries against the restored loan database.

## Commit & Pull Request Guidelines

History uses Conventional Commit style, for example `feat: add ChatLoan web interface and settings page`. Continue using concise prefixes such as `feat:`, `fix:`, `docs:`, `test:`, and `chore:`.

Pull requests should include a summary, affected services, setup or migration notes, linked issues when applicable, and screenshots for UI changes. Note manual verification, especially Docker startup, database restore, and representative chat/MCP queries.

## Security & Configuration Tips

Do not commit `.env` files, API keys, or alternate database backups. Treat credentials in `docker-compose.yml` as local development defaults only, and override them before deploying outside a trusted local environment.
