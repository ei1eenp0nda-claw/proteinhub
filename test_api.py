#!/usr/bin/env python3
"""
ProteinHub 快速测试脚本
验证核心功能是否正常工作
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def test_endpoint(method, endpoint, data=None, expected_status=200):
    """测试单个端点"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            return False, f"不支持的方法: {method}"
        
        if response.status_code == expected_status:
            return True, response.json() if response.content else None
        else:
            return False, f"状态码 {response.status_code}, 期望 {expected_status}"
    except requests.exceptions.ConnectionError:
        return False, "连接失败，服务可能未启动"
    except Exception as e:
        return False, str(e)

def main():
    print("🧪 ProteinHub 功能测试")
    print("=" * 50)
    
    tests = [
        ("GET", "/api/health", None, 200, "健康检查"),
        ("POST", "/api/init", None, 200, "初始化数据"),
        ("GET", "/api/proteins", None, 200, "获取蛋白列表"),
    ]
    
    passed = 0
    failed = 0
    
    for method, endpoint, data, expected, name in tests:
        print(f"\n测试: {name}")
        print(f"  {method} {endpoint}")
        
        success, result = test_endpoint(method, endpoint, data, expected)
        
        if success:
            print(f"  ✅ 通过")
            if result and 'count' in str(result):
                print(f"     返回数据: {result}")
            passed += 1
        else:
            print(f"  ❌ 失败: {result}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("\n🎉 所有测试通过！ProteinHub 运行正常。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查服务状态。")
        return 1

if __name__ == "__main__":
    sys.exit(main())
