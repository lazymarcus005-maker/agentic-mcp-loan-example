FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY agenticai_v2 ./agenticai_v2
COPY prompts ./prompts
COPY static ./static
COPY templates ./templates
COPY assets ./assets

RUN pip install --no-cache-dir .

ENV SYSTEM_PROMPT_PATH=/app/prompts/system_prompt.md

EXPOSE 80

CMD ["agenticai-v2"]
