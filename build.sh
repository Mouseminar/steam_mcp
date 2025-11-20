#!/bin/bash
# 构建脚本 - 安装依赖到正确的位置

set -e

echo "========================================="
echo "📦 开始安装依赖"
echo "========================================="
echo "当前目录: $(pwd)"
echo "Python 版本: $(python --version)"
echo "Pip 版本: $(pip --version)"
echo "========================================="

# 创建 python 依赖目录
mkdir -p python

# 安装依赖到 python 目录
echo "安装依赖到 ./python 目录..."
pip install -r requirements.txt -t python --upgrade

echo "========================================="
echo "✓ 依赖安装完成"
echo "========================================="
echo "python 目录内容:"
ls -la python/ | head -20
echo "========================================="
