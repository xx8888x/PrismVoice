<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Layers3, Search, ArrowUpRight, ArrowLeftRight, Clock3, ChevronRight, BookOpen, GitCompareArrows } from 'lucide-vue-next'

const events = ref([]), current = ref(null), loading = ref(true), error = ref(''), search = ref(''), demo = ref(false), sidebar = ref(false)
const leftId = ref(''), rightId = ref(''), comparison = ref(null), compareLoading = ref(false), tab = ref('compare')
let eventRequest = 0, compareRequest = 0, listRequest = 0
const visibleEvents = computed(() => events.value.filter(e => e.title.includes(search.value)))
const articles = computed(() => current.value?.articles || [])
const left = computed(() => articles.value.find(a => a.id === Number(leftId.value)))
const right = computed(() => articles.value.find(a => a.id === Number(rightId.value)))

const fmt = (value, dateOnly = false) => value ? new Intl.DateTimeFormat('zh-TW', { timeZone: 'Asia/Taipei', month: '2-digit', day: '2-digit', ...(dateOnly ? {} : {hour: '2-digit', minute: '2-digit', hour12: false}) }).format(new Date(value.endsWith('Z') || value.includes('+') ? value : value.replace(' ', 'T') + 'Z')) : '—'
const position = score => `${((score ?? 0) + 2) * 25}%`
const statusText = computed(() => ({opposed: '辨識到相反主張', different: '觀點呈現不同', undetermined: '主張方向待判定'}[comparison.value?.status] || '選擇文章開始比較'))

async function api(url, options = {}) {
  const response = await fetch(url, { credentials: 'same-origin', ...options, headers: { Accept: 'application/json', 'Content-Type': 'application/json', 'X-CSRF-TOKEN': document.querySelector('meta[name="csrf-token"]')?.content, ...(options.headers || {}) } })
  const data = await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.message || `讀取失敗（${response.status}）`)
  return data
}
async function loadEvents() {
  const token = ++listRequest; ++eventRequest; ++compareRequest
  loading.value = true; error.value = ''; current.value = null; comparison.value = null; events.value = []
  try {
    const data = await api(`/api/events?demo=${demo.value ? 1 : 0}`)
    if (token !== listRequest) return
    events.value = data
    if (data.length) await selectEvent(data[0].id)
  } catch(e) { if (token === listRequest) error.value = e.message }
  finally { if (token === listRequest) loading.value = false }
}
async function selectEvent(id, preserve = false) {
  const token = ++eventRequest; ++compareRequest; const oldLeft = leftId.value, oldRight = rightId.value
  loading.value = true; error.value = ''; comparison.value = null; current.value = null; sidebar.value = false
  try {
    const data = await api(`/api/events/${id}`)
    if (token !== eventRequest) return
    current.value = data
    leftId.value = preserve && data.articles.some(a => a.id === Number(oldLeft)) ? oldLeft : data.articles[0]?.id || ''
    rightId.value = preserve && data.articles.some(a => a.id === Number(oldRight)) ? oldRight : data.articles[1]?.id || ''
    await loadComparison()
  } catch(e) { if(token === eventRequest) error.value = e.message }
  finally { if(token === eventRequest) loading.value = false }
}
async function loadComparison() {
  const token = ++compareRequest; comparison.value = null
  if (!current.value || !leftId.value || !rightId.value || Number(leftId.value) === Number(rightId.value)) { compareLoading.value = false; return }
  compareLoading.value = true
  try {
    const data = await api(`/api/events/${current.value.id}/compare?left=${leftId.value}&right=${rightId.value}`)
    if(token === compareRequest) comparison.value = data
  } catch(e) { if(token === compareRequest) error.value = e.message }
  finally { if(token === compareRequest) compareLoading.value = false }
}
watch([leftId, rightId], loadComparison)
watch(demo, () => { search.value = ''; loadEvents() })
onMounted(loadEvents)
function selectFromTimeline(article) { if(article.id !== Number(leftId.value)) rightId.value = article.id; tab.value = 'compare'; }

const getBiasScore = assessments => { const key = Object.keys(assessments)[0]; return key ? assessments[key].score : 0; }
const getBiasClass = assessments => { const score = getBiasScore(assessments); return score > 0 ? "bias-right" : score < 0 ? "bias-left" : "bias-neutral"; }
const getBiasText = assessments => { const score = getBiasScore(assessments); return score > 0 ? "偏向支持" : score < 0 ? "偏向反對" : "中立"; }
</script>

