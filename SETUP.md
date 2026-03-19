# AlphaBot - AI 기반 주식/투자 분석 봇

## 필요한 API 키 및 환경변수

| 환경변수 | 설명 | 발급 URL |
|---|---|---|
| `GEMINI_API_KEY` | Google Gemini AI API 키 | https://aistudio.google.com/app/apikey |
| `SECRET_KEY` | JWT 토큰 서명용 시크릿 키 (임의 문자열) | - |
| `DATABASE_URL` | 데이터베이스 연결 URL (기본: SQLite) | - |
| `DEBUG` | 디버그 모드 활성화 여부 (`True` / `False`) | - |

## GitHub Secrets 설정

GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret

| Secret 이름 | 값 |
|---|---|
| `GEMINI_API_KEY` | Gemini API 키 |
| `SECRET_KEY` | JWT 시크릿 키 (랜덤 32자 이상 문자열) |

## 로컬 개발 환경 설정

```bash
# 1. 저장소 클론
git clone https://github.com/sconoscituo/AlphaBot.git
cd AlphaBot

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경변수 설정
cp .env.example .env
# .env 파일을 열어 아래 항목 입력:
# GEMINI_API_KEY=your_gemini_api_key
# SECRET_KEY=your_random_secret_key

# 5. 서버 실행
uvicorn app.main:app --reload
```

서버 기동 후 http://localhost:8000/docs 에서 API 문서를 확인할 수 있습니다.

## Docker로 실행

```bash
# 이미지 빌드 및 컨테이너 실행
docker-compose up --build
```

## 주요 기능 사용법

### 주식 데이터 조회
- `yfinance` 라이브러리를 통해 실시간 및 과거 주가 데이터를 수집합니다.
- 티커 심볼(예: `AAPL`, `005930.KS`)을 입력해 분석을 시작합니다.

### AI 투자 분석
- Gemini AI가 주가 데이터를 분석하여 투자 인사이트를 제공합니다.
- 무료 사용자: 최대 3년 백테스팅
- 프리미엄 사용자: 최대 10년 백테스팅

### 자동 스케줄링
- `APScheduler`를 사용해 주기적으로 시장 데이터를 수집하고 분석합니다.
- 스케줄 간격은 관리자 설정에서 변경 가능합니다.

### 인증
- JWT 기반 인증 사용 (토큰 유효기간: 24시간)
- `/api/auth/register` - 회원가입
- `/api/auth/login` - 로그인 및 토큰 발급

## 프로젝트 구조

```
AlphaBot/
├── app/
│   ├── config.py       # 환경변수 설정
│   ├── database.py     # DB 연결 관리
│   ├── main.py         # FastAPI 앱 진입점
│   ├── models/         # SQLAlchemy 모델
│   ├── routers/        # API 라우터
│   ├── schemas/        # Pydantic 스키마
│   ├── services/       # 비즈니스 로직
│   └── utils/          # 유틸리티 함수
├── tests/              # 테스트 코드
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```
