#!/usr/bin/env python3
"""
免费代理查找和测试工具
Free Proxy Finder and Tester Tool
"""

import requests
import time
import random
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

class ProxyFinder:
    def __init__(self):
        self.working_proxies = []
        self.tested_count = 0
        self.lock = threading.Lock()
        
    def get_free_proxy_list(self):
        """获取免费代理列表"""
        print("🔍 获取免费代理列表...")
        
        # 这里包含一些常见的免费代理，实际使用时可能需要更新
        proxy_list = [
            "http://103.152.112.145:80",
            "http://139.59.1.14:3128",
            "http://20.111.54.16:80",
            "http://103.149.162.194:80",
            "http://177.93.44.54:999",
            "http://103.78.27.246:8080",
            "http://202.43.190.11:8118",
            "http://103.155.166.94:8181",
            "http://103.155.166.95:8181",
            "http://103.155.166.85:8181",
            "http://43.132.166.30:8118",
            "http://194.195.213.197:1080",
            "http://45.167.125.97:9992",
            "http://103.155.166.90:8181",
            "http://185.82.96.77:9091",
            "http://103.155.166.89:8181",
            "http://103.155.166.88:8181",
            "http://103.78.27.38:8080",
            "http://181.78.16.237:8080",
            "http://103.155.166.87:8181",
        ]
        
        print(f"📋 获取到 {len(proxy_list)} 个代理地址")
        return proxy_list
    
    def test_proxy(self, proxy_url, timeout=10):
        """测试单个代理是否可用"""
        try:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # 测试HTTP请求
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            if response.status_code == 200:
                result = response.json()
                original_ip = result.get('origin', 'Unknown')
                
                # 获取响应时间
                response_time = response.elapsed.total_seconds()
                
                with self.lock:
                    self.tested_count += 1
                    print(f"✅ [{self.tested_count}] 代理可用: {proxy_url}")
                    print(f"   IP: {original_ip}")
                    print(f"   响应时间: {response_time:.2f}秒")
                
                return {
                    'proxy': proxy_url,
                    'status': 'working',
                    'ip': original_ip,
                    'response_time': response_time,
                    'test_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
            else:
                with self.lock:
                    self.tested_count += 1
                    print(f"❌ [{self.tested_count}] 代理响应错误: {proxy_url} (状态码: {response.status_code})")
                
        except requests.exceptions.Timeout:
            with self.lock:
                self.tested_count += 1
                print(f"⏰ [{self.tested_count}] 代理超时: {proxy_url}")
        except requests.exceptions.ConnectionError:
            with self.lock:
                self.tested_count += 1
                print(f"🔌 [{self.tested_count}] 连接失败: {proxy_url}")
        except Exception as e:
            with self.lock:
                self.tested_count += 1
                print(f"❓ [{self.tested_count}] 未知错误: {proxy_url} - {str(e)}")
        
        return None
    
    def find_working_proxies(self, max_workers=20, timeout=10):
        """并发测试所有代理"""
        proxy_list = self.get_free_proxy_list()
        working_proxies = []
        
        print(f"\n🧪 开始测试代理 (并发数: {max_workers}, 超时: {timeout}秒)")
        print("=" * 60)
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_proxy = {
                executor.submit(self.test_proxy, proxy, timeout): proxy 
                for proxy in proxy_list
            }
            
            # 收集结果
            for future in as_completed(future_to_proxy):
                result = future.result()
                if result:
                    working_proxies.append(result)
        
        end_time = time.time()
        test_duration = end_time - start_time
        
        print("=" * 60)
        print(f"🏁 测试完成！耗时: {test_duration:.1f}秒")
        print(f"📊 测试总数: {len(proxy_list)}")
        print(f"✅ 可用代理: {len(working_proxies)}")
        print(f"📈 成功率: {len(working_proxies)/len(proxy_list)*100:.1f}%")
        
        return working_proxies
    
    def save_working_proxies(self, proxies, filename='working_proxies.txt'):
        """保存可用代理到文件"""
        if not proxies:
            print("❌ 没有可用代理需要保存")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# 可用代理列表 - 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 总计: {len(proxies)} 个代理\n\n")
            
            for proxy in sorted(proxies, key=lambda x: x['response_time']):
                f.write(f"# IP: {proxy['ip']} | 响应时间: {proxy['response_time']:.2f}秒\n")
                f.write(f"{proxy['proxy']}\n\n")
        
        print(f"💾 已保存 {len(proxies)} 个可用代理到: {filename}")
    
    def test_yfinance_with_proxy(self, proxy_url):
        """测试代理是否能访问Yahoo Finance"""
        try:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
            
            # 尝试访问Yahoo Finance
            response = requests.get(
                'https://finance.yahoo.com/',
                proxies=proxies,
                timeout=15,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            
            if response.status_code == 200:
                print(f"✅ 代理可以访问Yahoo Finance: {proxy_url}")
                return True
            else:
                print(f"❌ 代理无法访问Yahoo Finance: {proxy_url} (状态码: {response.status_code})")
                return False
                
        except Exception as e:
            print(f"❌ 测试Yahoo Finance访问失败: {proxy_url} - {str(e)}")
            return False

def main():
    """主函数"""
    print("🚀 免费代理查找器")
    print("=" * 50)
    print("注意: 免费代理通常不稳定，仅用于测试目的")
    print("生产环境建议使用付费代理服务")
    print()
    
    finder = ProxyFinder()
    
    # 查找可用代理
    working_proxies = finder.find_working_proxies(max_workers=15, timeout=8)
    
    if working_proxies:
        print("\n🎉 找到可用代理:")
        print("-" * 50)
        
        # 按响应时间排序
        working_proxies.sort(key=lambda x: x['response_time'])
        
        for i, proxy in enumerate(working_proxies[:5], 1):  # 显示前5个最快的
            print(f"{i}. {proxy['proxy']}")
            print(f"   IP: {proxy['ip']}")
            print(f"   响应时间: {proxy['response_time']:.2f}秒")
            print()
        
        # 保存到文件
        finder.save_working_proxies(working_proxies)
        
        # 测试最快的代理是否能访问Yahoo Finance
        if working_proxies:
            print("🧪 测试最快代理访问Yahoo Finance...")
            fastest_proxy = working_proxies[0]['proxy']
            finder.test_yfinance_with_proxy(fastest_proxy)
        
        print("\n💡 使用方法:")
        print("export YFINANCE_PROXY_HTTP=\"" + working_proxies[0]['proxy'] + "\"")
        print("export YFINANCE_PROXY_HTTPS=\"" + working_proxies[0]['proxy'] + "\"")
        
    else:
        print("\n😞 没有找到可用的免费代理")
        print("\n🛡️ 替代方案:")
        print("1. 使用我们的速率限制功能（推荐）")
        print("2. 购买付费代理服务")
        print("3. 使用VPN服务")
        print("4. 在云服务器上部署程序")

def quick_test():
    """快速测试几个代理"""
    print("⚡ 快速代理测试")
    print("-" * 30)
    
    quick_list = [
        "http://103.152.112.145:80",
        "http://139.59.1.14:3128",
        "http://20.111.54.16:80",
    ]
    
    finder = ProxyFinder()
    working = []
    
    for proxy in quick_list:
        result = finder.test_proxy(proxy, timeout=5)
        if result:
            working.append(result)
            # 只测试第一个能用的
            break
    
    if working:
        best = working[0]
        print(f"\n🎯 推荐使用: {best['proxy']}")
        print("设置命令:")
        print(f"export YFINANCE_PROXY_HTTP=\"{best['proxy']}\"")
    else:
        print("\n❌ 快速测试没有找到可用代理")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        quick_test()
    else:
        main() 