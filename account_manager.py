"""
계정 관리 모듈
계정 정보 파일을 읽고 파싱하여 관리합니다.
"""
import csv
import json
from typing import List, Dict, Optional


class AccountManager:
    def __init__(self, account_file: str):
        """
        Args:
            account_file: 계정 정보가 담긴 파일 경로
        """
        self.account_file = account_file
        self.accounts: List[Dict[str, str]] = []
    
    def load_accounts(self) -> List[Dict[str, str]]:
        """
        계정 파일을 읽어서 파싱합니다.
        지원 형식:
        - TXT: email:password (한 줄에 하나)
        - CSV: email,password
        - JSON: [{"email": "...", "password": "..."}]
        
        Returns:
            계정 정보 리스트 [{"email": "...", "password": "..."}]
        """
        self.accounts = []
        
        try:
            if self.account_file.endswith('.json'):
                self.accounts = self._load_json()
            elif self.account_file.endswith('.csv'):
                self.accounts = self._load_csv()
            else:
                self.accounts = self._load_txt()
            
            print(f"총 {len(self.accounts)}개의 계정을 로드했습니다.")
            return self.accounts
        
        except Exception as e:
            print(f"계정 파일 로드 중 오류 발생: {e}")
            return []
    
    def _load_txt(self) -> List[Dict[str, str]]:
        """TXT 파일 형식 로드 (email:password)"""
        accounts = []
        with open(self.account_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if ':' not in line:
                    print(f"경고: {line_num}번째 줄 형식이 올바르지 않습니다: {line}")
                    continue
                
                parts = line.split(':', 1)
                if len(parts) == 2:
                    accounts.append({
                        'email': parts[0].strip(),
                        'password': parts[1].strip()
                    })
        
        return accounts
    
    def _load_csv(self) -> List[Dict[str, str]]:
        """CSV 파일 형식 로드"""
        accounts = []
        with open(self.account_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'email' in row and 'password' in row:
                    accounts.append({
                        'email': row['email'].strip(),
                        'password': row['password'].strip()
                    })
                elif len(row) >= 2:
                    # 첫 번째 컬럼이 email, 두 번째가 password라고 가정
                    keys = list(row.keys())
                    accounts.append({
                        'email': row[keys[0]].strip(),
                        'password': row[keys[1]].strip()
                    })
        
        return accounts
    
    def _load_json(self) -> List[Dict[str, str]]:
        """JSON 파일 형식 로드"""
        with open(self.account_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'accounts' in data:
            return data['accounts']
        else:
            return []
    
    def get_accounts(self) -> List[Dict[str, str]]:
        """로드된 계정 리스트를 반환합니다."""
        return self.accounts
    
    def get_account_count(self) -> int:
        """계정 개수를 반환합니다."""
        return len(self.accounts)

