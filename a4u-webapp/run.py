from app import create_app, db
from app.models import User, ResumeTemplate
import os

app = create_app()

def _default_template(name):
    return f"""<!DOCTYPE html>
<html lang="ko">
<head><meta charset="utf-8"/><title>{name} 이력서</title>
<style>
body {{ font-family: 'Inter', sans-serif; max-width: 800px; margin: 40px auto; padding: 0 24px; color: #111c2d; }}
h1 {{ color: #3525cd; font-size: 28px; margin-bottom: 4px; }}
.section {{ margin-top: 28px; border-top: 2px solid #e7eeff; padding-top: 16px; }}
.section h2 {{ color: #3525cd; font-size: 14px; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 12px; }}
.item {{ margin-bottom: 16px; }}
.item-title {{ font-weight: 600; }}
.item-sub {{ color: #6b7280; font-size: 14px; }}
</style>
</head>
<body>
<h1>홍길동</h1>
<p style="color:#6b7280;font-size:14px;">hong@example.com · 010-0000-0000 · 서울시</p>
<div class="section">
  <h2>경력</h2>
  <div class="item">
    <div class="item-title">시니어 개발자 — ABC 회사</div>
    <div class="item-sub">2020.03 ~ 현재</div>
    <ul style="font-size:14px;margin-top:6px;padding-left:18px;color:#374151;">
      <li>주요 업무 내용을 여기에 작성합니다.</li>
    </ul>
  </div>
</div>
<div class="section">
  <h2>학력</h2>
  <div class="item">
    <div class="item-title">한국대학교 컴퓨터공학과</div>
    <div class="item-sub">2014.03 ~ 2018.02 졸업</div>
  </div>
</div>
<div class="section">
  <h2>기술</h2>
  <p style="font-size:14px;">Python, Flask, SQL, JavaScript, React</p>
</div>
</body>
</html>"""

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email='admin@a4u.com').first():
            admin = User(
                email='admin@a4u.com',
                name='관리자',
                is_admin=True,
                status='active'
            )
            admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin1234'))
            db.session.add(admin)

        if ResumeTemplate.query.count() == 0:
            seed_templates = [
                ResumeTemplate(name='IT 개발자형', description='소프트웨어 개발자를 위한 기술 스택 중심 이력서', category='it', html_content=_default_template('IT 개발자형'), is_active=True),
                ResumeTemplate(name='경영 관리자형', description='프로젝트 관리 및 리더십 경험을 강조한 이력서', category='management', html_content=_default_template('경영 관리자형'), is_active=True),
                ResumeTemplate(name='일반 범용형', description='다양한 직군에 활용 가능한 기본 이력서 템플릿', category='general', html_content=_default_template('일반 범용형'), is_active=True),
            ]
            for t in seed_templates:
                db.session.add(t)

        db.session.commit()
        print("DB initialized.")

if __name__ == '__main__':
    init_db()
    PORT = os.environ.get('PORT', 5000)
    print(f"Server is running at http://localhost:{PORT}")
    print(f"Admin console: http://localhost:{PORT}/admin")
    app.run(host='0.0.0.0', port=int(PORT), debug=True)