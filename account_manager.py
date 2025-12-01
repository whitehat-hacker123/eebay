"""
계정 관리 모듈
계정 정보 파일을 읽고 파싱하여 관리합니다.
"""
import csv
import json
import re
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
        - JSON: [{"email": "...", "password": "..."}] 또는 [{"user": "...", "pass": "..."}]
        - JSON (배열 없이): {"user": "...", "pass": "..."}, {"user": "...", "pass": "..."}
        
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
                # TXT 파일이지만 JSON 형식일 수 있음
                self.accounts = self._load_txt()
            
            print(f"총 {len(self.accounts)}개의 계정을 로드했습니다.")
            return self.accounts
        
        except Exception as e:
            print(f"계정 파일 로드 중 오류 발생: {e}")
            return []
    
    def _load_txt(self) -> List[Dict[str, str]]:
        """TXT 파일 형식 로드 (email:password 또는 JSON 형식)"""
        accounts = []
        
        # 먼저 파일 전체를 읽어서 JSON 형식인지 확인
        try:
            with open(self.account_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            # JSON 형식인지 확인 (중괄호가 있으면 JSON으로 간주)
            if '{' in content:
                # JSON 형식으로 파싱 시도
                try:
                    # 여러 JSON 객체가 쉼표로 구분된 경우 처리
                    # 중첩된 중괄호를 고려하여 각 JSON 객체 추출
                    json_objects = []
                    brace_count = 0
                    current_obj = ""
                    in_string = False
                    escape_next = False
                    
                    for char in content:
                        if escape_next:
                            current_obj += char
                            escape_next = False
                            continue
                        
                        if char == '\\':
                            escape_next = True
                            current_obj += char
                            continue
                        
                        if char == '"' and not escape_next:
                            in_string = not in_string
                            current_obj += char
                            continue
                        
                        if not in_string:
                            if char == '{':
                                if brace_count == 0:
                                    current_obj = char
                                else:
                                    current_obj += char
                                brace_count += 1
                            elif char == '}':
                                current_obj += char
                                brace_count -= 1
                                if brace_count == 0:
                                    json_objects.append(current_obj.strip())
                                    current_obj = ""
                            elif brace_count > 0:
                                current_obj += char
                        else:
                            current_obj += char
                    
                    # 마지막 객체가 있으면 추가
                    if current_obj.strip() and brace_count == 0:
                        json_objects.append(current_obj.strip())
                    
                    if json_objects:
                        # 각 객체를 파싱
                        for obj_str in json_objects:
                            # 쉼표 제거
                            obj_str = obj_str.rstrip(',').strip()
                            try:
                                item = json.loads(obj_str)
                                if isinstance(item, dict):
                                    # user/pass 필드 지원
                                    email = item.get('user') or item.get('email') or item.get('username')
                                    password = item.get('pass') or item.get('password')
                                    
                                    if email and password:
                                        accounts.append({
                                            'email': str(email).strip(),
                                            'password': str(password).strip()
                                        })
                            except json.JSONDecodeError:
                                continue
                        
                        if accounts:
                            return accounts
                    
                    # 객체를 찾지 못한 경우 배열로 감싸서 시도
                    if not content.startswith('['):
                        # 마지막 쉼표 제거 후 배열로 감싸기
                        content_cleaned = content.rstrip(',').strip()
                        content = '[' + content_cleaned + ']'
                    
                    data = json.loads(content)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                # user/pass 필드 지원
                                email = item.get('user') or item.get('email') or item.get('username')
                                password = item.get('pass') or item.get('password')
                                
                                if email and password:
                                    accounts.append({
                                        'email': str(email).strip(),
                                        'password': str(password).strip()
                                    })
                        if accounts:
                            return accounts
                except json.JSONDecodeError as e:
                    # JSON 파싱 실패하면 일반 TXT 형식으로 처리
                    pass
        except Exception as e:
            pass
        
        # 일반 TXT 형식 (email:password)
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
        """JSON 파일 형식 로드 (user/pass 또는 email/password 필드 지원)"""
        with open(self.account_file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # 배열로 감싸지 않은 경우 배열로 감싸기
        if not content.startswith('['):
            content = '[' + content + ']'
        
        data = json.loads(content)
        
        accounts = []
        
        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    # user/pass 필드 지원
                    email = item.get('user') or item.get('email') or item.get('username')
                    password = item.get('pass') or item.get('password')
                    
                    if email and password:
                        accounts.append({
                            'email': email.strip(),
                            'password': password.strip()
                        })
        elif isinstance(data, dict):
            if 'accounts' in data:
                for item in data['accounts']:
                    if isinstance(item, dict):
                        email = item.get('user') or item.get('email') or item.get('username')
                        password = item.get('pass') or item.get('password')
                        
                        if email and password:
                            accounts.append({
                                'email': email.strip(),
                                'password': password.strip()
                            })
            else:
                # 단일 객체인 경우
                email = data.get('user') or data.get('email') or data.get('username')
                password = data.get('pass') or data.get('password')
                
                if email and password:
                    accounts.append({
                        'email': email.strip(),
                        'password': password.strip()
                    })
        
        return accounts
    
    def get_accounts(self) -> List[Dict[str, str]]:
        """로드된 계정 리스트를 반환합니다."""
        return self.accounts
    
    def get_account_count(self) -> int:
        """계정 개수를 반환합니다."""
        return len(self.accounts)

