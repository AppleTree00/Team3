(function () {
  'use strict';

  const state = { articles: [], lastMarkdown: '', lastProvider: '' };
  const $ = (selector) => document.querySelector(selector);

  const stopwords = new Set([
    'the','and','for','with','from','that','this','are','was','were','will','has','have','its','into','over','after','before','about','says','said','new','latest','news','live','amid','your','you','our','their','they','them','his','her','who','what','when','where','how','why','but','not','can','may','could','would','should','more','most','than','then','also','as','at','by','in','on','to','of','a','an','is','be','or','it','via','up','out','off','first','report','reports','update','updates','announces','announced','analysis','industry',
    '및','그리고','관련','뉴스','최신','속보','대한','통해','위해','으로','에서','에게','한다','했다','하는','있는','없는','이번','오늘','지난','가장','기사','보도','출처','분석','산업'
  ]);
  const positiveWords = new Set(['growth','grow','surge','gain','rise','boost','win','success','positive','profit','record','breakthrough','deal','expand','improve','upgrade','strong','launch','approval','stable','recovery','innovation','혁신','성장','상승','확대','개선','성공','호재','강세','회복','승인']);
  const negativeWords = new Set(['fall','drop','decline','risk','loss','crisis','war','attack','fear','concern','warning','lawsuit','ban','delay','cut','weak','down','negative','probe','fraud','outage','위기','하락','감소','리스크','우려','경고','소송','금지','공격','약세','지연','손실','장애']);

  const sampleFallback = [
    {
      id: 'sample-1', provider: 'Sample fallback', title: 'OpenAI and enterprise AI agents remain a major topic in technology coverage',
      url: 'https://news.ycombinator.com/', source: 'sample.local', sourceCountry: 'US', language: 'English', publishedAt: new Date().toISOString(), image: '', tone: null,
      description: '브라우저가 외부 API 호출을 모두 차단했을 때만 표시되는 샘플입니다. GitHub Pages 배포 URL에서는 실제 API 호출을 다시 시도합니다.'
    },
    {
      id: 'sample-2', provider: 'Sample fallback', title: 'Companies continue testing workflow automation with AI tools',
      url: 'https://news.ycombinator.com/', source: 'sample.local', sourceCountry: 'US', language: 'English', publishedAt: new Date(Date.now() - 3600 * 1000).toISOString(), image: '', tone: null,
      description: '이 카드는 API 실패 시 화면 구조 확인용입니다. 실제 데이터가 아니므로 상태창에 명확히 표시됩니다.'
    }
  ];

  function escapeHtml(value = '') {
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
  function normalizeText(value = '') { return String(value).replace(/\s+/g, ' ').trim(); }
  function hostFromUrl(url = '') {
    try { return new URL(url).hostname.replace(/^www\./, ''); } catch { return 'unknown source'; }
  }
  function formatDate(value) {
    if (!value) return '날짜 없음';
    const raw = String(value);
    const normalized = /^\d{14}$/.test(raw)
      ? `${raw.slice(0,4)}-${raw.slice(4,6)}-${raw.slice(6,8)}T${raw.slice(8,10)}:${raw.slice(10,12)}:${raw.slice(12,14)}Z`
      : raw;
    const date = new Date(normalized);
    if (Number.isNaN(date.getTime())) return raw;
    return new Intl.DateTimeFormat('ko-KR', { dateStyle: 'medium', timeStyle: 'short' }).format(date);
  }
  function tokenize(text = '') {
    const matches = normalizeText(text.toLowerCase()).match(/[가-힣a-zA-Z0-9][가-힣a-zA-Z0-9+#.-]{1,}/g) || [];
    return matches
      .map((token) => token.replace(/^[^가-힣a-zA-Z0-9]+|[^가-힣a-zA-Z0-9+#.-]+$/g, ''))
      .filter((token) => token.length > 1 && !stopwords.has(token) && !/^\d+$/.test(token));
  }
  function setStatus(message, type = '') {
    const box = $('#statusBox');
    box.className = `status ${type}`.trim();
    box.textContent = message;
  }
  function setLoading(isLoading) {
    $('#searchButton').disabled = isLoading;
    $('#searchButton').textContent = isLoading ? '불러오는 중...' : '실제 뉴스 불러오기';
  }

  function withTimeout(promise, timeoutMs, label) {
    return Promise.race([
      promise,
      new Promise((_, reject) => setTimeout(() => reject(new Error(`${label} 호출 시간이 초과되었습니다.`)), timeoutMs))
    ]);
  }

  async function fetchJson(url, timeoutMs = 15000) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await fetch(url, {
        method: 'GET',
        cache: 'no-store',
        mode: 'cors',
        signal: controller.signal,
        headers: { 'Accept': 'application/json,text/plain,*/*' }
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return await response.json();
    } finally {
      clearTimeout(timer);
    }
  }

  function toJsonpUrl(url, callbackName) {
    const parsed = new URL(url);
    parsed.searchParams.set('format', 'jsonp');
    parsed.searchParams.set('callback', callbackName);
    parsed.searchParams.set('_', Date.now().toString());
    return parsed.toString();
  }

  function fetchJsonp(url, timeoutMs = 15000) {
    return new Promise((resolve, reject) => {
      const callbackName = `__newsAgentJsonp_${Date.now()}_${Math.random().toString(36).slice(2)}`;
      const script = document.createElement('script');
      let settled = false;
      const timer = setTimeout(() => cleanup(new Error('JSONP 호출 시간이 초과되었습니다.')), timeoutMs);

      function cleanup(error, data) {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        try { delete window[callbackName]; } catch { window[callbackName] = undefined; }
        if (script.parentNode) script.parentNode.removeChild(script);
        if (error) reject(error); else resolve(data);
      }

      window[callbackName] = (data) => cleanup(null, data);
      script.onerror = () => cleanup(new Error('JSONP 스크립트 로드에 실패했습니다.'));
      script.src = toJsonpUrl(url, callbackName);
      document.head.appendChild(script);
    });
  }

  async function requestGdelt(url) {
    try {
      return await fetchJson(url, 15000);
    } catch (fetchError) {
      setStatus(`GDELT fetch 실패(${fetchError.message}). JSONP로 재시도합니다.`);
      return fetchJsonp(url, 15000);
    }
  }

  function normalizeTimespan(value) {
    if (value === '1week') return '1w';
    if (value === '7d') return '7d';
    return value || '24h';
  }

  function getCreatedAfter(timespan) {
    const now = Math.floor(Date.now() / 1000);
    const span = normalizeTimespan(timespan);
    const match = String(span).match(/^(\d+)(h|d|w)$/);
    if (!match) return now - 24 * 3600;
    const amount = Number(match[1]);
    const unit = match[2];
    const seconds = unit === 'h' ? amount * 3600 : unit === 'd' ? amount * 86400 : amount * 7 * 86400;
    return now - seconds;
  }

  function buildGdeltUrl({ query, timespan, limit }) {
    const params = new URLSearchParams({
      query,
      mode: 'artlist',
      format: 'json',
      maxrecords: String(Math.min(Math.max(limit, 1), 75)),
      sort: 'datedesc',
      timespan: normalizeTimespan(timespan),
    });
    return `https://api.gdeltproject.org/api/v2/doc/doc?${params.toString()}`;
  }

  function buildGuardianUrl({ query, limit, guardianKey }) {
    const params = new URLSearchParams({
      q: query,
      'api-key': guardianKey,
      'show-fields': 'trailText,thumbnail,shortUrl',
      'order-by': 'newest',
      'page-size': String(Math.min(Math.max(limit, 1), 50)),
    });
    return `https://content.guardianapis.com/search?${params.toString()}`;
  }

  function buildHnUrl({ query, timespan, limit }) {
    const params = new URLSearchParams({
      query,
      tags: 'story',
      hitsPerPage: String(Math.min(Math.max(limit, 1), 50)),
      numericFilters: `created_at_i>${getCreatedAfter(timespan)}`
    });
    return `https://hn.algolia.com/api/v1/search_by_date?${params.toString()}`;
  }

  function buildSpaceflightUrl({ query, limit }) {
    const params = new URLSearchParams({
      limit: String(Math.min(Math.max(limit, 1), 50)),
      ordering: '-published_at'
    });
    if (query) params.set('search', query);
    return `https://api.spaceflightnewsapi.net/v4/articles/?${params.toString()}`;
  }

  function normalizeGdeltArticle(raw, index) {
    const url = raw.url || raw.url_mobile || '';
    const title = normalizeText(raw.title || raw.name || 'Untitled article');
    return {
      id: `gdelt-${index}-${url}`,
      provider: 'GDELT DOC API',
      title,
      url,
      source: raw.domain || raw.source || hostFromUrl(url),
      sourceCountry: raw.sourcecountry || raw.sourceCountry || raw.country || '',
      language: raw.language || raw.sourcelang || raw.sourceLanguage || '',
      publishedAt: raw.seendate || raw.date || raw.datetime || raw.publishedAt || '',
      image: raw.socialimage || raw.image || '',
      tone: raw.tone ?? raw.Tone ?? null,
      description: normalizeText(raw.excerpt || raw.description || ''),
    };
  }

  function normalizeGuardianArticle(raw, index) {
    const fields = raw.fields || {};
    return {
      id: `guardian-${index}-${raw.id || raw.webUrl}`,
      provider: 'The Guardian',
      title: normalizeText(raw.webTitle || 'Untitled article'),
      url: raw.webUrl || fields.shortUrl || '',
      source: 'theguardian.com',
      sourceCountry: 'GB',
      language: 'English',
      publishedAt: raw.webPublicationDate || '',
      image: fields.thumbnail || '',
      tone: null,
      description: normalizeText((fields.trailText || '').replace(/<[^>]+>/g, '')),
    };
  }

  function normalizeHnArticle(raw, index) {
    const url = raw.url || `https://news.ycombinator.com/item?id=${raw.objectID}`;
    const title = normalizeText(raw.title || raw.story_title || 'Untitled Hacker News story');
    return {
      id: `hn-${index}-${raw.objectID}`,
      provider: 'Hacker News Algolia API',
      title,
      url,
      source: hostFromUrl(url),
      sourceCountry: '',
      language: 'English',
      publishedAt: raw.created_at || '',
      image: '',
      tone: null,
      description: normalizeText(`HN points ${raw.points ?? 0}, comments ${raw.num_comments ?? 0}. ${raw.story_text || ''}`),
    };
  }

  function normalizeSpaceflightArticle(raw, index) {
    return {
      id: `spaceflight-${index}-${raw.id}`,
      provider: 'Spaceflight News API',
      title: normalizeText(raw.title || 'Untitled article'),
      url: raw.url || '',
      source: raw.news_site || hostFromUrl(raw.url),
      sourceCountry: '',
      language: 'English',
      publishedAt: raw.published_at || raw.updated_at || '',
      image: raw.image_url || '',
      tone: null,
      description: normalizeText(raw.summary || ''),
    };
  }

  async function fetchGdeltArticles(options) {
    const url = buildGdeltUrl(options);
    $('#apiUrlBox').textContent = url;
    const data = await requestGdelt(url);
    const results = data?.articles || data?.results || data?.items || [];
    return results.map(normalizeGdeltArticle).filter((article) => article.title && article.url);
  }

  async function fetchGuardianArticles(options) {
    if (!options.guardianKey) throw new Error('Guardian API Key가 필요합니다. API 키 없이 확인하려면 자동 안정 모드 또는 GDELT를 선택하세요.');
    const url = buildGuardianUrl(options);
    $('#apiUrlBox').textContent = url.replace(options.guardianKey, '••••••');
    const data = await fetchJson(url, 15000);
    const results = data?.response?.results || [];
    return results.map(normalizeGuardianArticle).filter((article) => article.title && article.url);
  }

  async function fetchHnArticles(options) {
    const url = buildHnUrl(options);
    $('#apiUrlBox').textContent = url;
    const data = await fetchJson(url, 15000);
    const results = data?.hits || [];
    return results.map(normalizeHnArticle).filter((article) => article.title && article.url);
  }

  async function fetchSpaceflightArticles(options) {
    const url = buildSpaceflightUrl(options);
    $('#apiUrlBox').textContent = url;
    const data = await fetchJson(url, 15000);
    const results = Array.isArray(data) ? data : (data?.results || []);
    return results.map(normalizeSpaceflightArticle).filter((article) => article.title && article.url);
  }

  async function runProvider(provider, options) {
    if (provider === 'gdelt') return fetchGdeltArticles(options);
    if (provider === 'guardian') return fetchGuardianArticles(options);
    if (provider === 'hn') return fetchHnArticles(options);
    if (provider === 'spaceflight') return fetchSpaceflightArticles(options);
    throw new Error(`알 수 없는 데이터 소스입니다: ${provider}`);
  }

  async function fetchArticles(options) {
    const provider = options.provider;
    if (provider !== 'auto') {
      const articles = await runProvider(provider, options);
      state.lastProvider = provider;
      return articles;
    }

    const attempts = [
      ['gdelt', 'GDELT DOC API'],
      ['hn', 'Hacker News Algolia API'],
      ['spaceflight', 'Spaceflight News API']
    ];
    const errors = [];
    for (const [key, label] of attempts) {
      try {
        setStatus(`${label}로 실제 뉴스 데이터를 호출하는 중입니다...`);
        const articles = await withTimeout(runProvider(key, options), 17000, label);
        if (articles.length) {
          state.lastProvider = key;
          return articles;
        }
        errors.push(`${label}: 결과 없음`);
      } catch (error) {
        console.warn(label, error);
        errors.push(`${label}: ${error.message || error}`);
      }
    }
    const err = new Error(`모든 공개 API 호출이 실패했습니다. ${errors.join(' / ')}`);
    err.errors = errors;
    throw err;
  }

  function scoreSentiment(text = '', explicitTone = null) {
    if (explicitTone !== null && explicitTone !== undefined && explicitTone !== '') {
      const numeric = Number(explicitTone);
      if (!Number.isNaN(numeric)) {
        if (numeric > 1.5) return { label: '긍정', score: numeric, className: 'positive' };
        if (numeric < -1.5) return { label: '부정', score: numeric, className: 'negative' };
        return { label: '중립', score: numeric, className: 'neutral' };
      }
    }
    let score = 0;
    tokenize(text).forEach((word) => {
      if (positiveWords.has(word)) score += 1;
      if (negativeWords.has(word)) score -= 1;
    });
    if (score > 0) return { label: '긍정', score, className: 'positive' };
    if (score < 0) return { label: '부정', score, className: 'negative' };
    return { label: '중립', score, className: 'neutral' };
  }

  function summarizeArticle(article) {
    const source = article.source || hostFromUrl(article.url);
    const published = formatDate(article.publishedAt);
    const keywords = tokenize(`${article.title} ${article.description}`).slice(0, 4);
    const keywordPhrase = keywords.length ? ` 핵심 키워드는 ${keywords.join(', ')}입니다.` : '';
    const desc = article.description ? ` ${article.description}` : '';
    const sampleNote = article.provider === 'Sample fallback' ? ' API 실패 시 표시되는 샘플 카드입니다.' : ' 실제 API에서 받은 기사 데이터입니다.';
    return `${source}에서 ${published} 기준으로 확인된${sampleNote}${keywordPhrase}${desc}`;
  }

  function vectorize(text) {
    const map = new Map();
    tokenize(text).forEach((token) => map.set(token, (map.get(token) || 0) + 1));
    return map;
  }
  function cosineSimilarity(a, b) {
    const va = vectorize(a);
    const vb = vectorize(b);
    let dot = 0, normA = 0, normB = 0;
    va.forEach((value, key) => { dot += value * (vb.get(key) || 0); normA += value * value; });
    vb.forEach((value) => { normB += value * value; });
    if (!normA || !normB) return 0;
    return dot / (Math.sqrt(normA) * Math.sqrt(normB));
  }
  function getRelatedArticles(target, articles) {
    return articles
      .filter((article) => article.id !== target.id)
      .map((article) => ({ article, score: cosineSimilarity(`${target.title} ${target.description}`, `${article.title} ${article.description}`) }))
      .filter((item) => item.score > 0)
      .sort((a, b) => b.score - a.score)
      .slice(0, 3);
  }

  function enrichArticles(articles) {
    return articles.map((article) => {
      const sentiment = scoreSentiment(`${article.title} ${article.description}`, article.tone);
      return { ...article, sentiment, summary: summarizeArticle(article), keywords: tokenize(`${article.title} ${article.description}`).slice(0, 6) };
    });
  }

  function renderMetrics(articles) {
    $('#metricTotal').textContent = String(articles.length);
    $('#metricUpdated').textContent = new Intl.DateTimeFormat('ko-KR', { timeStyle: 'short' }).format(new Date());
    const sourceCounts = new Map();
    const sentimentCounts = { 긍정: 0, 중립: 0, 부정: 0 };
    const keywordCounts = new Map();
    articles.forEach((article) => {
      sourceCounts.set(article.source, (sourceCounts.get(article.source) || 0) + 1);
      sentimentCounts[article.sentiment.label] = (sentimentCounts[article.sentiment.label] || 0) + 1;
      article.keywords.forEach((token) => keywordCounts.set(token, (keywordCounts.get(token) || 0) + 1));
    });
    const topSource = [...sourceCounts.entries()].sort((a, b) => b[1] - a[1])[0];
    $('#metricTopSource').textContent = topSource ? `${topSource[0]} (${topSource[1]})` : '-';
    const topSentiment = Object.entries(sentimentCounts).sort((a, b) => b[1] - a[1])[0];
    $('#metricSentiment').textContent = topSentiment && articles.length ? `${topSentiment[0]} (${topSentiment[1]})` : '-';
    const topKeywords = [...keywordCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 16);
    $('#keywordCloud').innerHTML = topKeywords.length
      ? topKeywords.map(([word, count]) => `<span class="keyword">${escapeHtml(word)} <strong>${count}</strong></span>`).join('')
      : '<span class="muted">검색 후 표시됩니다.</span>';
    $('#sentimentSummary').innerHTML = articles.length
      ? Object.entries(sentimentCounts).map(([label, count]) => `<span class="chip ${label === '긍정' ? 'positive' : label === '부정' ? 'negative' : 'neutral'}">${label} ${count}</span>`).join('')
      : '<span class="muted">검색 후 표시됩니다.</span>';
  }

  function renderArticles(articles) {
    const list = $('#articleList');
    if (!articles.length) {
      list.innerHTML = '<div class="notice">검색 조건에 맞는 기사가 없습니다. 검색어를 영어로 바꾸거나 기간을 넓혀보세요.</div>';
      $('#exportButton').disabled = true;
      state.lastMarkdown = '';
      return;
    }
    list.innerHTML = articles.map((article, index) => {
      const related = getRelatedArticles(article, articles);
      const imageHtml = article.image ? `<img class="article-thumb" src="${escapeHtml(article.image)}" alt="" loading="lazy" onerror="this.remove(); this.closest('.article').classList.add('no-image');" />` : '';
      const keywords = article.keywords.length ? article.keywords.map((word) => `<span class="tag">${escapeHtml(word)}</span>`).join('') : '<span class="tag">keyword pending</span>';
      const relatedHtml = related.length ? `<div class="related"><strong>관련 기사 추천</strong><ul>${related.map(({ article: item, score }) => `<li><a href="${escapeHtml(item.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title)}</a> <span>유사도 ${Math.round(score * 100)}%</span></li>`).join('')}</ul></div>` : '';
      return `<article class="article ${article.image ? '' : 'no-image'}">
        <div class="article-body">
          <div class="article-meta">
            <span>#${index + 1}</span>
            <span>${escapeHtml(article.provider)}</span>
            <span>${escapeHtml(article.source)}</span>
            ${article.sourceCountry ? `<span>${escapeHtml(article.sourceCountry)}</span>` : ''}
            ${article.language ? `<span>${escapeHtml(article.language)}</span>` : ''}
            <span>${escapeHtml(formatDate(article.publishedAt))}</span>
          </div>
          <div class="article-title"><a href="${escapeHtml(article.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(article.title)}</a></div>
          <p class="article-summary">${escapeHtml(article.summary)}</p>
          <div>${keywords}</div>
          <div class="button-row" style="margin-top:12px">
            <span class="chip ${article.sentiment.className}">감정: ${escapeHtml(article.sentiment.label)}</span>
            <a class="button secondary" href="${escapeHtml(article.url)}" target="_blank" rel="noopener noreferrer">원문 보기</a>
          </div>
          ${relatedHtml}
        </div>
        ${imageHtml}
      </article>`;
    }).join('');
    state.lastMarkdown = buildMarkdown(articles);
    $('#exportButton').disabled = false;
  }

  function buildMarkdown(articles) {
    const query = $('#queryInput').value.trim();
    const lines = [`# 뉴스 요약 및 분석: ${query}`, '', `- 생성 시각: ${new Date().toLocaleString('ko-KR')}`, `- 데이터 소스: ${state.lastProvider || '-'}`, `- 기사 수: ${articles.length}`, '', '## 주요 기사'];
    articles.forEach((article, index) => {
      lines.push('', `### ${index + 1}. ${article.title}`);
      lines.push(`- 데이터 소스: ${article.provider}`);
      lines.push(`- 출처: ${article.source}`);
      lines.push(`- 보도 시각: ${formatDate(article.publishedAt)}`);
      lines.push(`- 감정: ${article.sentiment.label}`);
      lines.push(`- 키워드: ${article.keywords.join(', ') || '-'}`);
      lines.push(`- 요약: ${article.summary}`);
      lines.push(`- 링크: ${article.url}`);
    });
    return lines.join('\n');
  }

  async function runSearch() {
    const query = $('#queryInput').value.trim();
    const provider = $('#providerSelect').value;
    const timespan = $('#timespanSelect').value;
    const limit = Number($('#limitSelect').value || 12);
    const guardianKey = $('#guardianKeyInput').value.trim() || sessionStorage.getItem('guardianApiKey') || '';
    if (!query) { setStatus('검색어를 입력해주세요.', 'error'); return; }
    if (guardianKey) sessionStorage.setItem('guardianApiKey', guardianKey);
    setLoading(true);
    setStatus('실제 뉴스 API를 호출하는 중입니다...');
    $('#articleList').innerHTML = '<div class="notice">실제 기사 데이터를 불러오는 중입니다.</div>';
    try {
      const rawArticles = await fetchArticles({ query, provider, timespan, limit, guardianKey });
      state.articles = enrichArticles(rawArticles).slice(0, limit);
      renderMetrics(state.articles);
      renderArticles(state.articles);
      const sourceLabel = state.articles[0]?.provider || state.lastProvider || '선택한 API';
      setStatus(`${sourceLabel}에서 ${state.articles.length}개의 실제 기사 데이터를 불러와 요약·키워드·감정·관련 기사 분석을 완료했습니다.`, 'success');
    } catch (error) {
      console.error(error);
      state.lastProvider = 'sample-fallback';
      state.articles = enrichArticles(sampleFallback).slice(0, limit);
      renderMetrics(state.articles);
      renderArticles(state.articles);
      $('#apiUrlBox').textContent = `${$('#apiUrlBox').textContent}\n\nFallback reason: ${error.message || error}`;
      setStatus(`공개 API 호출이 현재 환경에서 실패했습니다. 화면 구조 확인을 위해 샘플 데이터를 표시합니다. GitHub Pages 배포 URL 또는 인터넷 연결 환경에서 다시 시도하세요. 원인: ${error.message || error}`, 'warn');
    } finally {
      setLoading(false);
    }
  }

  function init() {
    $('#providerSelect').addEventListener('change', () => {
      $('#guardianKeyWrap').classList.toggle('hidden', $('#providerSelect').value !== 'guardian');
    });
    $('#searchForm').addEventListener('submit', (event) => { event.preventDefault(); runSearch(); });
    $('#demoQueryButton').addEventListener('click', () => {
      $('#queryInput').value = 'artificial intelligence OR OpenAI OR AI agent';
      $('#providerSelect').value = 'auto';
      $('#guardianKeyWrap').classList.add('hidden');
      runSearch();
    });
    $('#exportButton').addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(state.lastMarkdown);
        setStatus('Markdown 요약을 클립보드에 복사했습니다.', 'success');
      } catch {
        const blob = new Blob([state.lastMarkdown], { type: 'text/markdown;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'news-analysis-report.md';
        link.click();
        URL.revokeObjectURL(url);
        setStatus('클립보드 권한이 없어 Markdown 파일 다운로드로 대체했습니다.', 'success');
      }
    });
    const savedGuardianKey = sessionStorage.getItem('guardianApiKey');
    if (savedGuardianKey) $('#guardianKeyInput').value = savedGuardianKey;
    runSearch();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
