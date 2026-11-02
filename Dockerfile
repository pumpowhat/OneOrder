FROM python:3.12-slim

# Ngăn Python tạo bytecode và bật chế độ xuất log trực tiếp
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Cài đặt curl để phục vụ HEALTHCHECK
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Tạo người dùng non-root
RUN useradd -m -u 1000 appuser

# Sao chép và cài đặt requirements trước để tận dụng layer cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn ứng dụng
COPY . .

# Tạo thư mục lưu database SQLite và phân quyền cho appuser
RUN mkdir -p /app/db && chown -R appuser:appuser /app

# Chuyển sang người dùng non-root
USER appuser

# Khai báo cổng dịch vụ
EXPOSE 8000

# HEALTHCHECK gọi GET /api/health
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Khởi chạy dịch vụ FastAPI
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
