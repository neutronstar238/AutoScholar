"""
数据迁移脚本 - 已废弃

注意：本项目已迁移到本地文件存储（CSV），不再使用SQL数据库。
此脚本保留仅用于参考。

如需初始化本地存储，请运行：
python backend/test_local_storage.py
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """主函数"""
    print("⚠️  数据库迁移脚本已废弃")
    print("本项目已迁移到本地文件存储（CSV）")
    print("数据存储位置: backend/data/")
    print("如需测试本地存储，请运行: python backend/test_local_storage.py")


if __name__ == "__main__":
    main()
