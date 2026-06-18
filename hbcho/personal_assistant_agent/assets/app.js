(() => {
  const STORAGE_KEY = "pa_agent_events_v1";
  const NOTIFIED_KEY = "pa_agent_notified_v1";
  const WEEKDAY_MAP = { "일": 0, "월": 1, "화": 2, "수": 3, "목": 4, "금": 5, "토": 6 };
  const KEYWORD_WEIGHT = ["마감", "면접", "발표", "계약", "결제", "제출", "시험", "보고", "승인", "데모"];

  const $ = (selector) => document.querySelector(selector);
  const $$ = (selector) => Array.from(document.querySelectorAll(selector));

  const elements = {
    agentInput: $("#agentInput"),
    runCommand: $("#runCommand"),
    agentResponse: $("#agentResponse"),
    eventList: $("#eventList"),
    rangeFilter: $("#rangeFilter"),
    searchFilter: $("#searchFilter"),
    eventForm: $("#eventForm"),
    formTitle: $("#formTitle"),
    eventId: $("#eventId"),
    title: $("#title"),
    date: $("#date"),
    time: $("#time"),
    duration: $("#duration"),
    importance: $("#importance"),
    reminderMinutes: $("#reminderMinutes"),
    notes: $("#notes"),
    resetForm: $("#resetForm"),
    submitEvent: $("#submitEvent"),
    metricTotal: $("#metricTotal"),
    metricSoon: $("#metricSoon"),
    metricHigh: $("#metricHigh"),
    toast: $("#toast"),
    seedDemo: $("#seedDemo"),
    exportData: $("#exportData"),
    importData: $("#importData"),
    askNotification: $("#askNotification"),
    testReminder: $("#testReminder")
  };

  let events = loadEvents();
  let notified = loadJson(NOTIFIED_KEY, {});

  function loadJson(key, fallback) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : fallback;
    } catch (error) {
      console.warn("LocalStorage load failed", error);
      return fallback;
    }
  }

  function saveJson(key, data) {
    localStorage.setItem(key, JSON.stringify(data));
  }

  function loadEvents() {
    const loaded = loadJson(STORAGE_KEY, []);
    return loaded.map(normalizeEvent).filter(Boolean);
  }

  function saveEvents() {
    saveJson(STORAGE_KEY, events);
    render();
  }

  function normalizeEvent(event) {
    if (!event || !event.title || !event.date || !event.time) return null;
    return {
      id: event.id || cryptoRandomId(),
      title: String(event.title).trim(),
      date: event.date,
      time: event.time,
      duration: Number(event.duration || 60),
      importance: event.importance || "medium",
      reminderMinutes: Number(event.reminderMinutes ?? 30),
      notes: event.notes || "",
      createdAt: event.createdAt || new Date().toISOString(),
      updatedAt: event.updatedAt || new Date().toISOString()
    };
  }

  function cryptoRandomId() {
    if (window.crypto && crypto.randomUUID) return crypto.randomUUID();
    return `evt_${Date.now()}_${Math.random().toString(16).slice(2)}`;
  }

  function toDateTime(event) {
    return new Date(`${event.date}T${event.time}:00`);
  }

  function pad(number) { return String(number).padStart(2, "0"); }
  function formatDateInput(date) { return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`; }
  function formatTimeInput(date) { return `${pad(date.getHours())}:${pad(date.getMinutes())}`; }

  function formatKoreanDateTime(event) {
    const dt = toDateTime(event);
    return new Intl.DateTimeFormat("ko-KR", {
      dateStyle: "medium",
      timeStyle: "short",
      weekday: "short"
    }).format(dt);
  }

  function escapeHtml(value = "") {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function getImportanceLabel(value) {
    return { low: "낮음", medium: "보통", high: "높음" }[value] || "보통";
  }

  function priorityFor(event) {
    const now = new Date();
    const start = toDateTime(event);
    const diffHours = (start - now) / 36e5;
    let score = 0;
    const reasons = [];

    if (event.importance === "high") { score += 45; reasons.push("중요도 높음"); }
    if (event.importance === "medium") { score += 22; reasons.push("중요도 보통"); }
    if (event.importance === "low") { score += 8; reasons.push("중요도 낮음"); }

    if (diffHours < 0) { score += 18; reasons.push("이미 지난 일정 확인 필요"); }
    else if (diffHours <= 24) { score += 38; reasons.push("24시간 이내"); }
    else if (diffHours <= 72) { score += 24; reasons.push("3일 이내"); }
    else if (diffHours <= 168) { score += 12; reasons.push("7일 이내"); }

    const searchable = `${event.title} ${event.notes}`;
    const matchedKeywords = KEYWORD_WEIGHT.filter((keyword) => searchable.includes(keyword));
    if (matchedKeywords.length) {
      score += Math.min(25, matchedKeywords.length * 9);
      reasons.push(`핵심 키워드: ${matchedKeywords.slice(0, 3).join(", ")}`);
    }

    if (hasConflict(event)) {
      score += 18;
      reasons.push("시간 충돌 가능성");
    }

    score = Math.min(100, Math.max(0, Math.round(score)));
    const level = score >= 70 ? "high" : score >= 42 ? "medium" : "low";
    const label = level === "high" ? "높음" : level === "medium" ? "중간" : "낮음";
    return { score, level, label, reason: reasons.join(" · ") || "일반 일정" };
  }

  function hasConflict(target) {
    const start = toDateTime(target).getTime();
    const end = start + target.duration * 60000;
    return events.some((event) => {
      if (event.id === target.id || event.date !== target.date) return false;
      const otherStart = toDateTime(event).getTime();
      const otherEnd = otherStart + event.duration * 60000;
      return start < otherEnd && end > otherStart;
    });
  }

  function render() {
    renderMetrics();
    renderEvents();
  }

  function renderMetrics() {
    const now = new Date();
    elements.metricTotal.textContent = events.length;
    elements.metricSoon.textContent = events.filter((event) => {
      const diffHours = (toDateTime(event) - now) / 36e5;
      return diffHours >= 0 && diffHours <= 24;
    }).length;
    elements.metricHigh.textContent = events.filter((event) => priorityFor(event).score >= 70).length;
  }

  function renderEvents() {
    const filtered = getFilteredEvents().sort((a, b) => toDateTime(a) - toDateTime(b));
    if (!filtered.length) {
      elements.eventList.innerHTML = `<div class="empty-state">조건에 맞는 일정이 없습니다. Agent 명령이나 직접 등록으로 일정을 추가해보세요.</div>`;
      return;
    }
    elements.eventList.innerHTML = filtered.map((event) => {
      const priority = priorityFor(event);
      const note = event.notes ? `<p class="event-note">${escapeHtml(event.notes)}</p>` : "";
      return `
        <article class="event-card">
          <div class="event-main">
            <h4>${escapeHtml(event.title)}</h4>
            <div class="event-meta">
              <span>📅 ${escapeHtml(formatKoreanDateTime(event))}</span>
              <span>⏱ ${event.duration}분</span>
              <span>⭐ 중요도 ${getImportanceLabel(event.importance)}</span>
              <span>🔔 ${event.reminderMinutes ? `${event.reminderMinutes}분 전` : "없음"}</span>
            </div>
            ${note}
            <div class="priority-box">
              <span class="tag ${priority.level}">우선순위 ${priority.label} · ${priority.score}점</span>
              <span class="tag neutral">${escapeHtml(priority.reason)}</span>
            </div>
          </div>
          <div class="event-actions">
            <button class="icon-btn" data-action="edit" data-id="${event.id}">편집</button>
            <button class="icon-btn danger" data-action="delete" data-id="${event.id}">삭제</button>
          </div>
        </article>`;
    }).join("");
  }

  function getFilteredEvents() {
    const range = elements.rangeFilter.value;
    const query = elements.searchFilter.value.trim().toLowerCase();
    const now = new Date();
    const today = formatDateInput(now);
    const tomorrowDate = new Date(now);
    tomorrowDate.setDate(now.getDate() + 1);
    const tomorrow = formatDateInput(tomorrowDate);

    return events.filter((event) => {
      const start = toDateTime(event);
      const diffDays = (start - new Date(`${today}T00:00:00`)) / 864e5;
      const matchesQuery = !query || `${event.title} ${event.notes}`.toLowerCase().includes(query);
      if (!matchesQuery) return false;
      if (range === "today") return event.date === today;
      if (range === "tomorrow") return event.date === tomorrow;
      if (range === "week") return diffDays >= 0 && diffDays < 8;
      if (range === "high") return priorityFor(event).score >= 70;
      return true;
    });
  }

  function setAgentResponse(html) {
    elements.agentResponse.innerHTML = `<strong>Agent 응답</strong>${html}`;
  }

  function showToast(message) {
    elements.toast.textContent = message;
    elements.toast.classList.add("show");
    window.setTimeout(() => elements.toast.classList.remove("show"), 3600);
  }

  function parseCommand(text) {
    const command = text.trim();
    if (!command) return { type: "empty" };
    if (/추천|우선순위|중요한/.test(command) && !/등록|추가|잡아|변경|수정/.test(command)) return { type: "recommend" };
    if (/조회|보여|목록|검색|알려/.test(command) && !/등록|추가|변경|수정|삭제/.test(command)) return { type: "query", text: command };
    if (/변경|수정|옮겨|바꿔/.test(command)) return { type: "change", text: command };
    if (/삭제|지워|취소/.test(command)) return { type: "delete", text: command };
    if (/등록|추가|잡아|생성/.test(command)) return { type: "create", text: command };
    return { type: "help", text: command };
  }

  function handleCommand() {
    const parsed = parseCommand(elements.agentInput.value);
    if (parsed.type === "empty") {
      setAgentResponse(`<p>요청 내용을 입력해주세요.</p>`);
      return;
    }
    const handlers = {
      create: handleCreateCommand,
      query: handleQueryCommand,
      change: handleChangeCommand,
      delete: handleDeleteCommand,
      recommend: handleRecommendCommand,
      help: handleHelpCommand
    };
    handlers[parsed.type](parsed.text);
  }

  function handleCreateCommand(text) {
    const start = parseDateTime(text);
    const title = inferTitle(text) || "새 일정";
    const importance = inferImportance(text);
    const event = normalizeEvent({
      title,
      date: formatDateInput(start),
      time: formatTimeInput(start),
      duration: inferDuration(text),
      importance,
      reminderMinutes: importance === "high" ? 60 : 30,
      notes: `Agent 명령으로 생성: ${text}`
    });
    events.push(event);
    saveEvents();
    const priority = priorityFor(event);
    setAgentResponse(`
      <p>일정을 등록했습니다.</p>
      <ul>
        <li>제목: ${escapeHtml(event.title)}</li>
        <li>날짜/시간: ${escapeHtml(formatKoreanDateTime(event))}</li>
        <li>우선순위: ${priority.label} (${priority.score}점)</li>
      </ul>`);
    showToast("일정이 등록되었습니다.");
  }

  function handleQueryCommand(text) {
    const matched = filterByTextTime(text, events).sort((a, b) => toDateTime(a) - toDateTime(b));
    if (!matched.length) {
      setAgentResponse(`<p>조건에 맞는 일정이 없습니다.</p>`);
      return;
    }
    setAgentResponse(`<p>${matched.length}개의 일정을 찾았습니다.</p><ul>${matched.slice(0, 6).map((event) => `<li>${escapeHtml(event.title)} — ${escapeHtml(formatKoreanDateTime(event))}</li>`).join("")}</ul>`);
  }

  function handleChangeCommand(text) {
    const target = findBestEvent(text);
    if (!target) {
      setAgentResponse(`<p>변경할 일정을 찾지 못했습니다. 목록에서 직접 편집하거나 제목을 더 구체적으로 입력해주세요.</p>`);
      return;
    }
    const start = parseDateTime(text, toDateTime(target));
    target.date = formatDateInput(start);
    target.time = formatTimeInput(start);
    const titleCandidate = inferTitle(text, true);
    if (titleCandidate && titleCandidate.length > 1 && !target.title.includes(titleCandidate)) target.title = titleCandidate;
    target.updatedAt = new Date().toISOString();
    saveEvents();
    setAgentResponse(`<p>일정을 변경했습니다.</p><ul><li>제목: ${escapeHtml(target.title)}</li><li>새 시간: ${escapeHtml(formatKoreanDateTime(target))}</li></ul>`);
    showToast("일정이 변경되었습니다.");
  }

  function handleDeleteCommand(text) {
    const target = findBestEvent(text);
    if (!target) {
      setAgentResponse(`<p>삭제할 일정을 찾지 못했습니다. 제목을 더 구체적으로 입력하거나 목록의 삭제 버튼을 사용해주세요.</p>`);
      return;
    }
    events = events.filter((event) => event.id !== target.id);
    saveEvents();
    setAgentResponse(`<p>일정을 삭제했습니다: ${escapeHtml(target.title)}</p>`);
    showToast("일정이 삭제되었습니다.");
  }

  function handleRecommendCommand() {
    const upcoming = events
      .filter((event) => toDateTime(event) >= new Date(Date.now() - 864e5))
      .map((event) => ({ event, priority: priorityFor(event) }))
      .sort((a, b) => b.priority.score - a.priority.score || toDateTime(a.event) - toDateTime(b.event));
    if (!upcoming.length) {
      setAgentResponse(`<p>추천할 예정 일정이 없습니다.</p>`);
      return;
    }
    setAgentResponse(`<p>가장 먼저 챙길 일정은 <strong>${escapeHtml(upcoming[0].event.title)}</strong>입니다.</p><ul>${upcoming.slice(0, 5).map(({ event, priority }) => `<li>${escapeHtml(event.title)} — ${priority.score}점 · ${escapeHtml(priority.reason)} · ${escapeHtml(formatKoreanDateTime(event))}</li>`).join("")}</ul>`);
  }

  function handleHelpCommand(text) {
    setAgentResponse(`<p>아직 이해하지 못한 요청입니다. 아래 형식으로 입력해보세요.</p><ul><li>다음 주 화요일 오후 2시에 회의 등록해줘</li><li>오늘 일정 조회해줘</li><li>회의 시간을 오후 3시로 변경해줘</li><li>중요한 일정 추천해줘</li></ul>`);
  }

  function parseDateTime(text, fallbackDate = new Date()) {
    const base = parseDate(text, fallbackDate);
    const time = parseTime(text, fallbackDate);
    base.setHours(time.hours, time.minutes, 0, 0);
    return base;
  }

  function parseDate(text, fallbackDate = new Date()) {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const normalized = text.replace(/\s+/g, " ");

    const iso = normalized.match(/(20\d{2})[-.\/년\s]+(\d{1,2})[-.\/월\s]+(\d{1,2})/);
    if (iso) return new Date(Number(iso[1]), Number(iso[2]) - 1, Number(iso[3]));

    const monthDay = normalized.match(/(?:^|\D)(\d{1,2})\s*월\s*(\d{1,2})\s*일?/);
    if (monthDay) {
      const date = new Date(today.getFullYear(), Number(monthDay[1]) - 1, Number(monthDay[2]));
      if (date < today) date.setFullYear(date.getFullYear() + 1);
      return date;
    }

    if (/모레/.test(normalized)) {
      const date = new Date(today);
      date.setDate(today.getDate() + 2);
      return date;
    }
    if (/내일/.test(normalized)) {
      const date = new Date(today);
      date.setDate(today.getDate() + 1);
      return date;
    }
    if (/오늘/.test(normalized)) return new Date(today);

    const weekdayMatch = normalized.match(/(다음\s*주|이번\s*주|다음주|이번주)?\s*([월화수목금토일])요일?/);
    if (weekdayMatch) {
      const target = WEEKDAY_MAP[weekdayMatch[2]];
      const current = today.getDay();
      const modifier = weekdayMatch[1] || "";
      let date = new Date(today);
      if (/다음/.test(modifier)) {
        const daysToMondayNextWeek = ((8 - current) % 7) || 7;
        date.setDate(today.getDate() + daysToMondayNextWeek + (target === 0 ? 6 : target - 1));
      } else if (/이번/.test(modifier)) {
        const mondayThisWeek = new Date(today);
        mondayThisWeek.setDate(today.getDate() - ((current + 6) % 7));
        date = mondayThisWeek;
        date.setDate(mondayThisWeek.getDate() + (target === 0 ? 6 : target - 1));
      } else {
        const diff = (target - current + 7) % 7 || 7;
        date.setDate(today.getDate() + diff);
      }
      return date;
    }

    const fallback = new Date(fallbackDate);
    fallback.setHours(0, 0, 0, 0);
    return fallback;
  }

  function parseTime(text, fallbackDate = new Date()) {
    const normalized = text.replace(/\s+/g, " ");
    const colon = normalized.match(/(오전|오후|am|pm)?\s*(\d{1,2})\s*[:시]\s*(\d{1,2})?/i);
    if (colon) {
      let hours = Number(colon[2]);
      const minutes = Number(colon[3] || 0);
      const meridiem = (colon[1] || "").toLowerCase();
      if ((meridiem === "오후" || meridiem === "pm") && hours < 12) hours += 12;
      if ((meridiem === "오전" || meridiem === "am") && hours === 12) hours = 0;
      if (!meridiem && hours >= 1 && hours <= 7) hours += 12;
      return { hours: Math.min(hours, 23), minutes: Math.min(minutes, 59) };
    }
    const korean = normalized.match(/(오전|오후)?\s*(\d{1,2})\s*시(?:\s*(\d{1,2})\s*분)?/);
    if (korean) {
      let hours = Number(korean[2]);
      const minutes = Number(korean[3] || 0);
      if (korean[1] === "오후" && hours < 12) hours += 12;
      if (korean[1] === "오전" && hours === 12) hours = 0;
      if (!korean[1] && hours >= 1 && hours <= 7) hours += 12;
      return { hours, minutes };
    }
    const fallback = new Date(fallbackDate);
    return { hours: fallback.getHours() || 9, minutes: fallback.getMinutes() || 0 };
  }

  function inferTitle(text, forChange = false) {
    let title = text
      .replace(/20\d{2}[-.\/년\s]+\d{1,2}[-.\/월\s]+\d{1,2}일?/g, " ")
      .replace(/\d{1,2}\s*월\s*\d{1,2}\s*일?/g, " ")
      .replace(/다음\s*주|이번\s*주|다음주|이번주|오늘|내일|모레|[월화수목금토일]요일?/g, " ")
      .replace(/오전|오후|am|pm/gi, " ")
      .replace(/\d{1,2}\s*[:시]\s*\d{0,2}\s*분?/g, " ")
      .replace(/\d+\s*(시간|분)\s*(동안|짜리)?/g, " ")
      .replace(/일정|등록해줘|등록|추가해줘|추가|잡아줘|생성|해줘|해주세요/g, " ")
      .replace(/시간을|시간|으로|로|변경해줘|변경|수정|옮겨|바꿔|삭제|지워|취소/g, " ")
      .replace(/[,.!?]/g, " ")
      .replace(/\s+/g, " ")
      .trim();

    if (forChange) {
      const firstKnown = findKnownTitleToken(text);
      if (firstKnown) return firstKnown;
    }
    if (!title) return "";
    return title.length > 28 ? title.slice(0, 28).trim() : title;
  }

  function inferImportance(text) {
    if (/중요|긴급|필수|마감|면접|발표|계약|제출|시험/.test(text)) return "high";
    if (/낮음|여유|가벼운/.test(text)) return "low";
    return "medium";
  }

  function inferDuration(text) {
    const hour = text.match(/(\d+)\s*시간/);
    const minute = text.match(/(\d+)\s*분/);
    let duration = 60;
    if (hour) duration = Number(hour[1]) * 60;
    if (minute && !/시\s*\d+\s*분/.test(text)) duration += Number(minute[1]);
    return Math.max(15, Math.min(duration, 480));
  }

  function filterByTextTime(text, source) {
    const now = new Date();
    const today = formatDateInput(now);
    const tomorrowDate = new Date(now);
    tomorrowDate.setDate(now.getDate() + 1);
    const tomorrow = formatDateInput(tomorrowDate);
    const lower = text.toLowerCase();

    return source.filter((event) => {
      if (/오늘/.test(text) && event.date !== today) return false;
      if (/내일/.test(text) && event.date !== tomorrow) return false;
      if (/이번\s*주|이번주|주간|7일/.test(text)) {
        const diff = (toDateTime(event) - new Date(`${today}T00:00:00`)) / 864e5;
        if (diff < 0 || diff >= 8) return false;
      }
      const titleToken = inferTitle(text, true).toLowerCase();
      if (titleToken && !`${event.title} ${event.notes}`.toLowerCase().includes(titleToken) && !/오늘|내일|이번/.test(text)) return false;
      if (lower.includes("중요") && priorityFor(event).score < 70) return false;
      return true;
    });
  }

  function findKnownTitleToken(text) {
    const stripped = text.replace(/시간을|시간|으로|로|변경|수정|옮겨|바꿔|삭제|취소|지워|해줘|해주세요/g, " ");
    const sorted = [...events].sort((a, b) => b.title.length - a.title.length);
    return sorted.find((event) => stripped.includes(event.title))?.title || "";
  }

  function findBestEvent(text) {
    const known = findKnownTitleToken(text);
    if (known) return events.find((event) => event.title === known);
    const title = inferTitle(text, true).toLowerCase();
    const candidates = events.filter((event) => `${event.title} ${event.notes}`.toLowerCase().includes(title));
    if (candidates.length) return candidates.sort((a, b) => toDateTime(a) - toDateTime(b))[0];
    return events.sort((a, b) => toDateTime(a) - toDateTime(b))[0] || null;
  }

  function submitForm(event) {
    event.preventDefault();
    const payload = normalizeEvent({
      id: elements.eventId.value || undefined,
      title: elements.title.value,
      date: elements.date.value,
      time: elements.time.value,
      duration: Number(elements.duration.value),
      importance: elements.importance.value,
      reminderMinutes: Number(elements.reminderMinutes.value),
      notes: elements.notes.value,
      createdAt: elements.eventId.value ? events.find((item) => item.id === elements.eventId.value)?.createdAt : new Date().toISOString(),
      updatedAt: new Date().toISOString()
    });
    if (!payload) return;

    const index = events.findIndex((item) => item.id === payload.id);
    if (index >= 0) events[index] = payload;
    else events.push(payload);

    saveEvents();
    resetForm();
    setAgentResponse(`<p>일정이 저장되었습니다: ${escapeHtml(payload.title)} — ${escapeHtml(formatKoreanDateTime(payload))}</p>`);
    showToast("일정이 저장되었습니다.");
  }

  function editEvent(id) {
    const event = events.find((item) => item.id === id);
    if (!event) return;
    elements.formTitle.textContent = "일정 변경";
    elements.eventId.value = event.id;
    elements.title.value = event.title;
    elements.date.value = event.date;
    elements.time.value = event.time;
    elements.duration.value = event.duration;
    elements.importance.value = event.importance;
    elements.reminderMinutes.value = event.reminderMinutes;
    elements.notes.value = event.notes;
    elements.submitEvent.textContent = "변경 저장";
    document.querySelector("#form").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function deleteEvent(id) {
    const event = events.find((item) => item.id === id);
    if (!event) return;
    if (!confirm(`'${event.title}' 일정을 삭제할까요?`)) return;
    events = events.filter((item) => item.id !== id);
    saveEvents();
    showToast("일정이 삭제되었습니다.");
  }

  function resetForm() {
    elements.formTitle.textContent = "직접 일정 등록";
    elements.eventForm.reset();
    elements.eventId.value = "";
    elements.duration.value = "60";
    elements.importance.value = "medium";
    elements.reminderMinutes.value = "30";
    const now = new Date();
    now.setHours(now.getHours() + 1, 0, 0, 0);
    elements.date.value = formatDateInput(now);
    elements.time.value = formatTimeInput(now);
    elements.submitEvent.textContent = "일정 저장";
  }

  function seedDemoData() {
    const base = new Date();
    const make = (offsetDays, hour, title, importance, notes) => {
      const date = new Date(base);
      date.setDate(base.getDate() + offsetDays);
      date.setHours(hour, 0, 0, 0);
      return normalizeEvent({
        title,
        date: formatDateInput(date),
        time: formatTimeInput(date),
        duration: 60,
        importance,
        reminderMinutes: importance === "high" ? 60 : 30,
        notes
      });
    };
    const samples = [
      make(1, 10, "프로젝트 발표 준비", "high", "발표 자료 최종 점검"),
      make(2, 14, "팀 회의", "medium", "진행 상황 공유"),
      make(5, 9, "계약 검토 마감", "high", "법무 검토 후 승인 필요"),
      make(7, 16, "회고 미팅", "low", "개선점 정리")
    ];
    events = [...events, ...samples];
    saveEvents();
    showToast("샘플 일정이 추가되었습니다.");
    setAgentResponse(`<p>샘플 일정 4개를 추가했습니다. “중요한 일정 추천해줘”를 실행해보세요.</p>`);
  }

  function exportData() {
    const blob = new Blob([JSON.stringify(events, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `personal-assistant-events-${formatDateInput(new Date())}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function importData(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const imported = JSON.parse(reader.result);
        if (!Array.isArray(imported)) throw new Error("JSON 배열이 아닙니다.");
        events = imported.map(normalizeEvent).filter(Boolean);
        saveEvents();
        showToast("일정 데이터를 가져왔습니다.");
      } catch (error) {
        showToast(`가져오기 실패: ${error.message}`);
      }
    };
    reader.readAsText(file);
  }

  async function requestNotificationPermission() {
    if (!("Notification" in window)) {
      showToast("이 브라우저는 알림 기능을 지원하지 않습니다.");
      return;
    }
    const permission = await Notification.requestPermission();
    showToast(permission === "granted" ? "브라우저 알림이 허용되었습니다." : "알림 권한이 허용되지 않았습니다.");
  }

  function sendNotification(title, body) {
    showToast(`${title} — ${body}`);
    if ("Notification" in window && Notification.permission === "granted") {
      new Notification(title, { body, icon: "" });
    }
  }

  function checkReminders() {
    const now = Date.now();
    events.forEach((event) => {
      if (!event.reminderMinutes) return;
      const start = toDateTime(event).getTime();
      const reminderStart = start - event.reminderMinutes * 60000;
      const key = `${event.id}-${event.date}-${event.time}`;
      if (!notified[key] && now >= reminderStart && now <= start + 60000) {
        notified[key] = true;
        saveJson(NOTIFIED_KEY, notified);
        sendNotification("중요 일정 알림", `${event.title} · ${formatKoreanDateTime(event)}`);
      }
    });
  }

  function bindEvents() {
    elements.runCommand.addEventListener("click", handleCommand);
    elements.agentInput.addEventListener("keydown", (event) => {
      if (event.key === "Enter") handleCommand();
    });
    $$("[data-sample]").forEach((button) => {
      button.addEventListener("click", () => {
        elements.agentInput.value = button.dataset.sample;
        handleCommand();
      });
    });
    elements.rangeFilter.addEventListener("change", renderEvents);
    elements.searchFilter.addEventListener("input", renderEvents);
    elements.eventList.addEventListener("click", (event) => {
      const button = event.target.closest("button[data-action]");
      if (!button) return;
      if (button.dataset.action === "edit") editEvent(button.dataset.id);
      if (button.dataset.action === "delete") deleteEvent(button.dataset.id);
    });
    elements.eventForm.addEventListener("submit", submitForm);
    elements.resetForm.addEventListener("click", resetForm);
    elements.seedDemo.addEventListener("click", seedDemoData);
    elements.exportData.addEventListener("click", exportData);
    elements.importData.addEventListener("change", (event) => importData(event.target.files[0]));
    elements.askNotification.addEventListener("click", requestNotificationPermission);
    elements.testReminder.addEventListener("click", () => sendNotification("알림 테스트", "브라우저 알림 기능이 정상적으로 호출되었습니다."));
  }

  bindEvents();
  resetForm();
  render();
  setInterval(checkReminders, 30000);
  checkReminders();
})();
