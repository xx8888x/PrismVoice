
    // Embedded Data Sets: Demo and Real News (UDN sample)
    const DATASETS = {
      demo: [
        {
          id: 1,
          title: "示範：市中心汽車通行費提案",
          description: "此事件與三篇文章均為虛構教學資料，用於示範相反主張如何在同一維度被識別，並非真實新聞。",
          is_demo: true,
          question: "是否支持向進入市中心的汽車收取通行費？",
          dimensions: [
            { key: "position", name: "主張方向", question: "是否支持向進入市中心的汽車收取通行費？", left: "反對／質疑", right: "支持／肯定", opposition: true },
            { key: "focus", name: "討論焦點", question: "文字主要聚焦人物攻防，還是制度與政策？", left: "人物攻防", right: "制度政策", opposition: false },
            { key: "tone", name: "表達方式", question: "文字主要呈現衝突，還是協商與合作？", left: "衝突對抗", right: "協商合作", opposition: false }
          ],
          articles: [
            {
              id: 101,
              title: "示範｜交通研究者支持通行費：收入應投入公共運輸",
              source: "示範文章 A",
              author: "交通研究者（虛構）",
              published_at: "2026-09-01 09:00:00",
              url: null,
              analysis_status: "reviewed",
              assessments: {
                position: { score: 2, confidence: 1.0, actor: "交通研究者（虛構）", evidence: "支持收取通行費，將收入投入公共運輸改善品質與班次。", reason: "直接明確支持同一項通行費提案。", method: "demo" },
                focus: { score: 2, confidence: 1.0, actor: "交通研究者（虛構）", evidence: "討論收入補貼與公車專用道政策設計。", reason: "全文聚焦交通制度政策分析，未涉及政黨攻防。", method: "demo" },
                tone: { score: 1, confidence: 1.0, actor: "交通研究者（虛構）", evidence: "建議市府與市民召開公聽會協商最佳費率。", reason: "採用政策建議與協商語氣。", method: "demo" }
              }
            },
            {
              id: 102,
              title: "示範｜商圈代表反對通行費：替代運輸尚未到位",
              source: "示範文章 B",
              author: "商圈代表（虛構）",
              published_at: "2026-09-02 11:30:00",
              url: null,
              analysis_status: "reviewed",
              assessments: {
                position: { score: -2, confidence: 1.0, actor: "商圈代表（虛構）", evidence: "強烈反對目前收取通行費，周邊捷運公車尚未健全，將重創商圈。", reason: "明確反對目前實施同一項提案，與 A 主張對立。", method: "demo" },
                focus: { score: 2, confidence: 1.0, actor: "商圈代表（虛構）", evidence: "指出捷運接駁缺口與顧客停車補貼機制。", reason: "針對交通配套制度深入辯論。", method: "demo" },
                tone: { score: -1, confidence: 1.0, actor: "商圈代表（虛構）", evidence: "抨擊政策草率倉促，若硬推將發起抗議。", reason: "表達強烈不滿與抗議對抗語氣。", method: "demo" }
              }
            },
            {
              id: 103,
              title: "示範｜市府提出分階段試辦，邀雙方協商配套",
              source: "示範文章 C",
              author: "市府發言人（虛構）",
              published_at: "2026-09-03 14:00:00",
              url: null,
              analysis_status: "reviewed",
              assessments: {
                position: { score: 1, confidence: 1.0, actor: "市府代表（虛構）", evidence: "支持小規模分階段試辦，並依商圈回饋滾動調整費率與優惠。", reason: "有條件支持並提出過渡配套措施。", method: "demo" },
                focus: { score: 2, confidence: 1.0, actor: "市府代表（虛構）", evidence: "公布試辦區域電子收費門架建置期程。", reason: "制度政策落地執行細節。", method: "demo" },
                tone: { score: 2, confidence: 1.0, actor: "市府代表（虛構）", evidence: "主動邀集研究者與商圈代表坐下來共同找出平衡點。", reason: "展現高度協商與尋求共識態度。", method: "demo" }
              }
            }
          ]
        }
      ],
      real: [
        {
          id: 2,
          title: "蔣得立入學與身分爭議",
          description: "依標題中特定人物與議題暫時分組；可人工移動文章修正。時間軸使用報導發布時間，不等同事件發生時間。",
          is_demo: false,
          question: "是否支持進一步釐清入學程序與身分？",
          dimensions: [
            { key: "position", name: "主張方向", question: "是否支持進一步釐清入學程序與身分？", left: "反對／質疑", right: "支持／肯定", opposition: true },
            { key: "focus", name: "討論焦點", question: "文字主要聚焦人物攻防，還是制度與政策？", left: "人物攻防", right: "制度政策", opposition: false },
            { key: "tone", name: "表達方式", question: "文字主要呈現衝突，還是協商與合作？", left: "衝突對抗", right: "協商合作", opposition: false }
          ],
          articles: [
            {
              id: 201,
              title: "蔣得立錄取國際交換生！洪婉臻質疑有無填迴避檢核表 蔣萬安：該揭露都揭露",
              source: "聯合新聞網",
              author: "記者楊正海／台北即時報導",
              published_at: "2026-09-04 16:15:42",
              url: "https://udn.com/news/story/6656/9734890",
              analysis_status: "reviewed",
              assessments: {
                position: { score: 1, confidence: 0.7, actor: "市議員洪婉臻", evidence: "質疑有無填利益迴避檢核表，要求局處公開審核紀錄。", reason: "支持公開檢驗審查透明度。", method: "manual" },
                focus: { score: -1, confidence: 0.75, actor: "市議員與市長", evidence: "議會質詢蔣萬安市長家族背景與首長身分。", reason: "聚焦特定政治人物攻防與質疑。", method: "manual" },
                tone: { score: -1, confidence: 0.7, actor: "報導筆調", evidence: "用詞包含『質疑』、『交鋒』。", reason: "展現議會對抗衝突氛圍。", method: "manual" }
              }
            },
            {
              id: 202,
              title: "查蔣得立非事實？國教署會議有人問僑生身分 殷瑋質疑護航：是否負責？",
              source: "聯合新聞網",
              author: "記者楊正海／台北即時報導",
              published_at: "2026-09-04 18:16:53",
              url: "https://udn.com/news/story/6656/9735176",
              analysis_status: "reviewed",
              assessments: {
                position: { score: -1, confidence: 0.7, actor: "北市府副秘書長殷瑋", evidence: "反駁查身分指控並質疑綠營護航抹黑。", reason: "質疑調查合理性並反對擴大政治炒作。", method: "manual" },
                focus: { score: -2, confidence: 0.8, actor: "市府發言人", evidence: "點名特定官員與發言人是否為言論負責。", reason: "高度聚焦人物口水戰。", method: "manual" },
                tone: { score: -2, confidence: 0.85, actor: "受訪者", evidence: "痛批『抹黑』、『政治操弄』。", reason: "明顯情緒性衝突抗辯。", method: "manual" }
              }
            }
          ]
        },
        {
          id: 3,
          title: "中火燃氣機組都審爭議",
          description: "台中電廠燃氣機組都市計畫審查卡關引發中央與地方攻防。",
          is_demo: false,
          question: "是否支持推進中火燃氣機組審查？",
          dimensions: [
            { key: "position", name: "主張方向", question: "是否支持推進中火燃氣機組審查？", left: "反對／保留", right: "支持／加速", opposition: true },
            { key: "focus", name: "討論焦點", question: "聚焦能源環保政策，還是跨黨派政治對立？", left: "人物政黨攻防", right: "能源空污政策", opposition: false },
            { key: "tone", name: "表達方式", question: "呈現激烈指責，還是政策論證？", left: "衝突斥責", right: "協商合作", opposition: false }
          ],
          articles: [
            {
              id: 301,
              title: "齊轟中火燃氣機組都審卡關15個月 綠委喊話盧秀燕：放下政治仇恨",
              source: "聯合新聞網",
              author: "記者趙容萱／台中即時報導",
              published_at: "2026-09-04 17:28:02",
              url: "https://udn.com/news/story/6656/9735073",
              analysis_status: "reviewed",
              assessments: {
                position: { score: 2, confidence: 0.85, actor: "立委蔡其昌等人", evidence: "強調燃氣取代燃煤能改善空污，呼籲加速通過審查。", reason: "明確主張加速推進燃氣機組審查。", method: "manual" },
                focus: { score: -1, confidence: 0.65, actor: "民進黨立委團", evidence: "喊話盧秀燕市長『放下政治仇恨』。", reason: "帶有地方首長責任指責。", method: "manual" },
                tone: { score: -2, confidence: 0.8, actor: "立委發言", evidence: "齊轟卡關、痛批政治操弄空污。", reason: "衝突斥責語氣鮮明。", method: "manual" }
              }
            },
            {
              id: 302,
              title: "中火二期環評市府嚴格把關 盧秀燕：絕不妥協市民健康",
              source: "聯合新聞網",
              author: "台中即時報導",
              published_at: "2026-09-04 14:00:00",
              url: "https://udn.com/news/story/6656/9734999",
              analysis_status: "reviewed",
              assessments: {
                position: { score: -2, confidence: 0.85, actor: "台中市長盧秀燕", evidence: "主張增一氣拆一煤，台電未承諾除役前決不同意都審放行。", reason: "明確反對在沒有拆煤承諾下通過審查，與立委主張相反對立。", method: "manual" },
                focus: { score: 1, confidence: 0.7, actor: "台中市政府", evidence: "提出碳排總量、空污減量具體數字要求。", reason: "討論實質環境指標與法規要求。", method: "manual" },
                tone: { score: -1, confidence: 0.75, actor: "市府聲明", evidence: "強硬表態『絕不妥協』。", reason: "展示防守堅決立場。", method: "manual" }
              }
            }
          ]
        },
        {
          id: 4,
          title: "陳其邁政績與跨市政治交鋒",
          description: "南北雙都市長對施政成果與統籌分配款展開公開辯論。",
          is_demo: false,
          question: "如何評價陳其邁的高雄施政表現？",
          dimensions: [
            { key: "position", name: "主張方向", question: "如何評價陳其邁的高雄施政表現？", left: "質疑／批評", right: "肯定／讚許", opposition: true },
            { key: "focus", name: "討論焦點", question: "文字主要聚焦市政數據，還是市長政治前途？", left: "政治人物動向", right: "市政數據評比", opposition: false },
            { key: "tone", name: "表達方式", question: "主要呈現互相揶揄，還是公共政策對話？", left: "冷嘲熱諷", right: "理性對話", opposition: false }
          ],
          articles: [
            {
              id: 401,
              title: "蔣萬安談政績酸『推銷高雄有功』 陳其邁回敬：台北資源多應更有格局",
              source: "聯合新聞網",
              author: "政治綜合報導",
              published_at: "2026-09-04 15:30:00",
              url: "https://udn.com/news/story/6656/9734850",
              analysis_status: "reviewed",
              assessments: {
                position: { score: 1, confidence: 0.75, actor: "陳其邁", evidence: "舉演唱會經濟與招商成效，強調高雄轉型成績有目共睹。", reason: "為自身施政做強烈肯定與辯護。", method: "manual" },
                focus: { score: -1, confidence: 0.65, actor: "雙方市長", evidence: "你來我往『推銷員』與『天龍國視角』標籤。", reason: "人物互虧與政治交鋒。", method: "manual" },
                tone: { score: -1, confidence: 0.7, actor: "新聞標題呈現", evidence: "『酸』、『回敬』。", reason: "典型政治對抗語態。", method: "manual" }
              }
            },
            {
              id: 402,
              title: "陳其邁任期將屆 綠基層力拱戰新北或承擔更大職責",
              source: "聯合新聞網",
              author: "台北即時報導",
              published_at: "2026-09-04 11:20:00",
              url: "https://udn.com/news/story/6656/9734500",
              analysis_status: "unreviewed",
              assessments: {
                position: { score: null, confidence: 0, actor: "", evidence: "", reason: "純屬選戰揣測，無政策立場依據。", method: "headline-rules-v1" },
                focus: { score: -2, confidence: 0.8, actor: "黨內基層", evidence: "點名市長人選與下屆大選佈局。", reason: "純粹政壇職務流言。", method: "headline-rules-v1" },
                tone: { score: 0, confidence: 0.5, actor: "報導筆調", evidence: "平實陳述派系觀點。", reason: "中性陳述。", method: "headline-rules-v1" }
              }
            }
          ]
        }
      ]
    };

    // State Variables
    let currentMode = 'demo'; // 'demo' | 'real'
    let currentEventId = 1;
    let leftArticleId = 101;
    let rightArticleId = 102;
    let editingTarget = 'left'; // 'left' | 'right'

    // Formatters
    const fmt = (val) => {
      if (!val) return '—';
      const d = new Date(val);
      const m = String(d.getMonth() + 1).padStart(2, '0');
      const day = String(d.getDate()).padStart(2, '0');
      const h = String(d.getHours()).padStart(2, '0');
      const min = String(d.getMinutes()).padStart(2, '0');
      return `${m}/${day} ${h}:${min}`;
    };

    // Initialize Page
    function init() {
      renderEventList();
      loadEvent(DATASETS[currentMode][0].id);
    }

    // Toggle Dataset (Demo vs Real)
    function toggleDataset(mode) {
      currentMode = mode;
      document.getElementById('btn-real').classList.toggle('active', mode === 'real');
      document.getElementById('btn-demo').classList.toggle('active', mode === 'demo');
      document.getElementById('breadcrumb-dataset-name').innerText = mode === 'demo' ? '示範案例展示' : '真實新聞觀察';
      document.getElementById('sidebar-footer-text').innerText = mode === 'demo' 
        ? '虛構教學資料 · 3 個示範來源' 
        : 'RSS 少量新聞樣本 · 聯合新聞網';
      
      const events = DATASETS[currentMode];
      renderEventList(events);
      if (events.length > 0) {
        loadEvent(events[0].id);
      }
    }

    // Render Sidebar Event List
    function renderEventList(eventsToRender = null) {
      const events = eventsToRender || DATASETS[currentMode];
      const container = document.getElementById('event-list-container');
      document.getElementById('event-count-badge').innerText = String(events.length).padStart(2, '0');
      
      container.innerHTML = events.map(e => `
        <button class="event-button ${e.id === currentEventId ? 'selected' : ''}" onclick="loadEvent(${e.id})">
          <span class="event-button-title">${e.title}</span>
          <span class="event-meta">
            <span>${e.articles.length} 篇報導</span>
            <span>${e.is_demo ? '示範' : '最新 09/04'}</span>
          </span>
        </button>
      `).join('');
    }

    // Search events
    function handleSearch(keyword) {
      const q = keyword.trim().toLowerCase();
      const filtered = DATASETS[currentMode].filter(e => e.title.toLowerCase().includes(q));
      renderEventList(filtered);
    }

    // Load an Event
    function loadEvent(eventId) {
      currentEventId = eventId;
      const event = DATASETS[currentMode].find(e => e.id === eventId) || DATASETS[currentMode][0];
      
      // Update sidebar selection
      document.querySelectorAll('.event-button').forEach(btn => btn.classList.remove('selected'));
      renderEventList();

      // Update Headings
      document.getElementById('event-type-label').innerText = event.is_demo ? 'DEMO / 虛構教學事件' : 'EVENT / 事件觀察';
      document.getElementById('event-badge-label').innerText = event.is_demo ? '示範' : '分組待核對';
      document.getElementById('event-title').innerText = event.title;
      document.getElementById('event-article-count').innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M6 6h10"/><path d="M6 10h10"/></svg>
        ${event.articles.length} 篇報導
      `;
      document.getElementById('event-num-id').innerText = String(event.id).padStart(2, '0');
      document.getElementById('timeline-count-badge').innerText = event.articles.length;

      const reviewedCount = event.articles.filter(a => a.analysis_status === 'reviewed').length;
      document.getElementById('event-reviewed-count').innerText = `${reviewedCount} 篇已標註`;

      if (event.is_demo) {
        document.getElementById('banner-note').style.display = 'flex';
        document.getElementById('banner-note-text').innerText = '此事件與文章皆為虛構教學資料，展示完整的「相反主張」識別門檻與依據留存機制。';
      } else {
        document.getElementById('banner-note').style.display = 'flex';
        document.getElementById('banner-note-text').innerText = '本事件資料來自聯合新聞網公開 RSS 標題與中繼資料；各維度分數反映文中主張，不推定媒體政治立場。';
      }

      // Default Left & Right articles
      leftArticleId = event.articles[0] ? event.articles[0].id : null;
      rightArticleId = event.articles[1] ? event.articles[1].id : (event.articles[0] ? event.articles[0].id : null);

      populateArticleDropdowns(event);
      updateComparison();
      renderTimeline(event);
    }

    // Populate Dropdown Selectors
    function populateArticleDropdowns(event) {
      const selectA = document.getElementById('select-article-a');
      const selectB = document.getElementById('select-article-b');

      selectA.innerHTML = event.articles.map(a => `
        <option value="${a.id}" ${a.id === leftArticleId ? 'selected' : ''}>${a.title}</option>
      `).join('');

      selectB.innerHTML = event.articles.map(a => `
        <option value="${a.id}" ${a.id === rightArticleId ? 'selected' : ''}>${a.title}</option>
      `).join('');
    }

    // Change Article Selection
    function changeArticle(target, id) {
      id = Number(id);
      if (target === 'left') {
        leftArticleId = id;
      } else {
        rightArticleId = id;
      }
      updateComparison();
      renderTimeline(getCurrentEvent());
    }

    function getCurrentEvent() {
      return DATASETS[currentMode].find(e => e.id === currentEventId);
    }

    // Calculate Comparison and Render Map
    function updateComparison() {
      const event = getCurrentEvent();
      const articleA = event.articles.find(a => a.id === leftArticleId);
      const articleB = event.articles.find(a => a.id === rightArticleId);

      if (!articleA || !articleB) return;

      // Update Card A
      document.getElementById('card-a-source').innerText = articleA.source;
      document.getElementById('card-a-title').innerText = articleA.title;
      document.getElementById('card-a-byline').innerText = `${fmt(articleA.published_at)} · ${articleA.author || '未提供作者'}`;
      document.getElementById('card-a-status').innerText = articleA.analysis_status === 'reviewed' ? '已標註' : '待判定';
      document.getElementById('card-a-status').className = `status-tag ${articleA.analysis_status === 'reviewed' ? 'reviewed' : ''}`;
      document.getElementById('card-a-link').style.display = articleA.url ? 'inline-flex' : 'none';
      if (articleA.url) document.getElementById('card-a-link').href = articleA.url;

      // Update Card B
      document.getElementById('card-b-source').innerText = articleB.source;
      document.getElementById('card-b-title').innerText = articleB.title;
      document.getElementById('card-b-byline').innerText = `${fmt(articleB.published_at)} · ${articleB.author || '未提供作者'}`;
      document.getElementById('card-b-status').innerText = articleB.analysis_status === 'reviewed' ? '已標註' : '待判定';
      document.getElementById('card-b-status').className = `status-tag ${articleB.analysis_status === 'reviewed' ? 'reviewed' : ''}`;
      document.getElementById('card-b-link').style.display = articleB.url ? 'inline-flex' : 'none';
      if (articleB.url) document.getElementById('card-b-link').href = articleB.url;

      // Calculate Dimension Comparison
      const posA = articleA.assessments.position || {};
      const posB = articleB.assessments.position || {};

      const posKnown = posA.score !== null && posB.score !== null && (posA.confidence || 0) >= 0.6 && (posB.confidence || 0) >= 0.6;
      const isOpposed = posKnown && (posA.score * posB.score < 0) && (Math.abs(posA.score - posB.score) >= 2);

      const statusBox = document.getElementById('comparison-status-box');
      if (isOpposed) {
        statusBox.className = 'comparison-status opposed';
        document.getElementById('comparison-status-title').innerText = '辨識到相反主張';
        document.getElementById('comparison-status-detail').innerText = `主張方向維度（分差 ${Math.abs(posA.score - posB.score)}，雙方信心均 ≥ 60%）`;
      } else if (posA.score !== null && posB.score !== null && posA.score !== posB.score) {
        statusBox.className = 'comparison-status different';
        document.getElementById('comparison-status-title').innerText = '觀點呈現不同';
        document.getElementById('comparison-status-detail').innerText = '雖有差異，但未達對立門檻或屬不同維度';
      } else {
        statusBox.className = 'comparison-status undetermined';
        document.getElementById('comparison-status-title').innerText = '主張方向待判定';
        document.getElementById('comparison-status-detail').innerText = '尚無足夠依據或信心不足，保留未判定狀態';
      }

      // Render 3 Dimensions
      const dimensionsHtml = event.dimensions.map(dim => {
        const a = articleA.assessments[dim.key] || { score: null, confidence: 0, actor: '', evidence: '', reason: '' };
        const b = articleB.assessments[dim.key] || { score: null, confidence: 0, actor: '', evidence: '', reason: '' };

        const aLeftPercent = a.score !== null ? ((a.score + 2) / 4) * 100 : 50;
        const bLeftPercent = b.score !== null ? ((b.score + 2) / 4) * 100 : 50;

        const dimOpposed = dim.opposition && isOpposed;

        return `
          <div class="dimension-row">
            <div class="dimension-title-line">
              <h3>${dim.name}</h3>
              ${dimOpposed ? '<span class="opposed-pill">相反主張</span>' : `<span style="font-size: .74rem; color: #8899af;">${dim.opposition ? '立場維度' : '呈現維度'}</span>`}
            </div>
            <p class="dimension-question">${dim.question}</p>
            
            <div class="axis-labels">
              <span>${dim.left} (−2)</span>
              <span>${dim.right} (+2)</span>
            </div>

            <div class="axis-container">
              <span class="axis-tick" style="left: 0%;"></span>
              <span class="axis-tick" style="left: 25%;"></span>
              <span class="axis-tick" style="left: 50%;"></span>
              <span class="axis-tick" style="left: 75%;"></span>
              <span class="axis-tick" style="left: 100%;"></span>

              ${a.score !== null ? `
                <div class="axis-marker a" style="left: ${aLeftPercent}%;" title="文章 A：${a.score > 0 ? '+' : ''}${a.score}">A</div>
              ` : ''}

              ${b.score !== null ? `
                <div class="axis-marker b" style="left: ${bLeftPercent}%;" title="文章 B：${b.score > 0 ? '+' : ''}${b.score}">B</div>
              ` : ''}
            </div>

            <div class="axis-scale">
              <span>−2</span>
              <span>−1</span>
              <span>0</span>
              <span>+1</span>
              <span>+2</span>
            </div>

            <div class="assessment-summary-row">
              <span>
                <b class="a">A</b> ${a.score !== null ? (a.score > 0 ? '+' : '') + a.score : '未判定'}
                ${a.score !== null ? `<small>· ${Math.round(a.confidence * 100)}% 信心</small>` : ''}
              </span>
              <span>
                <b class="b">B</b> ${b.score !== null ? (b.score > 0 ? '+' : '') + b.score : '未判定'}
                ${b.score !== null ? `<small>· ${Math.round(b.confidence * 100)}% 信心</small>` : ''}
              </span>
            </div>

            <details class="evidence-details">
              <summary>查看判定依據與引文</summary>
              <div class="evidence-grid">
                <div class="evidence-box">
                  <strong>A · ${a.actor || '主張者未判定'}</strong>
                  ${a.evidence ? `<blockquote>${a.evidence}</blockquote>` : '<p style="color: #94a3b8;">未標註具體引文</p>'}
                  <p>${a.reason || '尚無理由描述'}</p>
                  <small>評定方式：${a.method === 'demo' ? '示範案例預設' : (a.method === 'manual' ? '人工覆核' : '標題規則提示')}</small>
                </div>
                <div class="evidence-box">
                  <strong>B · ${b.actor || '主張者未判定'}</strong>
                  ${b.evidence ? `<blockquote>${b.evidence}</blockquote>` : '<p style="color: #94a3b8;">未標註具體引文</p>'}
                  <p>${b.reason || '尚無理由描述'}</p>
                  <small>評定方式：${b.method === 'demo' ? '示範案例預設' : (b.method === 'manual' ? '人工覆核' : '標題規則提示')}</small>
                </div>
              </div>
            </details>
          </div>
        `;
      }).join('');

      document.getElementById('dimensions-container').innerHTML = dimensionsHtml;
    }

    // Render Chronological Timeline
    function renderTimeline(event) {
      const container = document.getElementById('timeline-items');
      const sorted = [...event.articles].sort((a, b) => new Date(a.published_at) - new Date(b.published_at));

      container.innerHTML = sorted.map(article => {
        const isA = article.id === leftArticleId;
        const isB = article.id === rightArticleId;
        const isChosen = isA || isB;

        return `
          <li class="timeline-item ${isChosen ? 'active' : ''}">
            <span class="timeline-node"></span>
            <div class="timeline-time">${fmt(article.published_at)}</div>
            <div class="timeline-title">
              ${isA ? '<span class="letter" style="display:inline-grid; margin-right:4px; width:18px; height:18px; font-size: .65rem;">A</span>' : ''}
              ${isB ? '<span class="letter" style="display:inline-grid; margin-right:4px; width:18px; height:18px; font-size: .65rem; background: var(--orange-bg); color: var(--orange);">B</span>' : ''}
              ${article.title}
            </div>
            <div class="timeline-source">${article.source} · ${article.analysis_status === 'reviewed' ? '已標註' : '待判定'}</div>
            <div class="timeline-actions">
              ${article.id !== leftArticleId ? `
                <button onclick="setAsB(${article.id})">選為 B 比較 →</button>
              ` : ''}
              <button onclick="openModalForArticle(${article.id})">標註</button>
              ${article.url ? `<a href="${article.url}" target="_blank" style="color: #64748b;">原文 ↗</a>` : ''}
            </div>
          </li>
        `;
      }).join('');
    }

    function setAsB(articleId) {
      rightArticleId = articleId;
      document.getElementById('select-article-b').value = articleId;
      updateComparison();
      renderTimeline(getCurrentEvent());
      switchTab('compare');
      showNotice('已切換文章 B 並更新觀點地圖。');
    }

    // Switch between Comparison & Timeline
    function switchTab(tab) {
      document.getElementById('tab-compare-btn').classList.toggle('active', tab === 'compare');
      document.getElementById('tab-timeline-btn').classList.toggle('active', tab === 'timeline');

      const compView = document.getElementById('comparison-view');
      const timelineCol = document.getElementById('timeline-container');
      const grid = document.getElementById('main-content-grid');

      if (tab === 'timeline') {
        compView.style.display = 'none';
        timelineCol.style.width = '100%';
        timelineCol.style.borderLeft = 'none';
        timelineCol.style.background = '#ffffff';
        timelineCol.style.padding = '28px';
        timelineCol.style.borderRadius = '10px';
        timelineCol.style.border = '1px solid var(--line)';
        grid.style.gridTemplateColumns = '1fr';
      } else {
        compView.style.display = 'block';
        timelineCol.style.width = '300px';
        timelineCol.style.borderLeft = '1px solid var(--line)';
        timelineCol.style.background = 'transparent';
        timelineCol.style.padding = '0 0 0 24px';
        timelineCol.style.borderRadius = '0';
        timelineCol.style.border = 'none';
        grid.style.gridTemplateColumns = 'minmax(0, 1fr) 300px';
      }
    }

    // Toggle Method Explanation Panel
    function toggleMethodPanel() {
      const p = document.getElementById('method-panel');
      p.style.display = p.style.display === 'none' ? 'block' : 'none';
    }

    // Show temporary notice
    function showNotice(msg) {
      const container = document.getElementById('notice-container');
      container.innerHTML = `
        <div class="notice">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>
          <span>${msg}</span>
          <button class="notice-close" onclick="this.parentElement.remove()">&times;</button>
        </div>
      `;
      setTimeout(() => {
        if (container.firstElementChild) container.firstElementChild.remove();
      }, 5000);
    }

    // Modal Operations
    let activeEditingArticle = null;

    function openEditModal(target) {
      editingTarget = target;
      const event = getCurrentEvent();
      const article = event.articles.find(a => a.id === (target === 'left' ? leftArticleId : rightArticleId));
      if (!article) return;
      openModalForArticle(article.id);
    }

    function openModalForArticle(articleId) {
      const event = getCurrentEvent();
      const article = event.articles.find(a => a.id === articleId);
      if (!article) return;

      activeEditingArticle = article;
      document.getElementById('modal-article-title').innerText = article.title;

      // Build form inputs
      const container = document.getElementById('modal-dimensions-inputs');
      container.innerHTML = event.dimensions.map(d => {
        const current = article.assessments[d.key] || { score: null, confidence: 0, actor: '', evidence: '', reason: '' };
        return `
          <div style="border: 1px solid #e2e8f0; border-radius: 8px; padding: 14px; margin-bottom: 14px;">
            <div style="font-weight: 700; color: #1e293b; font-size: .9rem; margin-bottom: 4px;">${d.name}</div>
            <p style="font-size: .78rem; color: #64748b; margin-bottom: 10px;">${d.question}</p>

            <div class="form-row">
              <div class="form-group">
                <label>方向評分 (−2 ~ +2)</label>
                <select id="score-${d.key}">
                  <option value="" ${current.score === null ? 'selected' : ''}>未判定</option>
                  <option value="-2" ${current.score === -2 ? 'selected' : ''}>−2 · ${d.left}（明確）</option>
                  <option value="-1" ${current.score === -1 ? 'selected' : ''}>−1 · ${d.left}（傾向）</option>
                  <option value="0" ${current.score === 0 ? 'selected' : ''}>0 · 中性／兼具</option>
                  <option value="1" ${current.score === 1 ? 'selected' : ''}>+1 · ${d.right}（傾向）</option>
                  <option value="2" ${current.score === 2 ? 'selected' : ''}>+2 · ${d.right}（明確）</option>
                </select>
              </div>

              <div class="form-group">
                <label>信心水準 (Confidence)</label>
                <select id="conf-${d.key}">
                  <option value="0" ${current.confidence === 0 ? 'selected' : ''}>0% · 尚無依據</option>
                  <option value="0.55" ${current.confidence === 0.55 ? 'selected' : ''}>55% · 低信心</option>
                  <option value="0.7" ${current.confidence === 0.7 ? 'selected' : ''}>70% · 中信心</option>
                  <option value="0.9" ${current.confidence === 0.9 ? 'selected' : ''}>90% · 高信心</option>
                  <option value="1.0" ${current.confidence === 1.0 ? 'selected' : ''}>100% · 充分依據</option>
                </select>
              </div>
            </div>

            <div class="form-group">
              <label>主張者 (Actor)</label>
              <input type="text" id="actor-${d.key}" value="${current.actor || ''}" placeholder="例如：某立法委員、專家學者、受訪市民">
            </div>

            <div class="form-group">
              <label>文字依據 (Evidence 引文)</label>
              <textarea id="evidence-${d.key}" rows="2" placeholder="填入內文中支持判定的具體引文">${current.evidence || ''}</textarea>
            </div>

            <div class="form-group" style="margin-bottom: 0;">
              <label>判定理由 (Reason)</label>
              <textarea id="reason-${d.key}" rows="2" placeholder="說明此文字為何指向該維度立場">${current.reason || ''}</textarea>
            </div>
          </div>
        `;
      }).join('');

      document.getElementById('edit-modal').classList.add('open');
    }

    function closeEditModal() {
      document.getElementById('edit-modal').classList.remove('open');
      activeEditingArticle = null;
    }

    function handleSaveAnnotation(e) {
      e.preventDefault();
      if (!activeEditingArticle) return;

      const event = getCurrentEvent();
      event.dimensions.forEach(d => {
        const scoreVal = document.getElementById(`score-${d.key}`).value;
        const confVal = parseFloat(document.getElementById(`conf-${d.key}`).value);
        const actorVal = document.getElementById(`actor-${d.key}`).value.trim();
        const evidenceVal = document.getElementById(`evidence-${d.key}`).value.trim();
        const reasonVal = document.getElementById(`reason-${d.key}`).value.trim();

        activeEditingArticle.assessments[d.key] = {
          score: scoreVal !== "" ? parseInt(scoreVal) : null,
          confidence: scoreVal !== "" ? confVal : 0,
          actor: actorVal,
          evidence: evidenceVal,
          reason: reasonVal,
          method: 'manual'
        };
      });

      activeEditingArticle.analysis_status = 'reviewed';
      closeEditModal();
      updateComparison();
      renderTimeline(event);
      showNotice(`已成功儲存「${activeEditingArticle.title.substring(0, 16)}...」之標註，地圖已更新！`);
    }

    // Auto Run on load
    window.addEventListener('DOMContentLoaded', init);
  
