FROM python:3.12.0-alpine3.18 as base

FROM base as pip
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir --prefix=/install -r /requirements.txt \
    && python3 -c "import compileall; compileall.compile_path(maxlevels=10)"

FROM base as app
WORKDIR /app
COPY . .
RUN python3 -m compileall retraktarr.py api/

FROM base as final
WORKDIR /app
COPY --from=pip /install /usr/local
COPY --from=app /app .
ENTRYPOINT ["python3", "retraktarr.py"]
