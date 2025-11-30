"""
순차 처리 엔진
계정을 순차적으로 처리하여 로그인, 출금, 로그아웃을 수행합니다.
"""
import time
from typing import List, Dict
from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page
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
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
    
    def start(self):
        """브라우저를 시작합니다."""
        self.playwright = sync_playwright().start()
        
        browser_type = self.config.get('browser', 'chromium')
        if browser_type == 'firefox':
            browser_launcher = self.playwright.firefox
        elif browser_type == 'webkit':
            browser_launcher = self.playwright.webkit
        else:
            browser_launcher = self.playwright.chromium
        
        self.browser = browser_launcher.launch(
            headless=self.config.get('headless', True)
        )
    
    def stop(self):
        """브라우저를 종료합니다."""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
    
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
                "total_withdrawn": 0.0
            }
        
        stats = {
            "total": len(accounts),
            "success": 0,
            "failed": 0,
            "total_withdrawn": 0.0,
            "results": []
        }
        
        destination_wallet = self.config.get('destination_wallet', '')
        if not destination_wallet:
            print("경고: 목적 지갑 주소가 설정되지 않았습니다.")
        
        delay = self.config.get('delay_between_accounts', 5)
        retry_count = self.config.get('retry_count', 3)
        
        for idx, account in enumerate(accounts, 1):
            email = account.get('email', '')
            password = account.get('password', '')
            
            print(f"\n{'='*60}")
            print(f"계정 {idx}/{len(accounts)} 처리 중: {email}")
            print(f"{'='*60}")
            
            result = self._process_account(
                email,
                password,
                destination_wallet,
                retry_count
            )
            
            stats["results"].append(result)
            
            if result["success"]:
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
        email: str,
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
            "email": email,
            "success": False,
            "login_success": False,
            "withdrawal_success": False,
            "withdrawn_amount": 0.0,
            "error": ""
        }
        
        for attempt in range(1, retry_count + 1):
            try:
                print(f"\n시도 {attempt}/{retry_count}")
                
                # 브라우저 컨텍스트 생성 (프록시 사용)
                proxy = self.proxy_manager.get_next_proxy()
                context_options = {
                    "viewport": {"width": 1920, "height": 1080},
                    "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                if proxy:
                    proxy_config = {
                        "server": f"http://{proxy['server']}"
                    }
                    if 'username' in proxy and 'password' in proxy:
                        proxy_config["server"] = f"http://{proxy['username']}:{proxy['password']}@{proxy['server']}"
                    context_options["proxy"] = proxy_config
                    print(f"프록시 사용: {proxy['server']}")
                
                if self.context:
                    self.context.close()
                
                self.context = self.browser.new_context(**context_options)
                page = self.context.new_page()
                
                # 브라우저 자동화 및 출금 처리
                browser_automation = BrowserAutomation(page, self.captcha_solver)
                withdrawal_handler = WithdrawalHandler(page)
                
                # 로그인
                login_success = browser_automation.login(email, password)
                result["login_success"] = login_success
                
                if not login_success:
                    result["error"] = "로그인 실패"
                    self.logger.log_account(email, False, 0.0, "로그인 실패")
                    time.sleep(2)
                    continue
                
                print("로그인 성공")
                time.sleep(2)  # 로그인 후 대기
                
                # 잔액 확인
                balance = withdrawal_handler.check_balance()
                if balance is None or balance <= 0:
                    result["error"] = "출금 가능한 잔액이 없습니다."
                    result["success"] = True  # 로그인은 성공했으므로
                    self.logger.log_account(email, True, 0.0, "잔액 없음")
                    browser_automation.logout()
                    continue
                
                print(f"계정 잔액: {balance}")
                
                # 출금 처리
                withdrawal_result = withdrawal_handler.process_withdrawal(
                    destination_wallet,
                    amount=None  # 전체 잔액 출금
                )
                
                result["withdrawal_success"] = withdrawal_result["success"]
                result["withdrawn_amount"] = withdrawal_result.get("amount", 0.0)
                
                if withdrawal_result["success"]:
                    result["success"] = True
                    result["error"] = ""
                    print(f"출금 성공: {result['withdrawn_amount']}")
                    self.logger.log_account(
                        email,
                        True,
                        result["withdrawn_amount"],
                        "출금 성공"
                    )
                else:
                    result["error"] = withdrawal_result.get("message", "출금 실패")
                    print(f"출금 실패: {result['error']}")
                    self.logger.log_account(
                        email,
                        False,
                        0.0,
                        result["error"]
                    )
                
                # 로그아웃
                browser_automation.logout()
                time.sleep(1)
                
                # 성공하면 재시도 중단
                if result["success"]:
                    break
                
            except Exception as e:
                result["error"] = f"처리 중 오류: {str(e)}"
                print(f"계정 처리 중 오류: {e}")
                self.logger.log_account(email, False, 0.0, str(e))
                time.sleep(2)
        
        return result

