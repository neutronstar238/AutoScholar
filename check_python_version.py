#!/usr/bin/env python3
"""
检查 Python 版本是否符合要求
"""

import sys

def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    
    print(f"当前 Python 版本: {version.major}.{version.minor}.{version.micro}")
    print()
    
    # 检查版本范围
    if version.major == 3 and 10 <= version.minor <= 13:
        print("✅ Python 版本符合要求 (3.10-3.13)")
        
        if version.minor == 11:
            print("🎉 推荐版本 Python 3.11，完美！")
        else:
            print(f"💡 提示：推荐使用 Python 3.11 以获得最佳兼容性")
        
        return True
    else:
        print("❌ Python 版本不符合要求")
        print()
        print("要求：Python 3.10-3.13 (推荐 3.11)")
        print()
        
        if version.major == 3 and version.minor >= 14:
            print("⚠️  您使用的是 Python 3.14+")
            print("   部分依赖库（crewai, langgraph）尚未支持 Python 3.14")
            print()
        
        print("解决方案：")
        print("1. 安装 Python 3.11：https://www.python.org/downloads/")
        print("2. 使用 pyenv 管理多个 Python 版本")
        print("3. 创建虚拟环境时指定 Python 版本：")
        print("   python3.11 -m venv .venv")
        print()
        
        return False

if __name__ == "__main__":
    if check_python_version():
        sys.exit(0)
    else:
        sys.exit(1)
