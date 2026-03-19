# AlphaBot

주식 전략 백테스팅 + AI 시뮬레이터 — 수익률 / MDD / 샤프지수 / CAGR 분석

## 개요

"이 전략을 썼으면 얼마 벌었을까?"를 과거 데이터로 검증하는 SaaS 플랫폼입니다.
이동평균 교차, RSI 전략 외에 Gemini AI가 자동으로 전략을 생성·최적화합니다.

## 주요 기능

- yfinance로 최대 10년치 주가 데이터 로드
- 이동평균 교차(MA Cross) 전략 백테스팅
- RSI 과매수/과매도 전략 백테스팅
- Gemini AI 추천 전략 자동 생성
- 수익률, MDD(최대낙폭), 샤프지수, CAGR 계산
- JWT 기반 사용자 인증

## 수익 구조

| 플랜 | 백테스트 기간 | 전략 | 가격 |
|------|------------|------|------|
| 무료 | 최근 3년 | 기본 전략 2종 (MA Cross) | 무료 |
| 프로 | 최대 10년 | RSI + AI 추천 전략 + 전략 저장 무제한 | $19/월 |
| 엔터프라이즈 | 최대 10년 | 팀 공유 + API 접근 + 커스텀 전략 업로드 | $49/월 |

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | FastAPI, SQLAlchemy (async), SQLite |
| 데이터 | yfinance, pandas, numpy |
| AI 전략 | Google Gemini API (gemini-1.5-flash) |
| 인증 | JWT (python-jose) |

## 설치 및 실행

### 로컬 실행

```bash
# 1. 저장소 클론
git clone https://github.com/sconoscituo/AlphaBot.git
cd AlphaBot

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일에서 GEMINI_API_KEY, SECRET_KEY 입력

# 5. 서버 실행
uvicorn app.main:app --reload --port 8001
```

### Docker 실행

```bash
cp .env.example .env
# .env 파일 편집

docker-compose up -d
```

서버 실행 후 http://localhost:8001/docs 에서 Swagger UI 확인

## 환경변수

| 변수 | 설명 | 필수 |
|------|------|------|
| `GEMINI_API_KEY` | Google Gemini API 키 | O |
| `SECRET_KEY` | JWT 서명 비밀키 | O |
| `DATABASE_URL` | SQLite DB 경로 | O |
| `DEBUG` | 디버그 모드 (true/false) | 선택 |

## 주요 API

### 인증

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/users/register` | 회원가입 |
| POST | `/api/users/login` | 로그인 (JWT 발급) |
| GET | `/api/users/me` | 내 정보 조회 |

### 백테스팅

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/api/backtest/run` | 백테스트 실행 |
| GET | `/api/backtest/history` | 실행 이력 조회 |
| GET | `/api/backtest/{id}` | 결과 상세 조회 |
| POST | `/api/backtest/ai` | AI 전략 추천 + 백테스트 |

## 지원 전략

| 전략 | `strategy` 값 | 파라미터 | 설명 |
|------|--------------|---------|------|
| 이동평균 교차 | `ma_cross` | `short_window`, `long_window` | 단기 이평이 장기 이평을 상향 돌파 시 매수 |
| RSI | `rsi` | `period`, `oversold`, `overbought` | RSI가 과매도 구간 진입 시 매수, 과매수 시 매도 |
| AI 추천 | `ai` | 없음 (Gemini가 자동 생성) | 티커·기간을 입력하면 AI가 최적 전략 제안 |

## 백테스팅 예시

```json
POST /api/backtest/run
{
  "ticker": "005930.KS",
  "strategy": "ma_cross",
  "start_date": "2020-01-01",
  "end_date": "2023-12-31",
  "params": {"short_window": 20, "long_window": 60}
}
```

## 성과 지표 설명

| 지표 | 설명 |
|------|------|
| **수익률 (Return)** | 백테스트 기간 전체 누적 수익률 (%) |
| **MDD (Max Drawdown)** | 최고점 대비 최대 낙폭 (%). 낮을수록 안정적 |
| **샤프지수 (Sharpe Ratio)** | 위험 대비 초과 수익률. 1.0 이상이면 양호, 2.0 이상이면 우수 |
| **CAGR (연평균 복리 성장률)** | 투자 기간을 연 단위로 환산한 평균 수익률. `(최종자산/초기자산)^(1/연수) - 1` |

## 결과 예시

```json
{
  "ticker": "005930.KS",
  "strategy": "ma_cross",
  "period": "2020-01-01 ~ 2023-12-31",
  "total_return": 48.3,
  "mdd": -22.1,
  "sharpe_ratio": 1.42,
  "cagr": 10.7,
  "trades": 14,
  "win_rate": 57.1
}
```

## 테스트

```bash
pytest tests/ -v --asyncio-mode=auto
```

## 라이선스

MIT