<template>
  <div class="workspace">
    <aside class="sidebar" :class="{open: sidebar}">
      <a class="brand" href="/" aria-label="稜鏡首頁"><span class="brand-symbol"><Layers3 :size="25" /></span><span>稜鏡 <b>PRISM</b></span></a>
      <div class="sidebar-label">AI 新聞觀點分析</div>
      <div class="dataset-toggle"><button :class="{active: !demo}" @click="demo = false">即時新聞</button><button :class="{active: demo}" @click="demo = true">歷史案例</button></div>
      <label class="search"><Search :size="17" /><input v-model="search" placeholder="搜尋新聞事件" /></label>
      <nav class="event-list">
        <button v-for="event in visibleEvents" :key="event.id" class="event-button" :class="{selected: current?.id === event.id}" @click="selectEvent(event.id)">
          <span class="event-button-title">{{ event.title }}</span><span class="event-meta">{{ event.articles_count }} 篇報導 <span>{{ fmt(event.articles_max_published_at, true) }}</span></span>
        </button>
      </nav>
    </aside>
    <div class="main-shell">
      <main>
        <div v-if="loading" class="loading-state">載入中…</div>
        <template v-else-if="current">
          <div class="event-heading">
            <h1>{{ current.title }}</h1>
            <div class="view-tabs" role="tablist">
              <button role="tab" :class="{active: tab === 'compare'}" @click="tab = 'compare'"><GitCompareArrows :size="17" />觀點比較</button>
              <button role="tab" :class="{active: tab === 'timeline'}" @click="tab = 'timeline'"><Clock3 :size="17" />時間軸</button>
            </div>
          </div>
          <div class="content-grid" :class="{'timeline-view': tab === 'timeline'}">
            <section v-if="tab === 'compare'" class="comparison-workspace">
              <div class="article-pair">
                <article v-for="(article, index) in [left, right]" :key="index" class="article-card" :class="index === 0 ? 'article-a' : 'article-b'">
                  <div class="card-top"><span class="letter">{{ index === 0 ? 'A' : 'B' }}</span><span>{{ article?.source }}</span></div>
                  <select :value="index === 0 ? leftId : rightId" @change="index === 0 ? leftId = Number($event.target.value) : rightId = Number($event.target.value)">
                    <option v-for="item in articles" :key="item.id" :value="item.id" :disabled="item.id === Number(index === 0 ? rightId : leftId)">{{ item.title }}</option>
                  </select>
                  <h3>{{ article?.title }}</h3>
                  <div class="card-footer"><a v-if="article?.url" :href="article.url" target="_blank">閱讀原文<ArrowUpRight :size="15" /></a></div>
                </article>
              </div>
              <section class="dimension-panel">
                <div v-if="compareLoading">AI 分析比較中…</div>
                <template v-else-if="comparison">
                  <div v-for="dimension in comparison.dimensions" :key="dimension.key" class="dimension-row">
                    <h3>{{ dimension.name }}</h3>
                    <p class="dimension-question">{{ dimension.question }}</p>
                    <div class="axis-labels"><span>{{ dimension.left }}</span><span>中立</span><span>{{ dimension.right }}</span></div>
                    <div class="axis">
                      <i v-for="n in 5" :key="n" :style="{left: `${(n-1)*25}%`}"></i>
                      <span v-if="dimension.leftAssessment.score !== null" class="marker a" :style="{left: position(dimension.leftAssessment.score)}">A</span>
                      <span v-if="dimension.rightAssessment.score !== null" class="marker b" :style="{left: position(dimension.rightAssessment.score)}">B</span>
                    </div>
                  </div>
                </template>
              </section>
            </section>
            <aside class="timeline-panel" v-if="tab === 'timeline'">
              <ol class="timeline">
                <li v-for="article in articles" :key="article.id" :class="{chosen: article.id === Number(leftId) || article.id === Number(rightId)}">
                  <time>{{ fmt(article.published_at) }}</time>
                  <h3>{{ article.title }}</h3>
                  <p>{{ article.source }}</p>
                  <div class="timeline-bias-indicator" v-if="article.assessments">
                    <span class="bias-dot" :class="getBiasClass(article.assessments)"></span>
                    立場傾向: {{ getBiasText(article.assessments) }}
                  </div>
                  <button v-if="article.id !== Number(leftId)" @click="selectFromTimeline(article)">設定為比較對象</button>
                </li>
              </ol>
            </aside>
          </div>
        </template>
      </main>
    </div>
  </div>
</template>

<style scoped>
.timeline-bias-indicator {
  font-size: 0.85em;
  margin-top: 6px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 6px;
}
.bias-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.bias-right {
  background-color: #3b82f6; /* Blue for right/support */
}
.bias-left {
  background-color: #ef4444; /* Red for left/oppose */
}
.bias-neutral {
  background-color: #9ca3af; /* Gray for neutral */
}
</style>
