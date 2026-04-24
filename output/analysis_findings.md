# 서지분석 결과 도출 — 비디오 분석/검색/요약 분야

**데이터**: Web of Science 논문 1,500편 (1986–2026)  
**분석일**: 2026-04-24

---

## 1. 연구 폭발적 성장 — 딥러닝이 분기점

| 구간 | 연간 논문 수 | 의미 |
|------|------------|------|
| 1997–2012 | 10~40편 | 전통적 컴퓨터 비전 시대 |
| 2013–2019 | 43~76편 | 딥러닝 적용 본격화 |
| 2021–2025 | 101~143편 | 급격한 성장, 매년 최고치 경신 |

2012년(AlexNet), 2017년(Transformer) 이후 논문 수가 계단식으로 증가했고, **2024~2025년에 사상 최고치(134→143편)**를 기록 중이다. 이 분야가 현재 가장 활발한 연구 단계임을 의미한다.

---

## 2. 중국의 압도적 지배 — 연구 생산의 절반

| 순위 | 국가 | 논문 수 | 비율 |
|------|------|--------|------|
| 1 | China | 750 | 50.0% |
| 2 | India | 171 | 11.4% |
| 3 | South Korea | 131 | 8.7% |
| 4 | Turkiye | 106 | 7.1% |
| 5 | England | 92 | 6.1% |

중국이 전체의 절반을 차지하며 2위 인도의 4.4배에 달한다. 미국이 상위 5위 안에 없다는 점은 WoS 기준 중국의 연구 생산량이 이미 서방을 추월했음을 보여준다. **한국이 3위**라는 점은 이 분야에서 국내 연구 경쟁력이 높음을 의미한다.

---

## 3. 인용 구조의 양극화 — 롱테일 분포

- 평균 인용 수: **18.73회**, 중앙값: **6.0회**
- 평균이 중앙값의 3배 이상 → 소수 논문이 인용을 독점하는 전형적인 롱테일 구조
- 전체 인용 합계: **28,097회**
- 코퍼스 H-index: **74** — 이 분야가 상당히 성숙한 연구 집단임을 의미

최고 인용 논문(562회)은 2007년 YouTube 분석 논문으로, 비디오 기술 자체보다 **비디오 플랫폼·콘텐츠 연구가 가장 많이 인용**된다는 점이 특징이다.

### 인용 TOP 5 논문

| 순위 | 제목 (요약) | 연도 | 인용 수 |
|------|------------|------|--------|
| 1 | I Tube, You Tube, Everybody Tubes (YouTube 분석) | 2007 | 562 |
| 2 | Convolutional MKL Based Multimodal Emotion Recognition | 2016 | 450 |
| 3 | A Survey on Visual Content-Based Video Indexing and Retrieval | 2011 | 368 |
| 4 | Affective video content representation and modeling | 2005 | 364 |
| 5 | Aggression and Sexual Behavior in Best-Selling Pornography Videos | 2010 | 364 |

---

## 4. 핵심 기술 키워드 트렌드 — 패러다임 전환 3단계

| 시기 | 지배 키워드 | 의미 |
|------|------------|------|
| 2000~2012 | shot boundary detection, video retrieval | 전통 신호처리 기반 |
| 2013~2019 | deep learning, convolutional neural network, object detection | CNN 중심 딥러닝 시대 |
| 2019~현재 | attention, transformer, action recognition, video summarization | Transformer 기반으로 전환 |

"transformer"와 "attention" 키워드가 2019년 이후 급등하며, **비디오 분야도 NLP와 동일한 패러다임 전환**이 진행 중임을 확인할 수 있다.

---

## 5. 학술지 집중도 — IEEE 계열이 주류

| 순위 | 저널 | 논문 수 |
|------|------|--------|
| 1 | Multimedia Tools and Applications | 40 |
| 2 | IEEE Transactions on Multimedia | 34 |
| 3 | IEEE Transactions on Circuits and Systems for Video Technology | 27 |
| 4 | Digital Health | 16 |
| 5 | IEEE Access | 15 |

상위 3개 저널이 모두 IEEE/멀티미디어 계열로, **이 분야의 핵심 게재 경로가 명확**하다. 논문 투고 전략 수립 시 이 저널들을 우선 타겟으로 삼는 것이 유리하다.

---

## 6. 생산적 저자 vs 영향력 있는 저자의 분리

| 기준 | 1위 저자 | 수치 |
|------|---------|------|
| 논문 수 | Schoeffmann, Klaus | 13편 |
| H-index | Zhang, HJ | H=10 |
| 총 인용 수 | Zhang, HJ | 1,321회 |

Zhang HJ(장홍장)는 1990~2000년대 비디오 검색 선구자로, 논문 수는 12편이지만 인용 집중도가 압도적이다. 반면 Schoeffmann은 최근까지 꾸준히 논문을 발표하며 논문 수 1위를 유지하고 있다. **양(논문 수)과 질(영향력)의 경향이 서로 다른 저자군**이 존재한다.

### WoS 데이터셋 내 H-index 상위 저자

| 저자 | 논문 수 | H-index | 총 인용 수 |
|------|--------|---------|----------|
| Zhang, HJ | 12 | 10 | 1,321 |
| Schoeffmann, Klaus | 13 | 9 | 264 |
| Hanjalic, A | 5 | 5 | 1,007 |
| Yeo, BL | 6 | 5 | 379 |
| Mei, Tao | 7 | 6 | 151 |

---

## 7. 주제 카테고리 — AI + 시스템 + 전기전자의 융합

| 순위 | WoS 카테고리 | 논문 수 |
|------|------------|--------|
| 1 | Computer Science, Artificial Intelligence | 315 |
| 2 | Computer Science, Information Systems | 259 |
| 3 | Engineering, Electrical & Electronic | 250 |
| 4 | Telecommunications | 175 |
| 5 | Computer Science, Theory & Methods | 172 |

AI, 정보시스템, 전기전자 공학이 함께 분류되는 **전형적인 융합 연구 분야**임을 확인할 수 있다.

---

## 종합 결론

> 비디오 분석/검색/요약 분야는 **2021년 이후 폭발적으로 성장** 중이며, **Transformer 기반 기술로 패러다임이 전환**됐다. 연구 생산은 **중국이 50%를 독점**하는 가운데 한국이 3위로 상위권에 위치해 있으며, **IEEE 계열 3개 저널**이 핵심 게재 통로로 기능한다. 인용 구조는 롱테일로 양극화되어 있고, 코퍼스 H-index 74는 이 분야가 이미 성숙한 연구 생태계를 갖췄음을 보여준다.
