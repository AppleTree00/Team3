import os
from collections import deque
import time
from openai import OpenAI

from dotenv import load_dotenv

# .env 파일 읽기
load_dotenv()

# 1. OpenAI 클라이언트 초기화 (환경 변수에 OPENAI_API_KEY가 등록되어 있어야 합니다)
# 만약 직접 넣으려면: client = OpenAI(api_key="your-api-key-here")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. 초기 목표 및 작업 큐 설정
OBJECTIVE = "서울 지역 비건 빵집 창업을 위한 시장 조사"
task_queue = deque([
    {"task_id": 1, "task_name": "서울의 유명 비건 빵집 리스트업 하기"}
])
task_id_counter = 1

# 사용할 모델 설정 (가성비와 성능이 좋은 gpt-4o-mini 또는 gpt-4o 추천)
MODEL_NAME = "gpt-4o-mini"

# ==========================================
# 🤖 OpenAI 연동 에이전트(Agent) 함수 정의
# ==========================================

def execution_agent(objective: str, task: str) -> str:
    """[에이전트 1: 실행] GPT를 이용해 주어진 작업을 실제로 수행합니다."""
    print(f"\n[🔄 실행 중] 현재 작업: {task}")
    
    prompt = f"""당신은 자율형 AI 에이전트의 실행 팀입니다.
최종 목표: {objective}
수행할 작업: {task}

이 작업을 수행하고 구체적이고 유용한 결과 데이터를 도출해 주세요."""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response.choices[0].message.content.strip()


def task_creation_agent(objective: str, result: str, current_task: str) -> list:
    """[에이전트 2: 작업 생성] 완료된 결과를 분석하여 다음에 해야 할 작업을 생성합니다."""
    print(f"[💡 작업 생성 중] 이전 결과 분석 및 새 작업 생성 중...")
    
    prompt = f"""당신은 자율형 AI 에이전트의 기획 팀입니다.
최종 목표: {objective}
최근 완료한 작업: {current_task}
작업 결과: {result}

이 결과를 바탕으로 최종 목표를 달성하기 위해 '새롭게 추가해야 할 다음 작업 목록'을 브레인스토밍해 주세요.
주의: 기존 작업과 겹치지 않는 새로운 작업이어야 합니다.

[응답 형식]
각 작업을 한 줄에 하나씩만 작성해 주세요. 글머리 기호(-나 *)나 번호(1., 2.)는 붙이지 마세요.
예시:
홍대 지역 비건 빵집 방문객 유동인구 분석
비건 베이커리 원재료 공급망 조사"""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    # 응답 텍스트를 줄 단위로 쪼개어 리스트로 변환 및 정제
    raw_tasks = response.choices[0].message.content.strip().split("\n")
    new_tasks = [t.strip().lstrip("-*•0123456789. ") for t in raw_tasks if t.strip()]
    return new_tasks


def prioritization_agent(objective: str, current_tasks: list) -> list:
    """[에이전트 3: 우선순위 정렬] 현재 남은 작업들을 목표 달성에 가장 효과적인 순서로 재배치합니다."""
    print(f"[📊 우선순위 정렬 중] 작업 큐의 순서를 최적화하는 중...")
    
    tasks_string = "\n".join(current_tasks)
    prompt = f"""당신은 자율형 AI 에이전트의 관리 팀입니다.
최종 목표: {objective}
현재 대기 중인 작업들:
{tasks_string}

최종 목표를 가장 빠르고 효율적으로 달성할 수 있도록 위 작업들의 우선순위를 다시 정렬해 주세요.
주의: 리스트에 없는 새로운 작업을 추가하지 마십시오.

[응답 형식]
정렬된 작업을 한 줄에 하나씩만 작성해 주세요. 글머리 기호나 번호는 붙이지 마세요."""

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3 # 정렬은 논리적이어야 하므로 창의성(temperature)을 낮춤
    )
    
    raw_tasks = response.choices[0].message.content.strip().split("\n")
    sorted_tasks = [t.strip().lstrip("-*•0123456789. ") for t in raw_tasks if t.strip()]
    return sorted_tasks

# ==========================================
# 🚀 메인 루프 (BabyAGI 코어 로직)
# ==========================================

print("="*60)
print(f"🎯 실전 BabyAGI 가동 | 최종 목표: {OBJECTIVE}")
print("="*60)

# API 비용 및 무한 루프 방지를 위한 최대 반복 횟수 제한
max_iterations = 3 
iteration = 0

while task_queue and iteration < max_iterations:
    iteration += 1
    print(f"\n⚡ === [루프 {iteration} 단계 시작] ===")
    
    # 1. 큐에서 첫 번째 작업 꺼내기
    current_task = task_queue.popleft()
    print(f"📌 실행할 작업 ID {current_task['task_id']}: {current_task['task_name']}")
    
    # 2. 실행 에이전트 가동
    result = execution_agent(OBJECTIVE, current_task["task_name"])
    print(f"\n✅ [실행 결과]:\n{result}\n")
    
    # 3. 작업 생성 에이전트 가동
    new_task_names = task_creation_agent(OBJECTIVE, result, current_task["task_name"])
    print(f"➕ 새로 생성된 작업 목록: {new_task_names}")
    
    for name in new_task_names:
        task_id_counter += 1
        task_queue.append({"task_id": task_id_counter, "task_name": name})
    
    # 4. 우선순위 정렬 에이전트 가동
    task_names_in_queue = [t["task_name"] for t in task_queue] 
    
    if task_names_in_queue:
        sorted_task_names = prioritization_agent(OBJECTIVE, task_names_in_queue)
        
        # 정렬된 결과로 큐를 완전히 새로고침
        task_queue.clear()
        for i, name in enumerate(sorted_task_names):
            task_queue.append({"task_id": task_id_counter + i, "task_name": name})
            
    # 현재 루프 종료 후 큐 상태 브리핑
    print("\n📋 [현재 최적화된 대기 작업 목록]")
    for t in task_queue:
        print(f"  - [{t['task_id']}] {t['task_name']}")
    
    # API 과열 방지용 짧은 휴식
    time.sleep(2)

print("\n🎉 설정한 최대 루프에 도달하여 안전하게 BabyAGI를 종료합니다.")