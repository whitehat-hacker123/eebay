"""
순차 처리 엔진
계정을 순차적으로 처리하여 로그인, 출금, 로그아웃을 수행합니다.
"""
import time
import undetected_chromedriver as uc
from typing import List, Dict
from account_manager import AccountManager
from proxy_manager import ProxyManager
from browser_automation import BrowserAutomation
from withdrawal_handler import WithdrawalHandler
from captcha_solver import CaptchaSolver
from logger import Logger


class AccountProcessor:
    def __init__(
        self,
        account_manager: AccountManager,
        proxy_manager: ProxyManager,
        captcha_solver: CaptchaSolver,
        config: Dict
    ):
        """
        Args:
            account_manager: AccountManager 인스턴스
            proxy_manager: ProxyManager 인스턴스
            captcha_solver: CaptchaSolver 인스턴스
            config: 설정 딕셔너리
        """
        self.account_manager = account_manager
        self.proxy_manager = proxy_manager
        self.captcha_solver = captcha_solver
        self.config = config
        self.logger = Logger()
        self.driver = None
    
    def start(self):
        """브라우저를 시작합니다."""
        try:
            options = uc.ChromeOptions()
            
            # 헤드리스 모드 설정
            if self.config.get('headless', False):
                options.add_argument('--headless=new')
            
            # 탐지 회피를 위한 추가 옵션
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # User-Agent 설정
            user_agent = self.config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            options.add_argument(f'user-agent={user_agent}')
            
            # 창 크기 설정
            options.add_argument('--window-size=1920,1080')
            
            # undetected-chromedriver로 드라이버 생성
            self.driver = uc.Chrome(options=options, version_main=None)
            
            # 탐지 회피 스크립트 주입
            self.driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                '''
            })
            
            print("브라우저 시작 완료")
        
        except Exception as e:
            print(f"브라우저 시작 중 오류: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def stop(self):
        """브라우저를 종료합니다."""
        try:
            if self.driver:
                self.driver.quit()
                print("브라우저 종료 완료")
        except Exception as e:
            print(f"브라우저 종료 중 오류: {e}")
    
    def process_all_accounts(self) -> Dict:
        """
        모든 계정을 순차적으로 처리합니다.
        
        Returns:
            처리 결과 통계
        """
        accounts = self.account_manager.get_accounts()
        if not accounts:
            print("처리할 계정이 없습니다.")
            return {
                "total": 0,
                "success": 0,
                "failed": 0,
                "skipped": 0,
                "total_withdrawn": 0.0
            }
        
        stats = {
            "total": len(accounts),
            "success": 0,
            "failed": 0,
            "skipped": 0,
            "total_withdrawn": 0.0,
            "results": []
        }
        
        destination_wallet = self.config.get('destination_wallet', '')
        if not destination_wallet:
            print("경고: 목적 지갑 주소가 설정되지 않았습니다.")
        
        delay = self.config.get('delay_between_accounts', 5)
        retry_count = self.config.get('retry_count', 3)
        
        for idx, account in enumerate(accounts, 1):
            # 계정 정보 추출 (user/pass 또는 email/password 형식 지원)
            username = account.get('user') or account.get('email') or account.get('username', '')
            password = account.get('pass') or account.get('password', '')
            
            if not username or not password:
                print(f"계정 {idx}: 사용자명 또는 비밀번호가 없습니다. 스킵합니다.")
                stats["skipped"] += 1
                continue
            
            print(f"\n{'='*60}")
            print(f"계정 {idx}/{len(accounts)} 처리 중: {username}")
            print(f"{'='*60}")
            
            result = self._process_account(
                username,
                password,
                destination_wallet,
                retry_count
            )
            
            stats["results"].append(result)
            
            if result.get("skipped", False):
                stats["skipped"] += 1
            elif result["success"]:
                stats["success"] += 1
                stats["total_withdrawn"] += result.get("withdrawn_amount", 0.0)
            else:
                stats["failed"] += 1
            
            # 마지막 계정이 아니면 대기
            if idx < len(accounts):
                print(f"\n다음 계정 처리 전 {delay}초 대기 중...")
                time.sleep(delay)
        
        return stats
    
    def _process_account(
        self,
        username: str,
        password: str,
        destination_wallet: str,
        retry_count: int
    ) -> Dict:
        """
        단일 계정을 처리합니다.
        
        Returns:
            처리 결과 딕셔너리
        """
        result = {
            "username": username,
            "success": False,
            "skipped": False,
            "login_success": False,
            "withdrawal_success": False,
            "withdrawn_amount": 0.0,
            "balance": 0.0,
            "error": ""
        }
        
        for attempt in range(1, retry_count + 1):
            try:
                print(f"\n시도 {attempt}/{retry_count}")
                
                # 프록시 설정
                proxy = self.proxy_manager.get_next_proxy()
                if proxy and self.driver:
                    # 프록시는 undetected-chromedriver에서 직접 지원하지 않으므로
                    # ChromeOptions에 추가해야 함 (재시작 필요)
                    # 여기서는 프록시가 있으면 알림만 표시
                    print(f"프록시 사용: {proxy['server']} (참고: 프록시는 드라이버 재시작 시 적용)")
                
                # 브라우저 자동화 및 출금 처리
                browser_automation = BrowserAutomation(self.driver, self.captcha_solver)
                withdrawal_handler = WithdrawalHandler(self.driver)
                
                # 로그인
                login_success = browser_automation.login(username, password)
                result["login_success"] = login_success
                
                if not login_success:
                    result["error"] = "로그인 실패"
                    self.logger.log_account(
                        username, False, 0.0, "로그인 실패",
                        login_success=False, withdrawal_success=False, balance=0.0
                    )
                    time.sleep(2)
                    continue
                
                print("로그인 성공")
                time.sleep(3)  # 로그인 후 대기
                
                # 잔액 확인
                balance = withdrawal_handler.check_balance()
                result["balance"] = balance if balance else 0.0
                
                if balance is None or balance <= 0:
                    result["error"] = "출금 가능한 잔액이 없습니다."
                    result["success"] = True  # 로그인은 성공했으므로
                    result["skipped"] = True
                    self.logger.log_account(
                        username, True, 0.0, "잔액 없음",
                        login_success=True, withdrawal_success=False, balance=0.0
                    )
                    browser_automation.logout()
                    break
                
                print(f"계정 잔액: {balance}")
                
                # 출금 조건 확인
                if not withdrawal_handler.should_withdraw(balance, self.config):
                    result["error"] = "출금 조건을 만족하지 않습니다."
                    result["success"] = True  # 조건 불만족은 성공으로 간주 (스킵)
                    result["skipped"] = True
                    self.logger.log_account(
                        username, True, 0.0, result["error"],
                        login_success=True, withdrawal_success=False, balance=balance
                    )
                    browser_automation.logout()
                    break
                
                # 출금 처리
                withdrawal_result = withdrawal_handler.process_withdrawal(
                    destination_wallet,
                    amount=None,  # 전체 잔액 출금
                    config=self.config
                )
                
                result["withdrawal_success"] = withdrawal_result["success"]
                result["withdrawn_amount"] = withdrawal_result.get("amount", 0.0)
                
                if withdrawal_result["success"]:
                    result["success"] = True
                    result["error"] = ""
                    print(f"출금 성공: {result['withdrawn_amount']}")
                    self.logger.log_account(
                        username,
                        True,
                        result["withdrawn_amount"],
                        "출금 성공",
                        login_success=True,
                        withdrawal_success=True,
                        balance=balance
                    )
                else:
                    result["error"] = withdrawal_result.get("message", "출금 실패")
                    print(f"출금 실패: {result['error']}")
                    self.logger.log_account(
                        username,
                        False,
                        0.0,
                        result["error"],
                        login_success=True,
                        withdrawal_success=False,
                        balance=balance
                    )
                
                # 로그아웃
                browser_automation.logout()
                time.sleep(2)
                
                # 성공하면 재시도 중단
                if result["success"]:
                    break
                
            except Exception as e:
                result["error"] = f"처리 중 오류: {str(e)}"
                print(f"계정 처리 중 오류: {e}")
                import traceback
                traceback.print_exc()
                self.logger.log_account(
                    username, False, 0.0, str(e),
                    login_success=False, withdrawal_success=False, balance=0.0
                )
                time.sleep(2)
        
        return result
