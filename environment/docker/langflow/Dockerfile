ARG CUSTOM_LANGFLOW_IMG=fetest/langflow-fetest:tis
FROM ${CUSTOM_LANGFLOW_IMG}
ARG PYTHON_VERSION
ENV SRC=/app/.venv/lib/python${PYTHON_VERSION}/site-packages/langflow/

USER root
WORKDIR /app

RUN pip install --no-cache-dir psycopg2-binary

COPY ../environment/docker/langflow/src/api.v1.flows.py ${SRC}/api/v1/flows.py

COPY ../environment/docker/langflow/src/api.reload_router.py ${SRC}/api/reload_router.py
COPY ../environment/docker/langflow/src/api.schemas.py ${SRC}/api/schemas.py
COPY ../environment/docker/langflow/src/api.init.py ${SRC}/api/__init__.py

COPY ../environment/docker/langflow/src/main.py ${SRC}/main.py


USER user
