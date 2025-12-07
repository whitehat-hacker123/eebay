"""
브라우저 자동화 모듈
undetected-chromedriver를 사용하여 rollbet.gg 로그인을 자동화합니다.
"""
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import Optional, Dict
from captcha_solver import CaptchaSolver


class BrowserAutomation:
    def __init__(self, driver, captcha_solver: Optional[CaptchaSolver] = None):
        """
        Args:
            driver: undetected-chromedriver WebDriver 객체
            captcha_solver: CaptchaSolver 인스턴스 (선택적)
        """
        self.driver = driver
        self.captcha_solver = captcha_solver
        self.wait = WebDriverWait(driver, 30)
    
    def login(self, username: str, password: str, login_url: str = "https://rollbet.gg/login") -> bool:
        """
        rollbet.gg에 로그인합니다.
        
        Args:
            username: 사용자명 또는 이메일 주소
            password: 비밀번호
            login_url: 로그인 페이지 URL
        
        Returns:
            로그인 성공 여부
        """
        try:
            print(f"로그인 페이지 접속 중: {username}")
            self.driver.get(login_url)
            time.sleep(3)  # 페이지 로딩 대기
            
            # Email/Username 입력 필드 찾기 및 입력
            email_selectors = [
                'input[type="email"]',
                'input[name="email"]',
                'input[name="username"]',
                'input[name="user"]',
                'input[placeholder*="Email" i]',
                'input[placeholder*="Username" i]',
                'input[id*="email" i]',
                'input[id*="username" i]',
                'input[type="text"]'
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if email_input and email_input.is_displayed():
                        break
                except TimeoutException:
                    continue
            
            if not email_input:
                print("Email/Username 입력 필드를 찾을 수 없습니다.")
                return False
            
            # 기존 값 지우고 입력
            email_input.clear()
            email_input.send_keys(username)
            time.sleep(1)
            
            # Password 입력 필드 찾기 및 입력
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[name="pass"]',
                'input[placeholder*="Password" i]',
                'input[id*="password" i]'
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if password_input and password_input.is_displayed():
                        break
                except NoSuchElementException:
                    continue
            
            if not password_input:
                print("Password 입력 필드를 찾을 수 없습니다.")
                return False
            
            password_input.clear()
            password_input.send_keys(password)
            time.sleep(1)
            
            # hCaptcha 처리
            if self.captcha_solver:
                if not self._solve_captcha():
                    print("hCaptcha 해결 실패")
                    return False
            
            # Login 버튼 찾기 및 클릭
            login_button_selectors = [
                'button[type="submit"]',
                'button:contains("Login")',
                'button:contains("Log in")',
                'button:contains("로그인")',
                'input[type="submit"]',
                'button.btn-primary',
                'button.login-button',
                'button[class*="login"]',
                'button[class*="submit"]'
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    if ':contains(' in selector:
                        # contains는 XPath로 변환
                        text = selector.split('"')[1]
                        xpath = f"//button[contains(text(), '{text}')]"
                        login_button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        login_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    
                    if login_button and login_button.is_displayed():
                        break
                except (NoSuchElementException, TimeoutException):
                    continue
            
            if not login_button:
                print("Login 버튼을 찾을 수 없습니다.")
                return False
            
            login_button.click()
            time.sleep(5)  # 로그인 처리 대기
            
            # 로그인 성공 확인
            current_url = self.driver.current_url
            if "login" not in current_url.lower() or self._check_login_success():
                print(f"로그인 성공: {username}")
                return True
            else:
                print(f"로그인 실패: {username}")
                return False
        
        except Exception as e:
            print(f"로그인 중 오류 발생: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _solve_captcha(self) -> bool:
        """hCaptcha를 해결합니다."""
        try:
            # hCaptcha iframe 찾기
            time.sleep(2)  # 페이지 로딩 대기
            
            captcha_selectors = [
                'iframe[src*="hcaptcha"]',
                'iframe[title*="hcaptcha" i]',
                '.h-captcha iframe',
                'iframe[data-hcaptcha-widget-id]'
            ]
            
            captcha_iframe = None
            for selector in captcha_selectors:
                try:
                    captcha_iframe = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if captcha_iframe:
                        break
                except NoSuchElementException:
                    continue
            
            if not captcha_iframe:
                print("hCaptcha를 찾을 수 없습니다. 이미 해결되었거나 없는 것 같습니다.")
                return True  # CAPTCHA가 없으면 성공으로 간주
            
            # hCaptcha 사이트 키 추출
            site_key = self.driver.execute_script("""
                const iframe = document.querySelector('iframe[src*="hcaptcha"]');
                if (iframe) {
                    const src = iframe.src;
                    const match = src.match(/sitekey=([^&]+)/);
                    if (match) return match[1];
                }
                const widget = document.querySelector('[data-sitekey]');
                if (widget) {
                    return widget.getAttribute('data-sitekey');
                }
                return null;
            """)
            
            if not site_key:
                # 페이지 소스에서 직접 찾기
                page_source = self.driver.page_source
                import re
                match = re.search(r'data-sitekey=["\']([^"\']+)["\']', page_source)
                if match:
                    site_key = match.group(1)
                else:
                    print("hCaptcha 사이트 키를 찾을 수 없습니다.")
                    return False
            
            print(f"hCaptcha 사이트 키 발견: {site_key[:20]}...")
            
            # 2captcha로 해결
            page_url = self.driver.current_url
            token = self.captcha_solver.solve_hcaptcha(site_key, page_url)
            
            if not token:
                return False
            
            # 토큰을 페이지에 주입
            self.driver.execute_script(f"""
                // hCaptcha 콜백 함수 호출
                if (window.hcaptcha) {{
                    const widgetId = window.hcaptcha.render(
                        document.querySelector('.h-captcha') || document.body
                    );
                    window.hcaptcha.execute(widgetId, {{token: '{token}'}});
                }}
                // 직접 토큰 설정
                const textarea = document.querySelector('textarea[name="h-captcha-response"]');
                if (textarea) {{
                    textarea.value = '{token}';
                    textarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    textarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
                // g-recaptcha-response도 확인
                const gTextarea = document.querySelector('textarea[name="g-recaptcha-response"]');
                if (gTextarea) {{
                    gTextarea.value = '{token}';
                    gTextarea.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    gTextarea.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }}
            """)
            
            time.sleep(3)  # 토큰 적용 대기
            print("hCaptcha 토큰 주입 완료")
            return True
        
        except Exception as e:
            print(f"hCaptcha 해결 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _check_login_success(self) -> bool:
        """로그인 성공 여부를 확인합니다."""
        try:
            # 로그인 성공 표시 요소 확인
            success_indicators = [
                (By.CSS_SELECTOR, 'a[href*="logout"]'),
                (By.XPATH, '//button[contains(text(), "Logout")]'),
                (By.XPATH, '//button[contains(text(), "Log out")]'),
                (By.CSS_SELECTOR, '.user-menu'),
                (By.CSS_SELECTOR, '.account-menu'),
                (By.CSS_SELECTOR, '[data-testid="user-menu"]')
            ]
            
            for by, selector in success_indicators:
                try:
                    element = self.driver.find_element(by, selector)
                    if element:
                        return True
                except NoSuchElementException:
                    continue
            
            # URL 기반 확인
            current_url = self.driver.current_url.lower()
            if "dashboard" in current_url or "account" in current_url or "profile" in current_url:
                return True
            
            return False
        
        except:
            return False
    
    def logout(self) -> bool:
        """로그아웃합니다."""
        try:
            logout_selectors = [
                (By.CSS_SELECTOR, 'a[href*="logout"]'),
                (By.XPATH, '//button[contains(text(), "Logout")]'),
                (By.XPATH, '//button[contains(text(), "Log out")]'),
                (By.CSS_SELECTOR, '.logout-button')
            ]
            
            for by, selector in logout_selectors:
                try:
                    logout_button = self.driver.find_element(by, selector)
                    if logout_button and logout_button.is_displayed():
                        logout_button.click()
                        time.sleep(2)
                        print("로그아웃 완료")
                        return True
                except (NoSuchElementException, TimeoutException):
                    continue
            
            # URL로 직접 로그아웃 시도
            try:
                self.driver.get("https://rollbet.gg/logout")
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
