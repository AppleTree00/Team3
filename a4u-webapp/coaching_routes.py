"""
coaching_routes.py — AI 코칭 API
샘플 3종(IT개발자, 경영관리자, 일반범용) Few-shot 기반 프롬프트
API 키 없으면 Mock 피드백 반환
"""
import os
import json
from flask import Blueprint, request, jsonify

coaching_bp = Blueprint('coaching_bp', __name__, url_prefix='/api')

# ─────────────────────────────────────────────
# Few-shot 프롬프트 정의 (샘플 3종)
# ─────────────────────────────────────────────
FEW_SHOT_EXAMPLES = {
    'it': {
        'label': 'IT 개발자형',
        'system': """당신은 IT 개발자 이력서 전문 코치입니다. 
다음 기준으로 이력서를 분석하고 구체적인 개선안을 제시하세요:
1. 기술 스택 표현의 명확성 (버전, 경험 연수 포함)
2. 프로젝트 성과의 수치화 (예: "API 응답속도 40% 개선")
3. 오픈소스 기여, GitHub 활동 등 증빙 가능한 실적
4. JD 키워드 매칭률 향상 방법""",
        'examples': [
            {
                'resume_snippet': '파이썬으로 웹 개발을 했습니다.',
                'coaching': '▶ 개선 전: "파이썬으로 웹 개발을 했습니다."\n▶ 개선 후: "Python 3.11 + FastAPI 기반 RESTful API 서버 개발 (월 100만 요청 처리, 응답 시간 200ms 이하 유지)"\n\n💡 팁: 언어/프레임워크 버전을 명시하고, 규모와 성과를 수치로 표현하세요.'
            },
            {
                'resume_snippet': 'React로 프론트엔드를 개발했습니다.',
                'coaching': '▶ 개선 전: "React로 프론트엔드를 개발했습니다."\n▶ 개선 후: "React 18 + TypeScript로 사내 ERP 프론트엔드 구축 (화면 30+ 개, Lighthouse 성능 점수 90 이상 달성)"\n\n💡 팁: 컴포넌트 수, 성능 지표 등 측정 가능한 결과를 추가하세요.'
            }
        ]
    },
    'management': {
        'label': '경영 관리자형',
        'system': """당신은 경영/관리직 이력서 전문 코치입니다.
다음 기준으로 이력서를 분석하고 구체적인 개선안을 제시하세요:
1. 리더십과 팀 성과의 수치화 (예: "15명 팀 관리, 매출 23% 성장")
2. 의사결정 과정과 비즈니스 임팩트 서술
3. 전략 기획, 예산 관리, KPI 달성 사례
4. 이해관계자 커뮤니케이션 역량 표현""",
        'examples': [
            {
                'resume_snippet': '팀을 이끌며 프로젝트를 완수했습니다.',
                'coaching': '▶ 개선 전: "팀을 이끌며 프로젝트를 완수했습니다."\n▶ 개선 후: "15명 규모 제품 개발팀 리드, 6개월 내 신규 서비스 론칭 (목표 대비 2주 단축, 출시 첫 달 MAU 5만 명 달성)"\n\n💡 팁: 팀 규모, 기간, 결과를 구체적 수치로 명시하세요.'
            },
            {
                'resume_snippet': '예산을 관리했습니다.',
                'coaching': '▶ 개선 전: "예산을 관리했습니다."\n▶ 개선 후: "연 30억 원 규모 마케팅 예산 기획 및 집행, 전년 대비 ROI 18% 향상 (비용 절감 4.2억 원)"\n\n💡 팁: 예산 규모와 달성 성과를 반드시 수치화하세요.'
            }
        ]
    },
    'general': {
        'label': '일반 범용형',
        'system': """당신은 범용 이력서 전문 코치입니다.
다음 기준으로 이력서를 분석하고 구체적인 개선안을 제시하세요:
1. 직무 핵심 역량과 경험의 연결성
2. 성과 중심 서술 (업무 나열 → 결과 중심으로)
3. 자기소개서와의 일관성
4. 명확하고 간결한 표현 (불필요한 수식어 제거)""",
        'examples': [
            {
                'resume_snippet': '고객 응대를 담당했습니다.',
                'coaching': '▶ 개선 전: "고객 응대를 담당했습니다."\n▶ 개선 후: "일 평균 50건 고객 문의 처리, CS 만족도 4.7/5.0 유지 (월별 VOC 분석 및 개선안 도출)"\n\n💡 팁: 처리 건수와 만족도 같은 측정 지표를 활용하세요.'
            },
            {
                'resume_snippet': '문서 작성을 했습니다.',
                'coaching': '▶ 개선 전: "문서 작성을 했습니다."\n▶ 개선 후: "부서 주간 보고서 및 경영진 월간 대시보드 작성 (임원 3명 직보, 데이터 시각화로 의사결정 소요 시간 30% 단축)"\n\n💡 팁: 문서의 목적, 독자, 비즈니스 임팩트를 명확히 서술하세요.'
            }
        ]
    }
}

UNAVAILABLE_SAMPLE_MSG = (
    "현재 이 기능은 고도화 단계에 있습니다. "
    "업데이트 이후 사용 가능하니 잠시만 기다려주세요.\n\n"
    "지원 가능한 샘플 유형: IT 개발자형(it), 경영 관리자형(management), 일반 범용형(general)"
)


