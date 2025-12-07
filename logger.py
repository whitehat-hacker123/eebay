"""
로깅 및 모니터링 모듈
로그인, 출금 성공/실패를 추적하고 로그 파일을 생성합니다.
"""
import json
import csv
from datetime import datetime
from typing import List, Dict
import os


class Logger:
    def __init__(self, log_file: str = "withdrawal_log.json", csv_file: str = "withdrawal_log.csv"):
        """
        Args:
            log_file: JSON 로그 파일 경로
            csv_file: CSV 로그 파일 경로
        """
        self.log_file = log_file
        self.csv_file = csv_file
        self.logs: List[Dict] = []
        
        # CSV 파일 헤더 작성 (파일이 없을 경우)
        if not os.path.exists(self.csv_file):
            self._init_csv()
    
    def _init_csv(self):
        """CSV 파일을 초기화합니다."""
        try:
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp',
                    'email',
                    'success',
                    'login_success',
                    'withdrawal_success',
                    'withdrawn_amount',
                    'balance',
                    'message'
                ])
        except Exception as e:
            print(f"CSV 파일 초기화 중 오류: {e}")
    
    def log_account(
        self,
        email: str,
        success: bool,
        withdrawn_amount: float,
        message: str = "",
        login_success: bool = False,
        withdrawal_success: bool = False,
        balance: float = 0.0
    ):
        """
        계정 처리 결과를 로깅합니다.
        
        Args:
            email: 계정 이메일
            success: 전체 성공 여부
            withdrawn_amount: 출금 금액
            message: 메시지
            login_success: 로그인 성공 여부
            withdrawal_success: 출금 성공 여부
            balance: 잔액
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "email": email,
            "success": success,
            "login_success": login_success,
            "withdrawal_success": withdrawal_success,
            "withdrawn_amount": withdrawn_amount,
            "balance": balance,
            "message": message
        }
        
        self.logs.append(log_entry)
        
        # CSV에 즉시 기록
        try:
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    log_entry["timestamp"],
                    log_entry["email"],
                    log_entry["success"],
                    log_entry["login_success"],
                    log_entry["withdrawal_success"],
                    log_entry["withdrawn_amount"],
                    log_entry["balance"],
                    log_entry["message"]
                ])
        except Exception as e:
            print(f"CSV 로그 기록 중 오류: {e}")
        
        # JSON 로그에도 추가
        self._save_json_log()
    
    def _save_json_log(self):
        """JSON 로그 파일을 저장합니다."""
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.logs, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"JSON 로그 저장 중 오류: {e}")
    
    def generate_summary(self, stats: Dict) -> str:
        """
        처리 결과 요약을 생성합니다.
        
        Args:
            stats: 통계 딕셔너리
        
        Returns:
            요약 문자열
        """
        total = stats.get('total', 1)
        success = stats.get('success', 0)
        failed = stats.get('failed', 0)
        skipped = stats.get('skipped', 0)
        
        summary = f"""
{'='*60}
출금 처리 요약
{'='*60}
총 계정 수: {total}
성공: {success}
실패: {failed}
스킵: {skipped}
총 출금 금액: {stats.get('total_withdrawn', 0.0):.2f}
성공률: {(success / total * 100) if total > 0 else 0:.2f}%
{'='*60}
"""
        return summary
    
    def save_summary(self, stats: Dict, summary_file: str = "summary.txt"):
        """
        요약을 파일로 저장합니다.
        
        Args:
            stats: 통계 딕셔너리
            summary_file: 요약 파일 경로
        """
        try:
            summary = self.generate_summary(stats)
            with open(summary_file, 'w', encoding='utf-8') as f:
                f.write(summary)
                f.write(f"\n생성 시간: {datetime.now().isoformat()}\n")
            print(f"요약이 저장되었습니다: {summary_file}")
        except Exception as e:
            print(f"요약 저장 중 오류: {e}")

