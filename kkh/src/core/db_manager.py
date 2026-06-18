import os
import sqlite3
import json
from datetime import datetime
from cryptography.fernet import Fernet

# --- Encryption Setup ---
# dev.md '4-C'에 따라 암호화 키를 환경 변수에서 로드합니다.
# 이 키는 미리 생성되어 안전하게 저장되어야 합니다.
# 예: key = Fernet.generate_key(); print(key)
ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # 환경 변수가 없을 경우, 임시 경고를 출력하고 넘어갑니다.
    # 실제 운영 환경에서는 raise ValueError를 통해 실행을 중단시켜야 합니다.
    print("경고: DB_ENCRYPTION_KEY 환경 변수가 설정되지 않았습니다. 암호화 기능이 비활성화됩니다.")
    cipher_suite = None
else:
    cipher_suite = Fernet(ENCRYPTION_KEY.encode())

# --- Database Path Setup ---
# 프로젝트 루트에 데이터베이스 파일을 생성합니다.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))
DB_PATH = os.path.join(PROJECT_ROOT, "agent_data.db")

def get_db_connection():
    """데이터베이스 연결을 생성하고 반환합니다."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """dev.md '4-C'에 명시된 스키마에 따라 테이블을 생성합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 사용자 정보 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL UNIQUE,
        timezone TEXT DEFAULT 'Asia/Seoul'
    );
    """)
    
    # Google API 인증 토큰 저장 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS auth_tokens (
        user_id TEXT PRIMARY KEY,
        token_data BLOB NOT NULL, -- 암호화된 JSON 토큰 데이터
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    );
    """)
    
    # 대화 컨텍스트 관리를 위한 최근 이벤트 기록 테이블
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS event_history (
        user_id TEXT PRIMARY KEY,
        last_event_id TEXT, -- 마지막으로 생성/조회된 이벤트의 ID 저장
        updated_at DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    );
    """)
    
    conn.commit()
    conn.close()
    print("DEBUG: Database tables created or already exist.")

# --- CRUD Functions ---

# User CRUD
def add_or_get_user(user_id: str, timezone: str = 'Asia/Seoul') -> dict:
    """사용자가 존재하면 정보를 반환하고, 없으면 새로 추가한 후 반환합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if user:
        conn.close()
        return dict(user)
    else:
        cursor.execute("INSERT INTO users (user_id, timezone) VALUES (?, ?)", (user_id, timezone))
        conn.commit()
        new_user = {"id": cursor.lastrowid, "user_id": user_id, "timezone": timezone}
        conn.close()
        return new_user

# Auth Token CRUD (with encryption)
def save_auth_token(user_id: str, token_dict: dict):
    """사용자의 인증 토큰을 암호화하여 데이터베이스에 저장합니다."""
    if not cipher_suite:
        raise RuntimeError("암호화 키가 설정되지 않아 토큰을 저장할 수 없습니다.")
    token_json = json.dumps(token_dict)
    encrypted_token = cipher_suite.encrypt(token_json.encode('utf-8'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # ON CONFLICT REPLACE는 이미 존재하는 user_id에 대해 UPDATE를 수행합니다.
    cursor.execute(
        "INSERT OR REPLACE INTO auth_tokens (user_id, token_data) VALUES (?, ?)",
        (user_id, encrypted_token)
    )
    conn.commit()
    conn.close()

def get_auth_token(user_id: str) -> dict | None:
    """데이터베이스에서 사용자의 인증 토큰을 복호화하여 반환합니다."""
    if not cipher_suite:
        raise RuntimeError("암호화 키가 설정되지 않아 토큰을 조회할 수 없습니다.")
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT token_data FROM auth_tokens WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row and row['token_data']:
        decrypted_token = cipher_suite.decrypt(row['token_data'])
        return json.loads(decrypted_token.decode('utf-8'))
    return None

# Event History CRUD
def update_event_history(user_id: str, last_event_id: str):
    """사용자의 마지막 이벤트 ID를 기록합니다."""
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO event_history (user_id, last_event_id, updated_at) VALUES (?, ?, ?)",
        (user_id, last_event_id, now)
    )
    conn.commit()
    conn.close()

def get_last_event_id(user_id: str) -> str | None:
    """사용자의 마지막 이벤트 ID를 조회합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT last_event_id FROM event_history WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row['last_event_id'] if row else None

if __name__ == '__main__':
    print("데이터베이스 관리 모듈 테스트를 시작합니다.")
    
    # 1. 테이블 생성
    create_tables()
    
    # 2. 환경 변수 확인 및 테스트 진행
    if not cipher_suite:
        print("\n테스트를 건너뛸 수 없습니다. DB_ENCRYPTION_KEY 환경 변수를 설정해주세요.")
    else:
        # 여기에 테스트 코드를 추가할 수 있습니다.
        print("\n데이터베이스 모듈이 준비되었습니다. (암호화 활성화)")
        # 예: add_or_get_user("test_user"), save_auth_token(...) 등
        pass