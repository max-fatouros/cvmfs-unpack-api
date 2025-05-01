FROM python:3.10

COPY . unpack-api/
WORKDIR unpack-api

RUN pip install --upgrade pip &&\
    pip install .

EXPOSE 8000

CMD ["fastapi", "run", "unpack_api/main.py"]
