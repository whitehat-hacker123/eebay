"""
브라우저 자동화 모듈
Playwright를 사용하여 rollbet.gg 로그인을 자동화합니다.
"""
import time
from playwright.sync_api import Page, Browser, BrowserContext
from typing import Optional, Dict
from captcha_solver import CaptchaSolver


class BrowserAutomation:
    def __init__(self, page: Page, captcha_solver: Optional[CaptchaSolver] = None):
        """
        Args:
            page: Playwright Page 객체
            captcha_solver: CaptchaSolver 인스턴스 (선택적)
        """
        self.page = page
        self.captcha_solver = captcha_solver
    
    def login(self, email: str, password: str, login_url: str = "https://rollbet.gg/login") -> bool:
        """
        rollbet.gg에 로그인합니다.
        
        Args:
            email: 이메일 주소
            password: 비밀번호
            login_url: 로그인 페이지 URL
        
        Returns:
            로그인 성공 여부
        """
        try:
            print(f"로그인 페이지 접속 중: {email}")
            self.page.goto(login_url, wait_until="networkidle", timeout=30000)
            time.sleep(2)  # 페이지 로딩 대기
            
            # Email 입력 필드 찾기 및 입력
            # 여러 가능한 셀렉터 시도
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[placeholder*="Email" i]',
                'input[id*="email" i]',
                'input[type="text"]'  # fallback
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = self.page.wait_for_selector(selector, timeout=5000)
                    if email_input:
                        break
                except:
                    continue
            
            if not email_input:
                print("Email 입력 필드를 찾을 수 없습니다.")
                return False
            
            email_input.fill(email)
            time.sleep(0.5)
            
            # Password 입력 필드 찾기 및 입력
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[placeholder*="Password" i]',
                'input[id*="password" i]'
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = self.page.wait_for_selector(selector, timeout=5000)
                    if password_input:
                        break
                except:
                    continue
            
            if not password_input:
                print("Password 입력 필드를 찾을 수 없습니다.")
                return False
            
            password_input.fill(password)
            time.sleep(0.5)
            
            # hCaptcha 처리
            if self.captcha_solver:
                if not self._solve_captcha():
                    print("hCaptcha 해결 실패")
                    return False
            
            # Login 버튼 찾기 및 클릭
            login_button_selectors = [
                'button[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Log in")',
                'button:has-text("로그인")',
                'input[type="submit"]',
                'button.btn-primary',
                'button.login-button'
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = self.page.wait_for_selector(selector, timeout=5000)
                    if login_button:
                        break
                except:
                    continue
            
            if not login_button:
                print("Login 버튼을 찾을 수 없습니다.")
                return False
            
            login_button.click()
            time.sleep(3)  # 로그인 처리 대기
            
            # 로그인 성공 확인
            # URL 변경 또는 특정 요소가 나타나는지 확인
            current_url = self.page.url
            if "login" not in current_url.lower() or self._check_login_success():
                print(f"로그인 성공: {email}")
                return True
            else:
                print(f"로그인 실패: {email}")
                return False
        
        except Exception as e:
            print(f"로그인 중 오류 발생: {e}")
            return False
    
    def _solve_captcha(self) -> bool:
        """hCaptcha를 해결합니다."""
        try:
            # hCaptcha iframe 찾기
            captcha_selectors = [
                'iframe[src*="hcaptcha"]',
                'iframe[title*="hcaptcha" i]',
                '.h-captcha iframe',
                'iframe[data-hcaptcha-widget-id]'
            ]
            
            captcha_iframe = None
            for selector in captcha_selectors:
                try:
                    captcha_iframe = self.page.wait_for_selector(selector, timeout=5000)
                    if captcha_iframe:
                        break
                except:
                    continue
            
            if not captcha_iframe:
                print("hCaptcha를 찾을 수 없습니다. 이미 해결되었거나 없는 것 같습니다.")
                return True  # CAPTCHA가 없으면 성공으로 간주
            
            # hCaptcha 사이트 키 추출
            site_key = self.page.evaluate("""
                () => {
                    const iframe = document.querySelector('iframe[src*="hcaptcha"]');
                    if (iframe) {
                        const src = iframe.src;
                        const match = src.match(/sitekey=([^&]+)/);
                        return match ? match[1] : null;
                    }
                    // 또는 data-sitekey 속성 확인
                    const widget = document.querySelector('[data-sitekey]');
                    if (widget) {
                        return widget.getAttribute('data-sitekey');
                    }
                    return null;
                }
            """)
            
            if not site_key:
                # 페이지 소스에서 직접 찾기
                page_content = self.page.content()
                import re
                match = re.search(r'data-sitekey=["\']([^"\']+)["\']', page_content)
                if match:
                    site_key = match.group(1)
                else:
                    print("hCaptcha 사이트 키를 찾을 수 없습니다.")
                    return False
            
            print(f"hCaptcha 사이트 키 발견: {site_key[:20]}...")
            
            # 2captcha로 해결
            page_url = self.page.url
            token = self.captcha_solver.solve_hcaptcha(site_key, page_url)
            
            if not token:
                return False
            
            # 토큰을 페이지에 주입
            self.page.evaluate(f"""
                () => {{
                    // hCaptcha 콜백 함수 호출
                    if (window.hcaptcha) {{
                        const widgetId = window.hcaptcha.render(document.querySelector('.h-captcha') || document.body);
                        window.hcaptcha.execute(widgetId, {{token: '{token}'}});
                    }}
                    // 또는 직접 토큰 설정
                    const textarea = document.querySelector('textarea[name="h-captcha-response"]');
                    if (textarea) {{
                        textarea.value = '{token}';
                        textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                    // g-recaptcha-response도 확인
                    const gTextarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                    if (gTextarea) {{
                        gTextarea.value = '{token}';
                        gTextarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    }}
                }}
            """)
            
            time.sleep(2)  # 토큰 적용 대기
            print("hCaptcha 토큰 주입 완료")
            return True
        
        except Exception as e:
            print(f"hCaptcha 해결 중 오류: {e}")
            return False
    
    def _check_login_success(self) -> bool:
        """로그인 성공 여부를 확인합니다."""
        try:
            # 로그인 성공 표시 요소 확인
            success_indicators = [
                'a[href*="logout"]',
                'button:has-text("Logout")',
                'button:has-text("Log out")',
                '.user-menu',
                '.account-menu',
                '[data-testid="user-menu"]'
            ]
            
            for selector in success_indicators:
                try:
                    element = self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        return True
                except:
                    continue
            
            # URL 기반 확인
            current_url = self.page.url
            if "dashboard" in current_url.lower() or "account" in current_url.lower():
                return True
            
            return False
        
        except:
            return False
    
    def logout(self) -> bool:
        """로그아웃합니다."""
        try:
            logout_selectors = [
                'a[href*="logout"]',
                'button:has-text("Logout")',
                'button:has-text("Log out")',
                '.logout-button'
            ]
            
            for selector in logout_selectors:
                try:
                    logout_button = self.page.wait_for_selector(selector, timeout=5000)
                    if logout_button:
                        logout_button.click()
                        time.sleep(2)
                        print("로그아웃 완료")
                        return True
                except:
                    continue
            
            # URL로 직접 로그아웃 시도
            try:
                self.page.goto("https://rollbet.gg/logout", timeout=10000)
                time.sleep(2)
                print("로그아웃 완료 (URL 직접 접근)")
                return True
            except:
                pass
            
            print("로그아웃 버튼을 찾을 수 없습니다.")
            return False
        
        except Exception as e:
            print(f"로그아웃 중 오류: {e}")
            return False

