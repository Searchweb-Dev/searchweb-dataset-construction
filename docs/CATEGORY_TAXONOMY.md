# Category & Taxonomy Reference

## Overview

AI 사이트를 체계적으로 분류하기 위한 3계층 카테고리 분류 시스템입니다.

---

## Level 1: Modality (모달리티 - 기본 카테고리)

AI가 처리하는 데이터 형식에 따른 분류입니다.

| 카테고리 | 설명 | 예시 |
|---------|------|------|
| **text** | 텍스트 기반 AI | ChatGPT, Claude, Gemini |
| **image** | 이미지 생성/분석 | DALL-E, Midjourney, Stable Diffusion |
| **video** | 영상 생성/편집 | Runway ML, Synthesia |
| **audio** | 음성 생성/인식 | ElevenLabs, AssemblyAI |
| **code** | 코드 생성/분석 | GitHub Copilot, Tabnine |
| **multimodal** | 다중 모달 처리 | GPT-4V, Claude 3 |
| **data** | 데이터 분석/ML | Databricks, Tableau |
| **business** | 비즈니스 솔루션 | HubSpot, Salesforce Einstein |

---

## Level 2: Task Type (작업 유형 - 세부 기능)

각 모달리티 내에서 수행하는 작업 유형입니다.

### Text (텍스트)

```
├─ text-generation      # 텍스트 생성
│  ├─ content-creation
│  ├─ copywriting
│  ├─ email-generation
│  └─ creative-writing
├─ text-analysis        # 텍스트 분석
│  ├─ sentiment-analysis
│  ├─ summarization
│  ├─ translation
│  ├─ grammar-check
│  └─ plagiarism-detection
├─ conversational       # 대화형
│  ├─ chatbot
│  ├─ virtual-assistant
│  ├─ customer-support
│  └─ language-learning
└─ search-retrieval     # 검색/조회
   ├─ semantic-search
   ├─ question-answering
   ├─ knowledge-base
   └─ research-assistant
```

### Image (이미지)

```
├─ image-generation    # 이미지 생성
│  ├─ text-to-image
│  ├─ image-editing
│  ├─ background-removal
│  ├─ inpainting
│  └─ upscaling
├─ image-analysis       # 이미지 분석
│  ├─ object-detection
│  ├─ face-recognition
│  ├─ ocr
│  ├─ image-classification
│  └─ visual-search
└─ avatar-animation     # 아바타/애니메이션
   ├─ avatar-generation
   ├─ talking-head
   ├─ motion-capture
   └─ digital-human
```

### Video (영상)

```
├─ video-generation    # 영상 생성
│  ├─ text-to-video
│  ├─ image-to-video
│  ├─ video-synthesis
│  └─ animation
├─ video-editing        # 영상 편집
│  ├─ auto-editing
│  ├─ background-removal
│  ├─ object-removal
│  ├─ subtitle-generation
│  └─ color-grading
├─ video-analysis       # 영상 분석
│  ├─ video-classification
│  ├─ scene-detection
│  ├─ action-recognition
│  └─ video-summarization
└─ talking-video        # 토킹 영상
   ├─ lip-sync
   ├─ voice-cloning
   └─ digital-avatar
```

### Audio (음성)

```
├─ speech-generation   # 음성 생성
│  ├─ text-to-speech
│  ├─ voice-cloning
│  ├─ music-generation
│  ├─ sound-effect-generation
│  └─ podcast-generation
├─ audio-analysis       # 음성 분석
│  ├─ speech-recognition
│  ├─ speaker-identification
│  ├─ emotion-detection
│  ├─ music-classification
│  └─ audio-enhancement
└─ audio-editing        # 음성 편집
   ├─ noise-reduction
   ├─ voice-change
   ├─ background-removal
   └─ mixing
```

### Code (코드)

```
├─ code-generation     # 코드 생성
│  ├─ code-completion
│  ├─ function-generation
│  ├─ class-generation
│  ├─ test-generation
│  ├─ documentation
│  └─ sql-generation
├─ code-analysis        # 코드 분석
│  ├─ bug-detection
│  ├─ code-review
│  ├─ performance-analysis
│  ├─ security-analysis
│  └─ code-search
├─ code-refactoring     # 코드 리팩토링
│  ├─ code-transformation
│  ├─ style-enforcement
│  └─ optimization
└─ dev-tools            # 개발 도구
   ├─ debugging
   ├─ deployment
   ├─ monitoring
   └─ api-generation
```

### Multimodal (다중모달)

```
├─ foundation-models    # 기초 모델
│  ├─ gpt-like
│  ├─ vision-language
│  └─ audio-visual
├─ search-retrieval     # 멀티모달 검색
│  ├─ multimodal-search
│  ├─ visual-qa
│  └─ scene-understanding
└─ content-understanding # 콘텐츠 이해
   ├─ document-understanding
   ├─ page-analysis
   └─ pdf-processing
```

