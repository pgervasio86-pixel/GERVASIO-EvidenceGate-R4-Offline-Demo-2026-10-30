FROM python:3.12-slim
WORKDIR /app
COPY src ./src
COPY web ./web
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8765
ENV HOST=0.0.0.0
EXPOSE 8765
# Public deployment requires owner-authorized API access, cost control and security review.
CMD ["python", "src/server.py"]
