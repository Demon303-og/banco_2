FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
# OpenShift ejecuta con UID aleatorio y GID 0
RUN chgrp -R 0 /app && chmod -R g=u /app
USER 1001
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
