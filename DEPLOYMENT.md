# Memorization Practice App

## 개요
기억 연습을 위한 Streamlit 기반 웹 애플리케이션입니다. Git 저장소에서 마크다운 파일을 자동으로 로드하고, 사용자가 질문 및 답변 컬럼을 설정하여 커스터마이징할 수 있습니다.

## 기능
- **마크다운 파일 자동 로드**: GitHub 저장소에서 마크다운 파일 자동 동기화
- **테이블 선택 및 학습**: 마크다운 파일의 여러 테이블 중 선택하여 학습
- **컬럼 커스터마이징**: Query/Answer 컬럼을 설정 화면에서 지정 가능
- **설정 저장**: 사용자 설정을 `settings.json`에 자동 저장
- **오답 우선 재학습**: 오답이 많은 문제를 우선적으로 다시 학습

## 로컬 실행

### 환경 설정
```bash
# Python 3.11+ 필요
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 앱 실행
```bash
streamlit run memo_streamlit.py
```

앱은 `http://localhost:8501`에서 접근 가능합니다.

## Docker 배포

### 빌드 및 실행 (docker-compose 권장)

```bash
# 컨테이너 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f memo-game

# 중지
docker-compose down
```

### 또는 수동 Docker 명령어

```bash
# 이미지 빌드
docker build -t memo-game:latest .

# 컨테이너 실행
docker run -d \
  -p 8501:8501 \
  -v memorization_data:/app/memorization \
  -v $(pwd)/settings.json:/app/settings.json \
  --name memo-game \
  memo-game:latest
```

앱은 `http://<server-ip>:8501`에서 접근 가능합니다.

## 설정 파일 (`settings.json`)

```json
{
  "repo_url": "https://github.com/your-repo/memorization.git",
  "query_columns": "Korean,Kor",
  "answer_columns": "English,Eng"
}
```

## 파일 구조
```
.
├── memo_streamlit.py             # 메인 Streamlit 앱
├── memo_lib.py                   # 마크다운 파싱 유틸리티
├── Dockerfile                    # Docker 이미지 정의
├── docker-compose.yml            # Docker Compose 설정
├── requirements.txt              # Python 의존성
├── .dockerignore                 # Docker 빌드 제외 파일
└── settings.json                 # 사용자 설정 (자동 생성)
```

## 배포 체크리스트

- [ ] `settings.json`에 Git 저장소 URL 설정
- [ ] Query/Answer 컬럼명 설정
- [ ] Docker 환경 준비 (Docker >= 20.10, Docker Compose >= 2.0)
- [ ] `docker-compose up -d` 실행
- [ ] 헬스 체크 확인: `curl http://localhost:8501/_stcore/health`
- [ ] 브라우저에서 `http://localhost:8501` 접근 확인

## 트러블슈팅

### 컨테이너가 자주 재시작되는 경우
```bash
docker-compose logs memo-game
```
로그에서 오류 메시지 확인

### 저장소를 못 찾는 경우
- `settings.json`의 `repo_url` 확인
- Git 접근 권한 확인 (public 저장소 권장)

### 포트 충돌
`docker-compose.yml`의 포트 번호 변경:
```yaml
ports:
  - "8502:8501"  # 호스트의 8502 포트로 매핑
```

## 라이선스
MIT
