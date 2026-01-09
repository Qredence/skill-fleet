# Build Stage
# FROM python:3.11-slim as builder
# WORKDIR /app
# COPY requirements.txt .
# RUN apt-get update && apt-get install -y gcc && pip install --user -r requirements.txt
#
# Final Stage
# FROM python:3.11-slim
# WORKDIR /app
# COPY --from=builder /root/.local /root/.local
# COPY . .
# ENV PATH=/root/.local/bin:$PATH
# USER 1000
# CMD ["python", "app.py"]