def _build_prompt(sample_type: str, resume_text: str, focus: str) -> tuple[str, str]:
    """system prompt + user message 반환"""
    config = FEW_SHOT_EXAMPLES.get(sample_type)
    if not config:
        return None, None

    examples_text = '\n\n'.join([
        f"[예시 {i+1}]\n입력: {ex['resume_snippet']}\n코칭: {ex['coaching']}"
        for i, ex in enumerate(config['examples'])
    ])

    system_prompt = f"""{config['system']}

=== Few-shot 예시 ===
{examples_text}

=== 지침 ===
- 반드시 한국어로 응답하세요.
- "▶ 개선 전 / ▶ 개선 후 / 💡 팁" 형식을 사용하세요.
- 3~5개의 구체적 개선 포인트를 제시하세요.
- 수치가 없는 경우 추정 수치를 제안해주세요.
"""
    user_msg = f"""다음 이력서 내용을 코칭해주세요.

[이력서 내용]
{resume_text}

[코칭 중점 사항]
{focus or '전체적인 표현 개선 및 성과 수치화'}
"""
    return system_prompt, user_msg


def _call_openai(system_prompt: str, user_msg: str) -> str:
    import openai
    client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_msg}
        ],
        max_tokens=1500,
        temperature=0.7
    )
    return response.choices[0].message.content


def _call_anthropic(system_prompt: str, user_msg: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))
    message = client.messages.create(
        model='claude-3-haiku-20240307',
        max_tokens=1500,
        system=system_prompt,
        messages=[{'role': 'user', 'content': user_msg}]
    )
    return message.content[0].text


def _mock_coaching(sample_type: str, resume_text: str) -> str:
    """API 키 없을 때 샘플 기반 Mock 코칭 반환"""
    config = FEW_SHOT_EXAMPLES.get(sample_type, FEW_SHOT_EXAMPLES['general'])
    label = config['label']
    preview = resume_text[:100].replace('\n', ' ') if resume_text else '(내용 없음)'

    return f"""[{label} 코칭 결과 — 데모 모드]

📋 분석 대상: "{preview}..."

▶ 개선 포인트 1: 성과 수치화
현재 서술에서 구체적인 수치(%, 건수, 금액)가 부족합니다.
💡 팁: "담당했습니다" → "OOO 건/월 처리, 성과율 XX% 달성"

▶ 개선 포인트 2: 동사 강화
업무 서술에 수동적 표현이 많습니다.
💡 팁: "했습니다" → "주도했습니다 / 달성했습니다 / 구축했습니다"

▶ 개선 포인트 3: 키워드 최적화
채용공고 핵심 키워드와의 매칭을 높이세요.
💡 팁: JD에서 반복 등장하는 용어를 이력서에 자연스럽게 반영하세요.

▶ 개선 포인트 4: STAR 구조 적용
상황(Situation) → 과제(Task) → 행동(Action) → 결과(Result)로 서술하세요.

---
⚠️ 이 결과는 데모 목적의 Mock 응답입니다.
실제 AI 코칭을 사용하려면 OPENAI_API_KEY 또는 ANTHROPIC_API_KEY를 설정하세요.
"""


# ─────────────────────────────────────────────
# API 엔드포인트
# ─────────────────────────────────────────────
@coaching_bp.route('/coaching', methods=['POST'])
def coaching():
    data = request.get_json(silent=True) or {}
    resume_text = (data.get('resume_text') or '').strip()
    sample_type = (data.get('sample_type') or 'general').lower()
    focus = (data.get('focus') or '').strip()

    if not resume_text:
        return jsonify(success=False, message='이력서 내용을 입력해주세요.'), 400

    # 지원 범위 확인
    if sample_type not in FEW_SHOT_EXAMPLES:
        return jsonify(
            success=False,
            message=UNAVAILABLE_SAMPLE_MSG,
            supported_types=list(FEW_SHOT_EXAMPLES.keys())
        ), 422

    system_prompt, user_msg = _build_prompt(sample_type, resume_text, focus)

    openai_key = os.environ.get('OPENAI_API_KEY', '')
    anthropic_key = os.environ.get('ANTHROPIC_API_KEY', '')

    coaching_result = None
    provider = 'mock'

    if openai_key:
        try:
            coaching_result = _call_openai(system_prompt, user_msg)
            provider = 'openai'
        except Exception as e:
            print(f"OpenAI error: {e}")

    if coaching_result is None and anthropic_key:
        try:
            coaching_result = _call_anthropic(system_prompt, user_msg)
            provider = 'anthropic'
        except Exception as e:
            print(f"Anthropic error: {e}")

    if coaching_result is None:
        coaching_result = _mock_coaching(sample_type, resume_text)
        provider = 'mock'

    return jsonify(
        success=True,
        coaching=coaching_result,
        sample_type=sample_type,
        sample_label=FEW_SHOT_EXAMPLES[sample_type]['label'],
        provider=provider
    )


@coaching_bp.route('/coaching/samples', methods=['GET'])
def coaching_samples():
    """지원 가능한 샘플 타입 목록"""
    import os
    ai_available = bool(os.environ.get('OPENAI_API_KEY') or os.environ.get('ANTHROPIC_API_KEY'))
    return jsonify(
        success=True,
        ai_available=ai_available,
        samples=[
            {'type': k, 'label': v['label']}
            for k, v in FEW_SHOT_EXAMPLES.items()
        ]
    )
