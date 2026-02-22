#!/usr/bin/env python3
"""
AutoScholar 修复验证脚本
检查所有修复是否正确应用
"""

import os
import sys
from pathlib import Path

def check_file_exists(filepath, description):
    """检查文件是否存在"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: {filepath} 不存在")
        return False

def check_file_contains(filepath, text, description):
    """检查文件是否包含特定文本"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if text in content:
                print(f"✅ {description}")
                return True
            else:
                print(f"❌ {description}: 未找到 '{text[:50]}...'")
                return False
    except Exception as e:
        print(f"❌ {description}: 读取文件失败 - {e}")
        return False

def main():
    print("=" * 60)
    print("AutoScholar 修复验证")
    print("=" * 60)
    print()
    
    checks = []
    
    # 1. 检查关键文件存在
    print("📁 检查文件存在性...")
    checks.append(check_file_exists(".env", ".env 配置文件"))
    checks.append(check_file_exists("frontend/src/pages/User.vue", "User.vue 页面"))
    checks.append(check_file_exists("QUICKSTART.md", "快速启动指南"))
    checks.append(check_file_exists("DEBUG_CHECKLIST.md", "调试检查清单"))
    print()
    
    # 2. 检查前端修复
    print("🎨 检查前端修复...")
    checks.append(check_file_contains(
        "frontend/src/main.js",
        "import router from './router'",
        "main.js 导入 router"
    ))
    checks.append(check_file_contains(
        "frontend/src/main.js",
        "app.use(router)",
        "main.js 使用 router"
    ))
    checks.append(check_file_contains(
        "frontend/src/main.js",
        "axios.defaults.baseURL",
        "main.js 配置 axios baseURL"
    ))
    checks.append(check_file_contains(
        "frontend/src/App.vue",
        "<router-view />",
        "App.vue 包含 router-view"
    ))
    checks.append(check_file_contains(
        "frontend/src/App.vue",
        "<el-menu",
        "App.vue 包含导航菜单"
    ))
    checks.append(check_file_contains(
        "frontend/package.json",
        '"marked"',
        "package.json 包含 marked 依赖"
    ))
    checks.append(check_file_contains(
        "frontend/vite.config.js",
        "port: 5173",
        "vite.config.js 使用正确端口"
    ))
    print()
    
    # 3. 检查后端修复
    print("⚙️  检查后端修复...")
    checks.append(check_file_contains(
        "backend/app/memory/database.py",
        "await init_db()",
        "database.py 实现初始化函数"
    ))
    checks.append(check_file_contains(
        "backend/app/api/notes.py",
        "await researcher.execute",
        "notes.py 实现笔记生成"
    ))
    checks.append(check_file_contains(
        "backend/app/models/base.py",
        "async def init_db():",
        "base.py 包含 init_db 函数"
    ))
    checks.append(check_file_contains(
        "backend/app/utils/config.py",
        "http://localhost:5173",
        "config.py 使用正确的前端 URL"
    ))
    print()
    
    # 4. 统计结果
    print("=" * 60)
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"检查完成: {passed}/{total} 通过 ({percentage:.1f}%)")
    
    if passed == total:
        print("🎉 所有检查通过！代码已成功修复。")
        return 0
    else:
        print(f"⚠️  有 {total - passed} 项检查未通过，请检查上述错误。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
