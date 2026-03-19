# AlphaBot

주식 전략 백테스팅 + AI 시뮬레이터 — 수익률 / MDD / 샤프지수 분석

## 개요

"이 전략을 썼으면 얼마 벌었을까?"를 과거 데이터로 검증하는 SaaS 플랫폼입니다.
이동평균 교차, RSI 전략 외에 Gemini AI가 자동으로 전략을 생성·최적화합니다.

## 주요 기능

- yfinance로 10년치 주가 데이터 로드
- 이동평균 교차(MA Cross) 전략 백테스팅
- RSI 과매수/과매도 전략 백테스팅
- Gemini AI 추천 전략 자동 생성
- 수익률, MDD(최대낙폭), 샤프지수 계산
- JWT 기반 사용자 인증

## 시작하기

```bash
# 1. 환경변수 설정
cp .env.example .env
# .env 파일에서 GEMINI_API_KEY, SECRET_KEY 입력

# 2. 의존성 설치
pip install -r requirements.txt

# 3. 서버 실행
uvicorn app.main:app --reload --port 8001
```

## API 문서

서버 실행 후 http://localhost:8001/docs 접속

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

## 수익 구조

- 무료: 최근 3년 백테스팅 + 기본 전략 2종
- 프로($19/월): 10년 데이터 + RSI/AI 전략 + 전략 저장 무제한
- 엔터프라이즈($49/월): 팀 공유 + API 접근 + 커스텀 전략 업로드

## 기술 스택

- Backend: FastAPI, SQLAlchemy (async), SQLite
- 데이터: yfinance, pandas, numpy
- AI: Google Gemini API
- 인증: JWT (python-jose)
