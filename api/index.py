"""Vercel Serverless 入口"""
import sys
import os

# 将项目根目录加入 sys.path，让 Vercel 能找到 app/config/db 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402

# Vercel Python Runtime 会调用这个变量
# 必须命名为 `app`
