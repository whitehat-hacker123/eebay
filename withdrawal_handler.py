"""
출금 처리 모듈
로그인 후 계정 잔액을 확인하고 출금을 처리합니다.
"""
import time
import re
from playwright.sync_api import Page
from typing import Optional, Dict
from browser_automation import BrowserAutomation


class WithdrawalHandler:
    def __init__(self, page: Page):
        """
        Args:
            page: Playwright Page 객체
        """
        self.page = page
    
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
                'span:has-text("Balance")',
                'div:has-text("Balance")'
            ]
            
            for selector in balance_selectors:
                try:
                    element = self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        balance_text = element.inner_text()
                        balance = self._parse_balance(balance_text)
                        if balance is not None:
                            print(f"잔액 확인: {balance}")
                            return balance
                except:
                    continue
            
            # 페이지 소스에서 직접 찾기
            page_content = self.page.content()
            balance_patterns = [
                r'balance["\']?\s*[:=]\s*["\']?([\d,]+\.?\d*)',
                r'잔액["\']?\s*[:=]\s*["\']?([\d,]+\.?\d*)',
                r'Balance["\']?\s*[:=]\s*["\']?([\d,]+\.?\d*)'
            ]
            
            for pattern in balance_patterns:
                match = re.search(pattern, page_content, re.IGNORECASE)
                if match:
                    balance = self._parse_balance(match.group(1))
                    if balance is not None:
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
            return float(cleaned)
        except:
            return None
    
    def navigate_to_withdrawal(self) -> bool:
        """
        출금 페이지로 이동합니다.
        
        Returns:
            이동 성공 여부
        """
        try:
            # 출금 페이지로 이동하는 여러 방법 시도
            withdrawal_urls = [
                "https://rollbet.gg/withdraw",
                "https://rollbet.gg/withdrawal",
                "https://rollbet.gg/wallet/withdraw",
                "https://rollbet.gg/account/withdraw"
            ]
            
            # 먼저 메뉴에서 출금 링크 찾기
            withdrawal_link_selectors = [
                'a[href*="withdraw" i]',
                'a:has-text("Withdraw")',
                'a:has-text("출금")',
                'button:has-text("Withdraw")',
                'button:has-text("출금")'
            ]
            
            for selector in withdrawal_link_selectors:
                try:
                    link = self.page.wait_for_selector(selector, timeout=3000)
                    if link:
                        link.click()
                        time.sleep(2)
                        if self._is_withdrawal_page():
                            print("출금 페이지로 이동 완료")
                            return True
                except:
                    continue
            
            # 직접 URL로 이동
            for url in withdrawal_urls:
                try:
                    self.page.goto(url, wait_until="networkidle", timeout=15000)
                    time.sleep(2)
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
            current_url = self.page.url.lower()
            if "withdraw" in current_url:
                return True
            
            # 출금 관련 요소 확인
            withdrawal_indicators = [
                'input[name*="amount" i]',
                'input[placeholder*="amount" i]',
                'input[name*="wallet" i]',
                'button:has-text("Withdraw")',
                'button:has-text("출금")'
            ]
            
            for selector in withdrawal_indicators:
                try:
                    element = self.page.wait_for_selector(selector, timeout=2000)
                    if element:
                        return True
                except:
                    continue
            
            return False
        except:
            return False
    
    def process_withdrawal(self, destination_wallet: str, amount: Optional[float] = None) -> Dict[str, any]:
        """
        출금을 처리합니다.
        
        Args:
            destination_wallet: 목적 지갑 주소
            amount: 출금 금액 (None이면 전체 잔액)
        
        Returns:
            {"success": bool, "amount": float, "message": str}
        """
        result = {
            "success": False,
            "amount": 0.0,
            "message": ""
        }
        
        try:
            # 잔액 확인
            balance = self.check_balance()
            if balance is None or balance <= 0:
                result["message"] = "출금 가능한 잔액이 없습니다."
                return result
            
            # 출금 금액 결정
            withdrawal_amount = amount if amount else balance
            
            if withdrawal_amount > balance:
                result["message"] = f"출금 금액({withdrawal_amount})이 잔액({balance})보다 큽니다."
                return result
            
            # 출금 페이지로 이동
            if not self.navigate_to_withdrawal():
                result["message"] = "출금 페이지로 이동할 수 없습니다."
                return result
            
            time.sleep(2)
            
            # 지갑 주소 입력
            wallet_input_selectors = [
                'input[name*="wallet" i]',
                'input[name*="address" i]',
                'input[placeholder*="wallet" i]',
                'input[placeholder*="address" i]',
                'input[type="text"]'
            ]
            
            wallet_input = None
            for selector in wallet_input_selectors:
                try:
                    # 여러 입력 필드 중에서 지갑 주소 필드 찾기
                    inputs = self.page.query_selector_all(selector)
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
                wallet_input.fill(destination_wallet)
                time.sleep(0.5)
                print(f"지갑 주소 입력 완료: {destination_wallet[:20]}...")
            else:
                print("지갑 주소 입력 필드를 찾을 수 없습니다. 수동 확인이 필요할 수 있습니다.")
            
            # 출금 금액 입력
            amount_input_selectors = [
                'input[name*="amount" i]',
                'input[placeholder*="amount" i]',
                'input[type="number"]'
            ]
            
            amount_input = None
            for selector in amount_input_selectors:
                try:
                    inputs = self.page.query_selector_all(selector)
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
                amount_input.fill(str(withdrawal_amount))
                time.sleep(0.5)
                print(f"출금 금액 입력 완료: {withdrawal_amount}")
            else:
                print("출금 금액 입력 필드를 찾을 수 없습니다.")
            
            # 출금 버튼 클릭
            withdraw_button_selectors = [
                'button[type="submit"]',
                'button:has-text("Withdraw")',
                'button:has-text("출금")',
                'button:has-text("Confirm")',
                'button:has-text("확인")',
                'button.btn-primary',
                'button.withdraw-button'
            ]
            
            withdraw_button = None
            for selector in withdraw_button_selectors:
                try:
                    button = self.page.wait_for_selector(selector, timeout=3000)
                    if button and button.is_visible():
                        withdraw_button = button
                        break
                except:
                    continue
            
            if withdraw_button:
                withdraw_button.click()
                time.sleep(3)  # 출금 처리 대기
                print("출금 버튼 클릭 완료")
            else:
                print("출금 버튼을 찾을 수 없습니다.")
                result["message"] = "출금 버튼을 찾을 수 없습니다."
                return result
            
            # 출금 성공 확인
            success_indicators = [
                'text=출금 요청이 완료되었습니다',
                'text=Withdrawal request submitted',
                'text=Success',
                'text=성공',
                '.success-message',
                '.alert-success'
            ]
            
            for indicator in success_indicators:
                try:
                    element = self.page.wait_for_selector(indicator, timeout=5000)
                    if element:
                        result["success"] = True
                        result["amount"] = withdrawal_amount
                        result["message"] = "출금 요청이 성공적으로 제출되었습니다."
                        print(f"출금 성공: {withdrawal_amount}")
                        return result
                except:
                    continue
            
            # 에러 메시지 확인
            error_indicators = [
                '.error-message',
                '.alert-danger',
                'text=Error',
                'text=오류'
            ]
            
            for indicator in error_indicators:
                try:
                    element = self.page.wait_for_selector(indicator, timeout=2000)
                    if element:
                        error_text = element.inner_text()
                        result["message"] = f"출금 실패: {error_text}"
                        print(f"출금 실패: {error_text}")
                        return result
                except:
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
            return result

