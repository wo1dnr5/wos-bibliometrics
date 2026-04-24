FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bibliometrics_analysis.py .
COPY plot_annual_trend.py .
COPY savedrecs.txt .
COPY savedrecs-2.txt .
COPY savedrecs-3.txt .

VOLUME ["/app/output"]

CMD ["python", "bibliometrics_analysis.py"]
