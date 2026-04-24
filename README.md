# WoS 서지분석 — 비디오 분석/검색/요약 분야

## 프로젝트 요약

Web of Science(WoS)에서 수집한 논문 1,500편을 대상으로 비디오 분석·검색·요약 분야의 연구 동향을 정량적으로 분석하는 서지분석(Bibliometrics) 프로그램입니다.

| 항목 | 내용 |
|------|------|
| 분석 대상 | Video Analysis / Retrieval / Summarization 관련 WoS 논문 |
| 데이터 | `savedrecs.txt`, `savedrecs-2.txt`, `savedrecs-3.txt` (각 500건, 총 1,500편) |
| 출력 | 차트 18종 (PNG) + 통계 요약 (`summary_stats.json`) |
| 실행 환경 | **Docker 컨테이너** (docker compose로 관리) |
| 필요 API 키 | 없음 (모든 데이터는 로컬 WoS 텍스트 파일에서 읽음) |

---

## 분석 결과 요약

> 전체 도출 결과: [`output/analysis_findings.md`](output/analysis_findings.md)

### 핵심 수치 (N=1,500편, 1986–2026)

| 지표 | 값 |
|------|----|
| 총 인용 수 | 28,097회 |
| 평균 인용 수 | 18.73회 (중앙값 6.0 — 롱테일 분포) |
| 코퍼스 H-index | 74 |
| 최다 논문 국가 | 중국 750편 (50%) |
| 최고 인용 논문 | I Tube, You Tube, Everybody Tubes (2007, 562회) |
| 핵심 게재지 | Multimedia Tools and Applications, IEEE Trans. Multimedia, IEEE TCSVT |

### 주요 발견

**1. 폭발적 성장 중** — 2024년 134편, 2025년 143편으로 역대 최고치 경신. 2017년 Transformer 등장 이후 계단식 급증.

**2. 중국 독주** — 전체 논문의 50%를 차지. 한국은 131편으로 3위. 미국은 상위 5위권 밖.

**3. 패러다임 전환 3단계** — 전통 신호처리(~2012) → CNN 딥러닝(2013~2019) → Transformer/Attention(2019~현재). `attention`, `transformer` 키워드가 2019년 이후 급등.

**4. 인용 양극화** — 평균(18.73)이 중앙값(6.0)의 3배. 소수 논문이 인용을 집중 독점하는 전형적인 롱테일 구조.

**5. IEEE 계열 3개 저널이 핵심 게재 통로** — 상위 3개 저널이 모두 IEEE/멀티미디어 계열. 논문 투고 전략의 기준점.

---

## 분석 항목 (차트 18종)

| 번호 | 파일명 | 내용 |
|------|--------|------|
| 01 | `01_annual_trend.png` | 연도별 출판 건수 + 누적 인용 추세 |
| 02 | `02_document_types.png` | 문헌 유형 분포 (파이차트) |
| 03 | `03_top_journals.png` | 상위 20개 게재지/학술대회 |
| 04 | `04_top_authors.png` | 논문 수 기준 상위 20명 저자 |
| 05 | `05_top_countries.png` | 국가별 논문 수 (상위 20개국) |
| 06 | `06_top_institutions.png` | 기관별 논문 수 (상위 20개 기관) |
| 07 | `07_top_keywords.png` | 저자 키워드 빈도 (상위 30개) |
| 08 | `08_wordcloud.png` | 키워드 워드클라우드 |
| 09 | `09_most_cited.png` | 인용 수 TOP 15 논문 |
| 10 | `10_citation_distribution.png` | 인용 수 분포 (로그 스케일) + 연대별 박스플롯 |
| 11 | `11_wos_categories.png` | WoS 주제 카테고리 분포 (상위 15개) |
| 12 | `12_keyword_network.png` | 키워드 공출현 네트워크 (상위 40개) |
| 13 | `13_country_collaboration.png` | 국가 간 국제 협력 네트워크 |
| 14 | `14_author_hindex.png` | 상위 저자 H-index + 총 인용 수 |
| 15 | `15_language.png` | 언어 분포 |
| 16 | `16_avg_references.png` | 연도별 평균 참고문헌 수 추세 |
| 17 | `17_keyword_trend.png` | 주요 개념 등장 빈도 추세 (2000–2024) |
| 18 | `18_collaboration_heatmap.png` | 상위 15개국 협력 히트맵 |
| 별도 | `annual_trend_detail.png` | 상세 연도별 추이 (문헌유형 누적 + 히트맵) |

---

## 실행

### Docker 실행 (권장)

분석 결과가 로컬 `output/` 폴더에 저장됩니다.

```bash
# 이미지 빌드
docker build -t wos-bibliometrics .

# 전체 분석 실행 (차트 18종 + summary_stats.json 생성)
docker run --rm -v $(pwd)/output:/app/output wos-bibliometrics

# 연도별 상세 추이 차트만 별도 실행
docker run --rm -v $(pwd)/output:/app/output wos-bibliometrics \
  python plot_annual_trend.py
```

실행 완료 후 `output/` 폴더에 결과 파일이 생성됩니다.

### 로컬 실행

```bash
pip install -r requirements.txt

# 전체 분석
python bibliometrics_analysis.py

# 연도별 상세 추이 차트
python plot_annual_trend.py
```

---

## 데이터 준비 (WoS 텍스트 파일)

Web of Science에서 검색 결과를 내보낼 때 아래 설정으로 저장합니다.

1. WoS 검색 → 결과 저장 → **기타 파일 형식**
2. 레코드 내용: **전체 레코드 + 인용된 참고문헌**
3. 파일 형식: **일반 텍스트 (UTF-8)**
4. 파일명을 `savedrecs.txt`, `savedrecs-2.txt`, `savedrecs-3.txt`로 저장 (500건씩 분할)

---

## 프로젝트 구조

```
서지분석/
├── bibliometrics_analysis.py  # 메인 분석 스크립트 (차트 18종 + JSON)
├── plot_annual_trend.py       # 연도별 상세 추이 차트 (별도 실행)
├── savedrecs.txt              # WoS 데이터 1/3 (500건)
├── savedrecs-2.txt            # WoS 데이터 2/3 (500건)
├── savedrecs-3.txt            # WoS 데이터 3/3 (500건)
├── output/                    # 분석 결과 (차트 PNG + summary_stats.json)
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

---

## 필요 패키지

```
numpy, pandas, matplotlib, seaborn, networkx, wordcloud
```

---

## 업데이트 내역

### 2026-04-24
- **분석 결과 도출 문서 추가**: `output/analysis_findings.md` — 7개 항목의 정량적 결론 정리
- **README 분석 결과 요약 섹션 추가**: 핵심 수치 및 5대 주요 발견 요약
- **최초 릴리즈**: WoS 서지분석 프로그램 Docker 컨테이너 환경으로 배포
- **경로 수정**: 절대경로 → 상대경로 (`os.path.dirname(__file__)`) 변환으로 Docker 호환
- **Docker 실행 환경 구성**: Dockerfile, .dockerignore 추가, output 볼륨 마운트 지원
