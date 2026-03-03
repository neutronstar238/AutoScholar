"""运行P0阶段所有测试的脚本"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, description):
    """运行命令并显示结果"""
    print(f"\n{'='*60}")
    print(f"🧪 {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    
    if result.returncode != 0:
        print(f"❌ {description} 失败")
        return False
    else:
        print(f"✅ {description} 通过")
        return True

def main():
    """主函数"""
    print("🚀 开始运行P0阶段完整测试套件")
    print(f"📁 工作目录: {Path.cwd()}")
    
    tests = [
        ("python test_local_storage.py", "本地存储基础功能测试"),
        ("pytest tests/test_cache_manager_properties.py -v", "缓存管理器属性测试"),
        ("pytest tests/test_search_engine_properties.py -v", "搜索引擎属性测试"),
        ("pytest tests/test_keyword_expander_properties.py -v", "关键词扩展器属性测试"),
        ("pytest tests/test_trending_manager_local.py -v", "热门论文管理器测试"),
        ("pytest tests/test_user_profile_manager_local.py -v", "用户画像管理器测试"),
    ]
    
    results = []
    for cmd, desc in tests:
        success = run_command(cmd, desc)
        results.append((desc, success))
    
    # 打印总结
    print(f"\n{'='*60}")
    print("📊 测试结果总结")
    print(f"{'='*60}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for desc, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {desc}")
    
    print(f"\n{'='*60}")
    print(f"总计: {passed}/{total} 测试套件通过")
    print(f"{'='*60}")
    
    if passed == total:
        print("\n🎉 恭喜！P0阶段所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试套件失败，请检查")
        return 1

if __name__ == "__main__":
    sys.exit(main())
