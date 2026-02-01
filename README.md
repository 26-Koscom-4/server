# FastAPI KAMI Server

프론트엔드 개발자가 SPA 화면에 API를 바로 붙일 수 있도록, 목적/화면/호출 흐름 중심으로 정리한 가이드입니다.  
필드 스키마와 예시는 Swagger(`/docs`)에서 확인하세요.

## Quick Start

### 로컬 실행 (uvicorn)

Python 버전: 3.13.5

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### 로컬 실행 (Docker)

```powershell
docker build -t kami-mock .
docker run --rm -p 8000:8000 kami-mock
```

- Base URL: http://localhost:8000
- Swagger Docs: http://localhost:8000/docs

## API Overview (의미 중심)

아래 표는 “무슨 화면에서, 어떤 목적으로 호출하는지”에 집중합니다.  
필드 상세 스펙은 `/docs`에서 확인하세요.

| Method | Path | Purpose | Used By (UI/화면) | Notes |
|---|---|---|---|---|
| GET | /health | 서버 상태 체크 | 공통 | 헬스체크 |
| GET | /api/main | 메인 화면 초기 렌더 데이터 | main | 자산 차트/지도 뱃지/추천 배너 |
| GET | /api/villages | 마을 카드 리스트 | villages | 마을 관리 화면 진입 시 |
| GET | /api/villages/{id} | 마을 상세 모달/데일리 진입 | villages modal, daily | 현재는 id 무시하고 동일 fixture 반환 |
| GET | /api/briefing | 아침 브리핑 화면 데이터 | briefing | 선택 마을 기준 콘텐츠 |
| GET | /api/daily | 데일리 브리핑 화면 데이터 | daily | 필요 시 villageId query를 확장 가능 |
| GET | /api/neighbors | 이웃 개미 추천 카드 | neighbors | “마을 추가” CTA |
| GET | /api/mypage | 마이페이지 요약/설정/상태 | mypage | 마이데이터/진단 결과 포함 |
| GET | /api/investment-test | 투자 성향 진단 데이터 | investment-test modal | 질문/타입/결과 표시 |
| GET | /api/mydata | 마이데이터 연동 모달 | mydata modal | 기관 리스트/진행 상태 |
| POST | /api/login | 로그인 처리 (항상 성공) | auth | mock 토큰 반환 |
| POST | /api/logout | 로그아웃 처리 | auth | 항상 성공 |
| POST | /api/villages | 마을 추가 (mock) | neighbors → add | 실제 저장 생략 가능 |
| POST | /api/investment-test/result | 진단 결과 저장 (in-memory) | investment-test modal | 이후 `/api/mypage` 반영 |
| POST | /api/mydata/complete | 마이데이터 연동 완료 (in-memory) | mydata modal | 이후 `/api/mypage` 반영 |

## Typical Frontend Call Flows

### App Boot
- (옵션) 로그인 상태 확인 후 `GET /api/mypage` 또는 `GET /api/main`
- 메인 렌더: `GET /api/main`

### Villages Flow
- 마을 관리 진입: `GET /api/villages`
- 마을 카드 클릭(상세 모달): `GET /api/villages/{id}`
- 데일리로 이동: `GET /api/daily` (필요 시 query 확장)

### Briefing Flow
- 브리핑 진입: `GET /api/briefing`
- 마을 선택 변경: 동일 endpoint 재호출 (또는 query param 확장)

### Neighbors Flow
- 추천 보기: `GET /api/neighbors`
- “마을 추가하기” 액션: `POST /api/villages`

### MyPage Flow
- 마이페이지 진입: `GET /api/mypage`
- 설정 저장: 현재 미구현 (향후 `POST/PUT /api/mypage/settings` 가능)
- 투자성향 진단 완료 반영: `POST /api/investment-test/result` → `GET /api/mypage`
- 마이데이터 연동 완료 반영: `POST /api/mydata/complete` → `GET /api/mypage`

## Conventions & Notes

- 모든 key는 camelCase를 사용합니다.
- returnRate / allocation은 percent point 기준입니다.
- 마을은 `id`, 자산은 `ticker`(또는 id)를 포함합니다.
- 일부 derived(optional) 필드는 프론트에서 계산 가능합니다.
- Mock 한계: fixture 기반이며 `/api/villages/{id}`는 id를 무시하고 동일 fixture를 반환합니다.

## Troubleshooting

- CORS: 데모 목적상 전체 허용(`*`)으로 설정되어 있습니다.
- 404 (FIXTURE_NOT_FOUND): fixture 파일명이 잘못되었거나 누락된 경우.
- Docker/포트 문제: `8000` 포트가 사용 중이면 다른 포트로 매핑하세요.  
  예: `docker run --rm -p 8080:8000 kami-mock`
