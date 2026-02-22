FROM python:3.12-slim

# 使用国内镜像源
RUN pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple

WORKDIR /app

# 使用国内镜像源安装依赖
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

EXPOSE 8000

CMD ["python3", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
