"""
출금 처리 모듈
로그인 후 계정 잔액을 확인하고 조건에 따라 출금을 처리합니다.
"""
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from typing import Optional, Dict


class WithdrawalHandler:
    def __init__(self, driver):
        """
        Args:
            driver: undetected-chromedriver WebDriver 객체
        """
        self.driver = driver
        self.wait = WebDriverWait(driver, 30)
    
    def check_balance(self) -> Optional[float]:
        """
        계정 잔액을 확인합니다.
        
        Returns:
            잔액 (float) 또는 None
        """
        try:
            # 잔액이 표시되는 여러 가능한 위치 확인
            balance_selectors = [
                '.balance',
                '.account-balance',
                '.wallet-balance',
                '[data-balance]',
                '.balance-amount',
                '.user-balance',
                '.total-balance',
                '.available-balance'
            ]
            
            for selector in balance_selectors:
                try:
                    element = self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                    if element:
                        balance_text = element.text
                        balance = self._parse_balance(balance_text)
                        if balance is not None and balance > 0:
                            print(f"잔액 확인: {balance}")
                            return balance
                except TimeoutException:
                    continue
            
            # XPath로 "Balance" 텍스트 포함 요소 찾기
            try:
                balance_elements = self.driver.find_elements(
                    By.XPATH, 
                    "//*[contains(text(), 'Balance') or contains(text(), 'balance') or contains(text(), '잔액')]"
                )
                for elem in balance_elements:
                    parent = elem.find_element(By.XPATH, '..')
                    balance_text = parent.text
                    balance = self._parse_balance(balance_text)
                    if balance is not None and balance > 0:
                        print(f"잔액 확인 (XPath): {balance}")
                        return balance
            except:
                pass
            
            # 페이지 소스에서 직접 찾기
            page_source = self.driver.page_source
            balance_patterns = [
                r'balance["\']?\s*[:=]\s*["\']?([\d,]+\.?\d*)',
                r'잔액["\']?\s*[:=]\s*["\']?([\d,]+\.?\d*)',
                r'Balance["\']?\s*[:=]\s*["\']?([\d,]+\.?\d*)',
                r'"balance":\s*([\d,]+\.?\d*)',
                r'data-balance=["\']?([\d,]+\.?\d*)'
            ]
            
            for pattern in balance_patterns:
                match = re.search(pattern, page_source, re.IGNORECASE)
                if match:
                    balance = self._parse_balance(match.group(1))
                    if balance is not None and balance > 0:
                        print(f"잔액 확인 (패턴 매칭): {balance}")
                        return balance
            
            print("잔액을 찾을 수 없습니다.")
            return None
        
        except Exception as e:
            print(f"잔액 확인 중 오류: {e}")
            return None
    
    def _parse_balance(self, text: str) -> Optional[float]:
        """텍스트에서 잔액 숫자를 파싱합니다."""
        try:
            # 숫자와 소수점만 추출
            cleaned = re.sub(r'[^\d.,]', '', text)
            cleaned = cleaned.replace(',', '')
            if cleaned:
                return float(cleaned)
            return None
        except:
            return None
    
    def should_withdraw(self, balance: float, config: Dict) -> bool:
        """
        출금 조건을 확인합니다.
        
        Args:
            balance: 현재 잔액
            config: 설정 딕셔너리
        
        Returns:
            출금해야 하면 True
        """
        # 최소 출금 금액 확인
        min_withdrawal_amount = config.get('min_withdrawal_amount', 0)
        if balance < min_withdrawal_amount:
            print(f"잔액({balance})이 최소 출금 금액({min_withdrawal_amount})보다 작습니다.")
            return False
        
        # 최소 잔액 필터링 (이 금액 이상일 때만 출금)
        min_balance_filter = config.get('min_balance_filter', 0)
        if min_balance_filter > 0 and balance < min_balance_filter:
            print(f"잔액({balance})이 최소 필터 금액({min_balance_filter})보다 작습니다. 스킵합니다.")
            return False
        
        # 최대 잔액 필터링 (이 금액 이하일 때만 출금)
        max_balance_filter = config.get('max_balance_filter', float('inf'))
        if balance > max_balance_filter:
            print(f"잔액({balance})이 최대 필터 금액({max_balance_filter})보다 큽니다. 스킵합니다.")
            return False
        
        return True
    
    def navigate_to_withdrawal(self) -> bool:
        """
        출금 페이지로 이동합니다.
        
        Returns:
            이동 성공 여부
        """
        try:
            # 먼저 메뉴에서 출금 링크 찾기
            withdrawal_link_selectors = [
                (By.CSS_SELECTOR, 'a[href*="withdraw" i]'),
                (By.XPATH, '//a[contains(text(), "Withdraw") or contains(text(), "출금")]'),
                (By.XPATH, '//button[contains(text(), "Withdraw") or contains(text(), "출금")]')
            ]
            
            for by, selector in withdrawal_link_selectors:
                try:
                    link = self.wait.until(EC.element_to_be_clickable((by, selector)))
                    if link:
                        link.click()
                        time.sleep(3)
                        if self._is_withdrawal_page():
                            print("출금 페이지로 이동 완료")
                            return True
                except TimeoutException:
                    continue
            
            # 직접 URL로 이동
            withdrawal_urls = [
                "https://rollbet.gg/withdraw",
                "https://rollbet.gg/withdrawal",
                "https://rollbet.gg/wallet/withdraw",
                "https://rollbet.gg/account/withdraw"
            ]
            
            for url in withdrawal_urls:
                try:
                    self.driver.get(url)
                    time.sleep(3)
                    if self._is_withdrawal_page():
                        print(f"출금 페이지로 이동 완료: {url}")
                        return True
                except:
                    continue
            
            print("출금 페이지로 이동할 수 없습니다.")
            return False
        
        except Exception as e:
            print(f"출금 페이지 이동 중 오류: {e}")
            return False
    
    def _is_withdrawal_page(self) -> bool:
        """현재 페이지가 출금 페이지인지 확인합니다."""
        try:
            current_url = self.driver.current_url.lower()
            if "withdraw" in current_url:
                return True
            
            # 출금 관련 요소 확인
            withdrawal_indicators = [
                (By.CSS_SELECTOR, 'input[name*="amount" i]'),
                (By.CSS_SELECTOR, 'input[placeholder*="amount" i]'),
                (By.CSS_SELECTOR, 'input[name*="wallet" i]'),
                (By.XPATH, '//button[contains(text(), "Withdraw") or contains(text(), "출금")]')
            ]
            
            for by, selector in withdrawal_indicators:
                try:
                    element = self.driver.find_element(by, selector)
                    if element:
                        return True
                except NoSuchElementException:
                    continue
            
            return False
        except:
            return False
    
    def process_withdrawal(
        self, 
        destination_wallet: str, 
        amount: Optional[float] = None,
        config: Optional[Dict] = None
    ) -> Dict[str, any]:
        """
        출금을 처리합니다.
        
        Args:
            destination_wallet: 목적 지갑 주소
            amount: 출금 금액 (None이면 전체 잔액)
            config: 설정 딕셔너리
        
        Returns:
            {"success": bool, "amount": float, "message": str}
        """
        result = {
            "success": False,
            "amount": 0.0,
            "message": ""
        }
        
        config = config or {}
        
        try:
            # 잔액 확인
            balance = self.check_balance()
            if balance is None or balance <= 0:
                result["message"] = "출금 가능한 잔액이 없습니다."
                return result
            
            # 출금 조건 확인
            if not self.should_withdraw(balance, config):
                result["message"] = "출금 조건을 만족하지 않습니다."
                result["success"] = True  # 조건 불만족은 성공으로 간주 (스킵)
                return result
            
            # 출금 금액 결정
            withdrawal_amount = amount if amount else balance
            
            # 최소 출금 금액 확인
            min_withdrawal = config.get('min_withdrawal_amount', 0)
            if withdrawal_amount < min_withdrawal:
                result["message"] = f"출금 금액({withdrawal_amount})이 최소 출금 금액({min_withdrawal})보다 작습니다."
                return result
            
            if withdrawal_amount > balance:
                result["message"] = f"출금 금액({withdrawal_amount})이 잔액({balance})보다 큽니다."
                return result
            
            # 출금 페이지로 이동
            if not self.navigate_to_withdrawal():
                result["message"] = "출금 페이지로 이동할 수 없습니다."
                return result
            
            time.sleep(3)
            
            # 지갑 주소 입력
            wallet_input_selectors = [
                (By.CSS_SELECTOR, 'input[name*="wallet" i]'),
                (By.CSS_SELECTOR, 'input[name*="address" i]'),
                (By.CSS_SELECTOR, 'input[placeholder*="wallet" i]'),
                (By.CSS_SELECTOR, 'input[placeholder*="address" i]')
            ]
            
            wallet_input = None
            for by, selector in wallet_input_selectors:
                try:
                    inputs = self.driver.find_elements(by, selector)
                    for inp in inputs:
                        placeholder = inp.get_attribute('placeholder') or ''
                        name = inp.get_attribute('name') or ''
                        if 'wallet' in placeholder.lower() or 'address' in placeholder.lower() or \
                           'wallet' in name.lower() or 'address' in name.lower():
                            wallet_input = inp
                            break
                    if wallet_input:
                        break
                except:
                    continue
            
            if wallet_input:
                wallet_input.clear()
                wallet_input.send_keys(destination_wallet)
                time.sleep(1)
                print(f"지갑 주소 입력 완료: {destination_wallet[:20]}...")
            else:
                print("지갑 주소 입력 필드를 찾을 수 없습니다. 수동 확인이 필요할 수 있습니다.")
            
            # 출금 금액 입력
            amount_input_selectors = [
                (By.CSS_SELECTOR, 'input[name*="amount" i]'),
                (By.CSS_SELECTOR, 'input[placeholder*="amount" i]'),
                (By.CSS_SELECTOR, 'input[type="number"]')
            ]
            
            amount_input = None
            for by, selector in amount_input_selectors:
                try:
                    inputs = self.driver.find_elements(by, selector)
                    for inp in inputs:
                        placeholder = inp.get_attribute('placeholder') or ''
                        name = inp.get_attribute('name') or ''
                        if 'amount' in placeholder.lower() or 'amount' in name.lower():
                            amount_input = inp
                            break
                    if amount_input:
                        break
                except:
                    continue
            
            if amount_input:
                amount_input.clear()
                amount_input.send_keys(str(withdrawal_amount))
                time.sleep(1)
                print(f"출금 금액 입력 완료: {withdrawal_amount}")
            else:
                print("출금 금액 입력 필드를 찾을 수 없습니다.")
            
            # 출금 버튼 클릭
            withdraw_button_selectors = [
                (By.CSS_SELECTOR, 'button[type="submit"]'),
                (By.XPATH, '//button[contains(text(), "Withdraw") or contains(text(), "출금")]'),
                (By.XPATH, '//button[contains(text(), "Confirm") or contains(text(), "확인")]'),
                (By.CSS_SELECTOR, 'button.btn-primary'),
                (By.CSS_SELECTOR, 'button.withdraw-button')
            ]
            
            withdraw_button = None
            for by, selector in withdraw_button_selectors:
                try:
                    button = self.wait.until(EC.element_to_be_clickable((by, selector)))
                    if button and button.is_displayed():
                        withdraw_button = button
                        break
                except TimeoutException:
                    continue
            
            if withdraw_button:
                withdraw_button.click()
                time.sleep(5)  # 출금 처리 대기
                print("출금 버튼 클릭 완료")
            else:
                print("출금 버튼을 찾을 수 없습니다.")
                result["message"] = "출금 버튼을 찾을 수 없습니다."
                return result
            
            # 출금 성공 확인
            success_indicators = [
                (By.XPATH, '//*[contains(text(), "출금 요청이 완료되었습니다")]'),
                (By.XPATH, '//*[contains(text(), "Withdrawal request submitted")]'),
                (By.XPATH, '//*[contains(text(), "Success")]'),
                (By.XPATH, '//*[contains(text(), "성공")]'),
                (By.CSS_SELECTOR, '.success-message'),
                (By.CSS_SELECTOR, '.alert-success')
            ]
            
            for by, selector in success_indicators:
                try:
                    element = self.wait.until(EC.presence_of_element_located((by, selector)))
                    if element:
                        result["success"] = True
                        result["amount"] = withdrawal_amount
                        result["message"] = "출금 요청이 성공적으로 제출되었습니다."
                        print(f"출금 성공: {withdrawal_amount}")
                        return result
                except TimeoutException:
                    continue
            
            # 에러 메시지 확인
            error_indicators = [
                (By.CSS_SELECTOR, '.error-message'),
                (By.CSS_SELECTOR, '.alert-danger'),
                (By.XPATH, '//*[contains(text(), "Error")]'),
                (By.XPATH, '//*[contains(text(), "오류")]')
            ]
            
            for by, selector in error_indicators:
                try:
                    element = self.driver.find_element(by, selector)
                    if element:
                        error_text = element.text
                        result["message"] = f"출금 실패: {error_text}"
                        print(f"출금 실패: {error_text}")
                        return result
                except NoSuchElementException:
                    continue
            
            # 명확한 성공/실패 메시지가 없는 경우
            result["success"] = True  # 일단 성공으로 간주 (추후 확인 필요)
            result["amount"] = withdrawal_amount
            result["message"] = "출금 요청이 제출되었습니다. (확인 필요)"
            print("출금 요청 제출 완료 (확인 필요)")
            return result
        
        except Exception as e:
            result["message"] = f"출금 처리 중 오류: {e}"
            print(f"출금 처리 중 오류: {e}")
            import traceback
            traceback.print_exc()
            return result
