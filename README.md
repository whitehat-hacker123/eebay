# Rollbet 계정 출금 자동화 시스템

rollbet.gg 사이트에 수천 개의 계정에 순차적으로 로그인하여 각 계정의 잔액을 출금하고, 모든 자금을 하나의 지갑 주소로 집중시키는 자동화 시스템입니다.

## 주요 기능

- 순차적 계정 처리 (계정 한 개씩)
- hCaptcha 자동 해결 (2captcha API 사용)
- 프록시 로테이션 지원
- 자동 로그인 및 출금
- 상세한 로깅 및 통계

## 요구사항

- Python 3.8 이상
- 2captcha API 키
- 계정 정보 파일
- 프록시 리스트 파일 (선택적)

## 설치

1. 저장소 클론 또는 파일 다운로드

2. Python 패키지 설치:
```bash
pip install -r requirements.txt
```

3. Playwright 브라우저 설치:
```bash
playwright install chromium
```

## 설정

1. `config.json` 파일을 열고 다음 정보를 입력하세요:

```json
{
  "account_file": "accounts.txt",
  "proxy_file": "proxies.txt",
  "destination_wallet": "YOUR_WALLET_ADDRESS",
  "2captcha_api_key": "YOUR_2CAPTCHA_API_KEY",
  "retry_count": 3,
  "timeout": 30,
  "delay_between_accounts": 5,
  "headless": true,
  "browser": "chromium"
}
```

- `destination_wallet`: 모든 자금을 모을 지갑 주소
- `2captcha_api_key`: 2captcha.com에서 발급받은 API 키
- `delay_between_accounts`: 계정 간 대기 시간 (초)
- `headless`: 헤드리스 모드 (true/false)

2. 계정 정보 파일 생성 (`accounts.txt`):

```
email:password
user1@example.com:password123
user2@example.com:password456
```

또는 CSV 형식:
```csv
email,password
user1@example.com,password123
user2@example.com,password456
```

3. 프록시 파일 생성 (`proxies.txt`) - 선택적:

```
ip:port
ip:port:username:password
127.0.0.1:8080
192.168.1.1:3128:user:pass
```

## 사용 방법

```bash
python main.py
```

프로그램은 다음 순서로 실행됩니다:
1. 설정 파일 로드
2. 계정 및 프록시 파일 로드
3. 각 계정에 대해 순차적으로:
   - 로그인
   - hCaptcha 해결 (2captcha 사용)
   - 잔액 확인
   - 출금 처리
   - 로그아웃
4. 결과 요약 출력 및 저장

## 출력 파일

- `withdrawal_log.csv`: 상세 로그 (CSV 형식)
- `withdrawal_log.json`: 상세 로그 (JSON 형식)
- `summary.txt`: 처리 결과 요약

## 주의사항

1. **2captcha 잔액 확인**: 프로그램 실행 전에 2captcha 계정에 충분한 잔액이 있는지 확인하세요.

2. **계정 간 대기 시간**: `delay_between_accounts` 설정을 적절히 조정하여 rate limiting을 피하세요.

3. **프록시 사용**: 대량의 계정을 처리할 경우 프록시 사용을 권장합니다.

4. **테스트**: 실제 사용 전에 소수의 계정으로 테스트해보세요.

5. **법적 고려사항**: 이 도구 사용 시 관련 법규 및 서비스 약관을 준수해야 합니다.

## 문제 해결

### 로그인 실패
- 계정 정보가 올바른지 확인
- hCaptcha 해결이 제대로 되는지 확인
- 프록시가 작동하는지 확인

### 출금 실패
- 출금 페이지 구조가 변경되었을 수 있음
- 최소 출금 금액 확인
- 출금 수수료 확인

### hCaptcha 해결 실패
- 2captcha API 키 확인
- 2captcha 잔액 확인
- 네트워크 연결 확인

## 라이선스

이 프로젝트는 개인 사용 목적으로 제공됩니다.

# jubilant-pancake
# jubilant-pancake
