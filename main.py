"""
메인 실행 스크립트
전체 프로세스를 오케스트레이션합니다.
"""
import json
import sys
from account_manager import AccountManager
from proxy_manager import ProxyManager
from captcha_solver import CaptchaSolver
from account_processor import AccountProcessor
from logger import Logger


def load_config(config_file: str = "config.json") -> dict:
    """설정 파일을 로드합니다."""
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        print(f"설정 파일을 찾을 수 없습니다: {config_file}")
        print("config.json.example을 참고하여 config.json을 생성하세요.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"설정 파일 파싱 오류: {e}")
        sys.exit(1)


def validate_config(config: dict) -> bool:
    """설정이 유효한지 확인합니다."""
    required_keys = ['account_file', 'destination_wallet', '2captcha_api_key']
    
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"필수 설정이 누락되었습니다: {key}")
            return False
    
    return True


def main():
    """메인 함수"""
    print("="*60)
    print("Rollbet 계정 출금 자동화 시스템")
    print("="*60)
    
    # 설정 로드
    config = load_config()
    
    if not validate_config(config):
        print("설정 검증 실패. 프로그램을 종료합니다.")
        sys.exit(1)
    
    # 2captcha 잔액 확인
    captcha_solver = CaptchaSolver(config['2captcha_api_key'])
    balance = captcha_solver.get_balance()
    if balance is not None:
        print(f"2captcha 잔액: ${balance:.2f}")
        if balance < 1.0:
            print("경고: 2captcha 잔액이 부족할 수 있습니다.")
    else:
        print("2captcha 잔액 확인 실패")
    
    # 계정 관리자 초기화
    print(f"\n계정 파일 로드 중: {config['account_file']}")
    account_manager = AccountManager(config['account_file'])
    accounts = account_manager.load_accounts()
    
    if not accounts:
        print("로드된 계정이 없습니다. 프로그램을 종료합니다.")
        sys.exit(1)
    
    # 프록시 관리자 초기화
    proxy_manager = None
    if config.get('proxy_file'):
        print(f"\n프록시 파일 로드 중: {config['proxy_file']}")
        proxy_manager = ProxyManager(config['proxy_file'])
        proxies = proxy_manager.load_proxies()
        if not proxies:
            print("경고: 프록시가 로드되지 않았습니다. 프록시 없이 진행합니다.")
    else:
        print("프록시 파일이 설정되지 않았습니다. 프록시 없이 진행합니다.")
        # 빈 프록시 관리자 생성
        proxy_manager = ProxyManager("")
    
    # 계정 처리기 초기화
    processor = AccountProcessor(
        account_manager,
        proxy_manager,
        captcha_solver,
        config
    )
    
    try:
        # 브라우저 시작
        print("\n브라우저 시작 중...")
        processor.start()
        
        # 모든 계정 처리
        print(f"\n총 {len(accounts)}개의 계정 처리 시작...")
        stats = processor.process_all_accounts()
        
        # 결과 출력
        logger = Logger()
        summary = logger.generate_summary(stats)
        print(summary)
        
        # 요약 저장
        logger.save_summary(stats)
        
        print("\n처리 완료!")
        
    except KeyboardInterrupt:
        print("\n\n사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n오류 발생: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 브라우저 종료
        print("\n브라우저 종료 중...")
        processor.stop()
        print("프로그램 종료")


if __name__ == "__main__":
    main()

