import os
from datetime import datetime

from src.core.reporting import get_weekly_report_data, generate_html_report, send_email

def main():
    """주간 리포트를 생성하고 이메일로 발송하는 메인 함수."""
    print("주간 리포트 생성을 시작합니다...")
    
    try:
        # 1. 데이터 조회 및 가공
        print(" - 1/3: 데이터베이스에서 지난 주 데이터를 조회합니다...")
        report_data = get_weekly_report_data()
        
        if not report_data:
            print(" - 경고: 지난 주 데이터가 없어 리포트를 생성하지 않습니다.")
            return

        # 2. HTML 리포트 생성 및 이메일 발송
        print(" - 2/3: 조회된 데이터를 바탕으로 HTML 리포트를 생성합니다...")
        html_report = generate_html_report(report_data)
        print(" - 3/3: 생성된 리포트를 이메일로 발송합니다...")
        subject = f"AI 에이전트 주간 운영 리포트 ({datetime.now().strftime('%Y-%m-%d')})"
        send_email(subject, html_report, os.getenv("REPORT_RECIPIENT_EMAIL"))
    except Exception as e:
        print(f"\n리포트 생성 중 심각한 오류가 발생했습니다: {e}")

if __name__ == "__main__":
    main()