### Data & Analytics (데이터)

```
├─ data-generation     # 데이터 생성
│  ├─ synthetic-data
│  ├─ data-augmentation
│  └─ test-data
├─ data-analysis        # 데이터 분석
│  ├─ visualization
│  ├─ forecasting
│  ├─ anomaly-detection
│  ├─ clustering
│  └─ regression-analysis
├─ business-intelligence # BI
│  ├─ dashboard
│  ├─ report-generation
│  └─ metric-tracking
└─ ml-operations        # MLOps
   ├─ model-training
   ├─ hyperparameter-tuning
   ├─ feature-engineering
   └─ model-monitoring
```

### Business (비즈니스)

```
├─ marketing            # 마케팅
│  ├─ campaign-generation
│  ├─ personalization
│  ├─ social-media
│  └─ market-analysis
├─ sales                # 영업
│  ├─ lead-scoring
│  ├─ sales-prediction
│  ├─ proposal-generation
│  └─ pricing-optimization
├─ human-resources      # HR
│  ├─ recruitment
│  ├─ resume-analysis
│  ├─ interview-analysis
│  └─ employee-engagement
├─ finance              # 금융
│  ├─ fraud-detection
│  ├─ risk-analysis
│  ├─ portfolio-optimization
│  └─ financial-forecasting
└─ legal-compliance     # 법무/컴플라이언스
   ├─ contract-analysis
   ├─ document-review
   ├─ compliance-monitoring
   └─ due-diligence
```

---

## Level 3: Detail (세부 기능 - 선택사항)

특정 작업 유형 내에서의 구체적인 기능입니다.

### 예시

**Text > text-generation > content-creation**
- blog-writing: 블로그 글쓰기
- article-writing: 기사 작성
- newsletter: 뉴스레터 작성

**Image > image-generation > text-to-image**
- realistic-image: 사실적 이미지
- artistic-image: 예술적 이미지
- stylized-image: 스타일화된 이미지
- 3d-model: 3D 모델

**Audio > speech-generation > text-to-speech**
- natural-tts: 자연스러운 음성
- voice-cloning: 목소리 복제
- multi-language: 다국어

**Code > code-generation > code-completion**
- function-completion: 함수 자동완성
- class-completion: 클래스 자동완성
- algorithm-completion: 알고리즘 자동완성

---

## Tags (추가 특성 - 선택사항)

서비스의 추가 특성을 태그로 분류합니다.

### 언어 & 접근성
- `multilingual`: 다국어 지원
- `korean`: 한국어 지원
- `accessible`: 접근성 고려

### API & 통합
- `api-available`: API 제공
- `webhook`: Webhook 지원
- `integrations`: 써드파티 연동 지원
- `plugin`: 플러그인 제공

### 가격 & 라이선스
- `free-tier`: 무료 플랜 제공
- `open-source`: 오픈소스
- `commercial`: 상용 라이선스
- `paid`: 유료

### 기술 & 모델
- `custom-model`: 커스텀 모델 지원
- `fine-tuning`: 파인튜닝 가능
- `local-deployment`: 로컬 배포 가능

### 성능 & 품질
- `real-time`: 실시간 처리
- `batch-processing`: 배치 처리
- `high-quality`: 고품질
- `gpu-accelerated`: GPU 가속

---

## 사용 예시

### ChatGPT
```json
{
  "level_1": "text",
  "level_2": "conversational",
  "level_3": null,
  "tags": ["api-available", "free-tier", "multilingual"]
}
```

### Midjourney
```json
{
  "level_1": "image",
  "level_2": "image-generation",
  "level_3": "text-to-image",
  "tags": ["discord-integration", "paid", "high-quality"]
}
```

### GitHub Copilot
```json
{
  "level_1": "code",
  "level_2": "code-generation",
  "level_3": "code-completion",
  "tags": ["ide-plugin", "subscription", "multilingual"]
}
```

### ElevenLabs
```json
{
  "level_1": "audio",
  "level_2": "speech-generation",
  "level_3": "text-to-speech",
  "tags": ["voice-cloning", "api-available", "multilingual", "free-tier"]
}
```

---

## 선택 가이드

### Claude 분석 시 Level 3 필수 여부

- **필수**: 같은 Level 2 내 구분이 명확할 때
  - text-to-image vs 다른 image-generation
  - code-completion vs code-generation

- **선택**: Level 2가 이미 충분히 구체적일 때
  - conversational (이미 chatbot vs virtual-assistant 구분 안 필요)
  - visual-qa (Level 2가 구체적)

### Tags 선택 가이드

- **최소 1개 이상** 추가하기
- 서비스의 가장 특징적인 기능 3~5개 선택
- 중복 피하기 (multilingual은 multilingual-support로 통일)
