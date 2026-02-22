#!/bin/bash
# AutoScholar Linux 服务端安装脚本

echo "🚀 AutoScholar Linux 安装程序"
echo "================================"

# 检查 Docker
echo -e "\n📦 检查 Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ 未检测到 Docker，请先安装 Docker"
    exit 1
fi
echo "✅ Docker 已安装：$(docker --version)"

# 检查 Docker Compose
echo -e "\n📦 检查 Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 未检测到 Docker Compose，请先安装"
    exit 1
fi
echo "✅ Docker Compose 已安装：$(docker-compose --version)"

# 创建 .env 文件
echo -e "\n⚙️  创建配置文件..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ 配置文件已创建，请编辑 .env 文件"
else
    echo "✅ 配置文件已存在"
fi

# 创建数据目录
echo -e "\n📁 创建数据目录..."
mkdir -p data/postgres data/redis data/ollama
echo "✅ 数据目录已创建"

echo -e "\n✨ 安装完成！"
echo -e "\n📝 下一步:"
echo "1. 编辑 .env 文件"
echo "2. 运行 ./deploy/linux/start.sh 启动服务"
echo "3. 访问 http://your-server-ip:3000"
