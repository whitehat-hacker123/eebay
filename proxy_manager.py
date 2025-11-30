"""
프록시 관리 모듈
프록시 리스트를 관리하고 로테이션합니다.
"""
import random
import requests
from typing import List, Dict, Optional


class ProxyManager:
    def __init__(self, proxy_file: str):
        """
        Args:
            proxy_file: 프록시 리스트 파일 경로
        """
        self.proxy_file = proxy_file
        self.proxies: List[Dict[str, str]] = []
        self.current_index = 0
        self.failed_proxies = set()
    
    def load_proxies(self) -> List[Dict[str, str]]:
        """
        프록시 파일을 읽어서 파싱합니다.
        지원 형식:
        - ip:port
        - ip:port:username:password
        
        Returns:
            프록시 리스트 [{"server": "ip:port", "username": "...", "password": "..."}]
        """
        self.proxies = []
        
        try:
            with open(self.proxy_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(':')
                    if len(parts) < 2:
                        print(f"경고: {line_num}번째 줄 형식이 올바르지 않습니다: {line}")
                        continue
                    
                    proxy_dict = {
                        'server': f"{parts[0]}:{parts[1]}"
                    }
                    
                    # 인증 정보가 있는 경우
                    if len(parts) >= 4:
                        proxy_dict['username'] = parts[2]
                        proxy_dict['password'] = parts[3]
                    
                    self.proxies.append(proxy_dict)
            
            print(f"총 {len(self.proxies)}개의 프록시를 로드했습니다.")
            return self.proxies
        
        except FileNotFoundError:
            print(f"프록시 파일을 찾을 수 없습니다: {self.proxy_file}")
            return []
        except Exception as e:
            print(f"프록시 파일 로드 중 오류 발생: {e}")
            return []
    
    def get_next_proxy(self) -> Optional[Dict[str, str]]:
        """
        다음 프록시를 가져옵니다 (로테이션).
        
        Returns:
            프록시 딕셔너리 또는 None
        """
        if not self.proxies:
            return None
        
        # 실패한 프록시 제외하고 가져오기
        available_proxies = [p for p in self.proxies if p['server'] not in self.failed_proxies]
        
        if not available_proxies:
            # 모든 프록시가 실패한 경우 실패 목록 초기화
            print("모든 프록시가 실패했습니다. 실패 목록을 초기화합니다.")
            self.failed_proxies.clear()
            available_proxies = self.proxies
        
        # 순차적으로 또는 랜덤하게 선택
        proxy = available_proxies[self.current_index % len(available_proxies)]
        self.current_index += 1
        
        return proxy
    
    def get_random_proxy(self) -> Optional[Dict[str, str]]:
        """
        랜덤한 프록시를 가져옵니다.
        
        Returns:
            프록시 딕셔너리 또는 None
        """
        if not self.proxies:
            return None
        
        available_proxies = [p for p in self.proxies if p['server'] not in self.failed_proxies]
        
        if not available_proxies:
            self.failed_proxies.clear()
            available_proxies = self.proxies
        
        return random.choice(available_proxies)
    
    def mark_proxy_failed(self, proxy: Dict[str, str]):
        """프록시를 실패 목록에 추가합니다."""
        self.failed_proxies.add(proxy['server'])
        print(f"프록시 실패로 표시: {proxy['server']}")
    
    def verify_proxy(self, proxy: Dict[str, str], timeout: int = 10) -> bool:
        """
        프록시가 작동하는지 확인합니다.
        
        Args:
            proxy: 프록시 딕셔너리
            timeout: 타임아웃 (초)
        
        Returns:
            프록시가 작동하면 True
        """
        try:
            proxies = {
                'http': f"http://{proxy['server']}",
                'https': f"http://{proxy['server']}"
            }
            
            if 'username' in proxy and 'password' in proxy:
                proxies['http'] = f"http://{proxy['username']}:{proxy['password']}@{proxy['server']}"
                proxies['https'] = f"http://{proxy['username']}:{proxy['password']}@{proxy['server']}"
            
            response = requests.get(
                'http://httpbin.org/ip',
                proxies=proxies,
                timeout=timeout
            )
            
            return response.status_code == 200
        except:
            return False
    
    def get_proxy_count(self) -> int:
        """프록시 개수를 반환합니다."""
        return len(self.proxies)

