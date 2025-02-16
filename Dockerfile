FROM python:3.10-slim-buster

WORKDIR /app

RUN python -m pip install --upgrade pip

COPY requirements.txt /app/.
RUN python -m pip install -r requirements.txt

COPY . /app

EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "data-evaluator-ui.py", "--server.port=8501", "--server.address=0.0.0.0"]
