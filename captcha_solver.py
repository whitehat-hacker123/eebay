"""
hCaptcha 처리 모듈
2captcha API를 사용하여 hCaptcha를 해결합니다.
"""
import time
import requests
from typing import Optional


class CaptchaSolver:
    def __init__(self, api_key: str):
        """
        Args:
            api_key: 2captcha API 키
        """
        self.api_key = api_key
        self.base_url = "http://2captcha.com"
    
    def solve_hcaptcha(self, site_key: str, page_url: str, timeout: int = 120) -> Optional[str]:
        """
        hCaptcha를 해결하고 토큰을 반환합니다.
        
        Args:
            site_key: hCaptcha 사이트 키
            page_url: 페이지 URL
            timeout: 최대 대기 시간 (초)
        
        Returns:
            hCaptcha 토큰 또는 None
        """
        # 1. 작업 생성
        task_id = self._create_task(site_key, page_url)
        if not task_id:
            return None
        
        # 2. 결과 대기
        token = self._wait_for_result(task_id, timeout)
        return token
    
    def _create_task(self, site_key: str, page_url: str) -> Optional[str]:
        """2captcha에 작업을 생성합니다."""
        try:
            url = f"{self.base_url}/in.php"
            params = {
                'key': self.api_key,
                'method': 'hcaptcha',
                'sitekey': site_key,
                'pageurl': page_url,
                'json': 1
            }
            
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if data.get('status') == 1:
                task_id = data.get('request')
                print(f"hCaptcha 작업 생성됨: {task_id}")
                return task_id
            else:
                error = data.get('request', 'Unknown error')
                print(f"hCaptcha 작업 생성 실패: {error}")
                return None
        
        except Exception as e:
            print(f"hCaptcha 작업 생성 중 오류: {e}")
            return None
    
    def _wait_for_result(self, task_id: str, timeout: int = 120) -> Optional[str]:
        """작업 결과를 대기합니다."""
        start_time = time.time()
        check_interval = 5  # 5초마다 확인
        
        while time.time() - start_time < timeout:
            try:
                url = f"{self.base_url}/res.php"
                params = {
                    'key': self.api_key,
                    'action': 'get',
                    'id': task_id,
                    'json': 1
                }
                
                response = requests.get(url, params=params, timeout=30)
                data = response.json()
                
                if data.get('status') == 1:
                    token = data.get('request')
                    print(f"hCaptcha 토큰 수신 성공")
                    return token
                elif data.get('request') == 'CAPCHA_NOT_READY':
                    # 아직 준비되지 않음, 대기
                    time.sleep(check_interval)
                    continue
                else:
                    error = data.get('request', 'Unknown error')
                    print(f"hCaptcha 결과 확인 실패: {error}")
                    return None
            
            except Exception as e:
                print(f"hCaptcha 결과 확인 중 오류: {e}")
                time.sleep(check_interval)
        
        print(f"hCaptcha 타임아웃: {timeout}초 초과")
        return None
    
    def get_balance(self) -> Optional[float]:
        """2captcha 계정 잔액을 확인합니다."""
        try:
            url = f"{self.base_url}/res.php"
            params = {
                'key': self.api_key,
                'action': 'getbalance',
                'json': 1
            }
            
            response = requests.get(url, params=params, timeout=30)
            data = response.json()
            
            if data.get('status') == 1:
                balance = float(data.get('request', 0))
                return balance
            else:
                return None
        
        except Exception as e:
            print(f"잔액 확인 중 오류: {e}")
            return None

