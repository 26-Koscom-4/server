# Page/Modal Data Requirements

본 문서는 UI 렌더링에 필요한 하드코딩/샘플 데이터 및 구조를 전수 정리한 것이다. 실제 값은 `js/app.js`의 `sampleData`, 각 렌더 함수, 그리고 `index.html`의 정적 마크업에서 확인된다.

## Field Conventions

- **id/ticker 규칙**
  - 모든 village 객체/참조는 `id`를 포함한다.
  - 모든 asset 객체/참조는 `ticker`(또는 `assetId`)를 포함한다. 본 문서에서는 `ticker` 사용.
- **단위 규칙**
  - `returnRate`/`allocation`은 **percent point**로 통일 (예: `12.5` = 12.5%).
  - 금액은 **KRW 정수**로 통일 (예: `15000000`).
- **derived 필드**
  - `bannerVisible`, `unreadBadgeVisible` 등은 **derived(optional)**로 표기한다.
- **HTML 문자열**
  - Daily fallback은 `...Html` 또는 `HTML string`임을 명시한다.

## Main (mainPage)

### Hero
| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| hero.title | string | text | no | "개미 마을" | `index.html` 메인 히어로 섹션 |
| hero.subtitle | string | text | no | "방치된 내 주식, 개미 마을이 깨워줍니다." | `index.html` 메인 히어로 섹션 |
| hero.cta.label | string | text | no | "내 마을 시작하기 🚀" | `index.html` 메인 히어로 섹션 |
| hero.cta.targetPage | string | pageName | no | "villages" | `index.html` CTA onclick |

### World Map / Hotspots
| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| map.title | string | text | no | "전 세계 나의 투자 마을" | `index.html` 메인 월드맵 섹션 |
| map.hotspots[] | array | object list | no | 4개 (국장/미장/배당/글로벌ETF) | `index.html` map-hotspot, `js/app.js:542-567` |
| map.hotspots[].villageId | string | id | no | "village-korea" | `fixtures/ui_state_main.json` |
| map.hotspots[].villageName | string | name | no | "국장마을" | `index.html` / `js/app.js:542-567` |
| map.hotspots[].badgeId | string | DOM id | no | "badge-국장마을" | `js/app.js:546-551` |
| map.hotspots[].unreadBadgeVisible | boolean | derived | yes | true/false | `js/app.js:521-567` |

### Recommendation Banner
| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| recommendation.hasNewRecommendation | boolean | flag | no | true | `js/app.js:93-97`, `js/app.js:807-833` |
| recommendation.lastCheckedDate | string | ISO datetime | no | null | `js/app.js:93-97`, `js/app.js:833-840` |
| recommendation.recommendedVillages | string[] | list | no | ["원자재 마을","신흥국 마을","채권 마을"] | `js/app.js:93-97` |
| recommendation.bannerVisible | boolean | derived | yes | true/false | `js/app.js:807-827` |

### Asset Chart (Chart.js doughnut)
| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| assetChart.type | string | chart type | no | "doughnut" | `js/app.js:967` |
| assetChart.data.labels[] | string[] | asset types | no | ["기술주","성장주","AI주",...] | `js/app.js:887-934` |
| assetChart.data.datasets[0].data[] | number[] | KRW | no | [11500000, 3500000, 6000000, ...] | `js/app.js:887-934` |
| assetChart.data.datasets[0].backgroundColor[] | string[] | rgba | no | ["rgba(...)", ...] | `js/app.js:915-933` |
| assetChart.options | object | Chart.js options (optional) | no | legend hidden, tooltip formatter, cutout 60% | `js/app.js:972-1000` |
| assetLegend.items[] | array | object list | no | {label,value,percentage,icon,color} | `js/app.js:936-964` |

## Villages (villagesPage)

| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| villages[] | array | object list | no | 6개 마을 | `js/app.js:97-188`, `js/app.js:328-365` |
| villages[].id | string | id | no | "village-us" | `fixtures/ui_state_villages.json` |
| villages[].name | string | name | no | "미장마을" | `js/app.js:102` |
| villages[].icon | string | emoji | no | "🇺🇸" | `js/app.js:103` |
| villages[].assets[] | array | object list | no | {name,type,value,ticker} | `js/app.js:104-182` |
| villages[].assets[].ticker | string | ticker | no | "AAPL" | `fixtures/ui_state_villages.json` |
| villages[].assets[].value | number | KRW | no | 4000000 | `js/app.js:104-182` |
| villages[].totalValue | number | KRW | no | 15000000 | `js/app.js:110` |
| villages[].returnRate | number | percent point | no | 12.5 | `js/app.js:111` |
| villages[].allocation | number | percent point | no | 32.3 | `js/app.js:112` |

## Briefing (briefingPage)

### Village Selector
| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| selector.villages[] | array | object list | no | {id,name,icon,returnRate} | `js/app.js:609-631` |
| selector.villages[].id | string | id | no | "village-us" | `fixtures/ui_state_briefing.json` |
| selector.villages[].returnRate | number | percent point | no | 12.5 | `js/app.js:621-627` |

### Briefing Content (선택 마을)
| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| briefing.selectedVillage.id | string | id | no | "village-us" | `fixtures/ui_state_briefing.json` |
| briefing.selectedVillage | object | village | no | {name, totalValue, returnRate, allocation} | `js/app.js:640-702` |
| briefing.selectedVillage.assets[].ticker | string | ticker | no | "AAPL" | `fixtures/ui_state_briefing.json` |
| briefing.typeTextMap | object | map | no | growth→"성장형" 등 | `js/app.js:568-585` |
| briefing.goalTextMap | object | map | no | long-term→"장기 투자" 등 | `js/app.js:588-606` |
| briefing.adviceMap | object | map | no | type별 조언 텍스트 | `js/app.js:619-702` |
| briefing.marketAdviceMap | object | map | no | type별 시장 조언 HTML | `js/app.js:703-716` |

## Daily (dailyBriefingPage)

| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| daily.selectedVillage.id | string | id | no | "village-dividend" | `fixtures/ui_state_daily.json` |
| daily.selectedVillage | object | village | no | {name, icon, totalValue, returnRate, allocation, assets[]} | `js/app.js:458-509` |
| daily.selectedVillage.assets[].ticker | string | ticker | no | "SCHD" | `fixtures/ui_state_daily.json` |
| daily.briefingSections[] | array | object list | no | 마을 요약/보유자산/투자정보/오늘의 조언 | `js/app.js:470-507` |
| daily.fallbackStaticContentHtml | string | HTML string (optional) | no | "<h3>...</h3>..." | `index.html` 데일리 브리핑 섹션 |

## Neighbors (neighborsPage)

| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| neighbors.recommendations[] | array | object list | no | 3개 카드 | `index.html` 이웃 개미 섹션 |
| neighbors.recommendations[].id | string | id | no | "commodities" | 문서화용 식별자 |
| neighbors.recommendations[].villageId | string | id | no | "village-commodities" | `fixtures/ui_state_neighbors.json` |
| neighbors.recommendations[].name | string | text | no | "원자재 마을" | `index.html` |
| neighbors.recommendations[].subtitle | string | text | no | "금, 은, 원유 ETF" | `index.html` |
| neighbors.recommendations[].reason | string | text | no | 추천 이유 본문 | `index.html` |
| neighbors.recommendations[].assets[] | array | object list | no | {ticker,label} | `index.html` |
| neighbors.recommendations[].correlation | number | score | no | -0.23 | `index.html` |
| neighbors.recommendations[].correlationNote | string | text | no | "낮은 상관관계 = 분산 효과 우수" | `index.html` |
| neighbors.recommendations[].addVillageName | string | name | no | "원자재 마을" | `index.html` addVillage 호출 |
| neighbors.recommendations[].addVillageId | string | id | no | "village-commodities" | `fixtures/ui_state_neighbors.json` |

## MyPage (mypagePage)

| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| user_profile.name | string | text | no | "김직장" | `js/app.js:90-94`, `js/app.js:1003-1010` |
| user_profile.theme | string | enum | no | "light"/"dark" | `js/app.js:90-94`, `js/app.js:1007-1011` |
| settings.briefing_time | string | HH:mm | no | "08:00" | `js/app.js:183-186`, `js/app.js:1012-1017` |
| settings.voice_speed | number | multiplier | no | 1.0 | `js/app.js:183-186`, `js/app.js:1014-1018` |
| statistics.totalAssets | number | KRW | yes | 46500000 | `js/app.js:1043-1053` |
| statistics.villageCount | number | count | yes | 6 | `js/app.js:1055-1057` |
| statistics.avgReturn | number | percent point | yes | 7.8 | `js/app.js:1059-1066` |
| statistics.assetCount | number | count | yes | 19 | `js/app.js:1069-1076` |
| activity.items[] | array | object list | yes | {title,time} | `index.html` 활동 리스트 초기값, `js/app.js:1095-1121` |
| mydata_integration.* | object | integration status | no | is_integrated, last_integration_date 등 | `js/app.js:2231-2249`, `js/app.js:1550-1576` |
| investment_test.* | object | test summary | no | mainType, percentages 등 | `js/app.js:2010-2148` |

## Village Modal (villageModal)

| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| modal.village.id | string | id | no | "village-us" | `fixtures/ui_state_villageModal.json` |
| modal.village | object | village | no | {name, icon, assets, totalValue, returnRate, allocation} | `js/app.js:373-439` |
| modal.village.assets[].ticker | string | ticker | no | "AAPL" | `fixtures/ui_state_villageModal.json` |
| modal.typeTextMap | object | map | no | growth→"성장형" 등 | `js/app.js:568-585` |
| modal.goalTextMap | object | map | no | long-term→"장기 투자" 등 | `js/app.js:588-606` |

## Investment Test Modal (investmentTestModal)

| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| investmentTypes | object | map | no | conservative/moderate 등 | `js/app.js:1596-1655` |
| investmentQuestions[] | array | object list | no | 25개 질문 | `js/app.js:1660+` |
| testState.currentQuestionIndex | number | index | yes | 0 | `js/app.js:1924-1990` |
| testState.userAnswers[] | number[] | index list | yes | [0,2,...] | `js/app.js:1930-1990` |
| testResult.scores | object | map | yes | {conservative:10,...} | `js/app.js:2016-2053` |
| testResult.percentages | object | % strings | yes | {conservative:"20.0",...} | `js/app.js:2036-2050` |
| resultChart.type | string | chart type | no | "doughnut" | `js/app.js:2110-2155` |
| resultChart.data.labels[] | string[] | type names | no | ["안정형",...] | `js/app.js:2112-2117` |
| resultChart.data.datasets[0].data[] | number[] | % | no | [20.0, 15.0, ...] | `js/app.js:2112-2117` |

## MyData Modal (mydataModal)

| key | type | unit/format | derived | example | source |
|---|---|---|---|---|---|
| mockInstitutions[] | array | object list | no | 7개 기관 | `js/app.js:1260-1273` |
| mockInstitutions[].id | string | id | no | "kb" | `js/app.js:1260-1273` |
| mockInstitutions[].name | string | text | no | "KB증권" | `js/app.js:1260-1273` |
| mockInstitutions[].icon | string | emoji | no | "🏦" | `js/app.js:1260-1273` |
| mockInstitutions[].description | string | text | no | "보유 주식 3종목" | `js/app.js:1260-1273` |
| consent.* | boolean | flag | no | true/false | `js/app.js:1298-1337` |
| selectedInstitutions[] | string[] | ids | no | ["kb","mirae"] | `js/app.js:1289-1306`, `js/app.js:1397-1460` |
| loadingMessages[] | string[] | text | no | "금융기관 연결 중..." 등 | `js/app.js:1476-1490` |
| loading.progress | number | % | yes | 40 | `js/app.js:1492-1516` |
| completionSummary[] | array | object list | yes | {id,name,icon,status} | `js/app.js:1520-1549` |
| mydata_integration.* | object | saved data | no | is_integrated, last_integration_date 등 | `js/app.js:1550-1576` |
