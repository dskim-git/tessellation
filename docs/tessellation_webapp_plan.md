# 테셀레이션 유닛 디자인 웹앱 개발 계획

## 1. 프로젝트 목적

이 저장소는 삼각형·사각형 기반 테셀레이션 유닛을 활용하여 학생들이 굿즈 전사용 디자인을 만들 수 있도록 돕는 웹앱을 개발하기 위한 작업 공간이다.

이 웹앱의 핵심 목표는 생성형 AI가 테셀레이션의 외곽선을 직접 수정하지 못하게 하고, 수학적으로 정확한 외곽선 프레임 안에 사용자가 준비한 내부 디자인 이미지만 배치하도록 하는 것이다.

최종 사용 흐름은 다음과 같다.

```text
테셀레이션 유형 선택
→ 헤슈 타입별 예시 유닛 확인
→ 유닛별 추천 주제 확인
→ 생성형 AI로 외곽선 없는 내부 디자인 이미지 생성
→ 웹앱에 내부 이미지 업로드
→ 위치·크기·회전 조절
→ 외곽선 프레임과 합성
→ 최종 PNG 다운로드
→ Canva에서 반복 배열 후 굿즈 제작
```

## 2. 현재 참고 코드

이 저장소에는 웹앱 제작을 위한 기존 Python 참고 코드를 보관한다.

```text
scripts/reference/
  square_heesch_reference.py
  square_c4_corner_reference.py
  triangle_heesch_reference.py
```

### 2.1 `square_heesch_reference.py`

사각형 기반 테셀레이션 유닛 생성 참고 코드이다.

활용 대상:

- TTTT
- TGTG
- G1G2G1G2
- TCTC
- CGCG
- CCCC
- C4 관련 기본 구조

주의:

- 이 코드에 들어 있는 C4 구현은 이후 수정본보다 부정확할 수 있다.
- 사각형 테셀레이션 중 C4가 들어가는 부분은 `square_c4_corner_reference.py`의 로직을 우선 사용한다.

### 2.2 `square_c4_corner_reference.py`

사각형 C4 유형 보정을 위한 참고 코드이다.

핵심 내용:

- C4를 정사각형 중심 기준 90도 회전으로 처리하지 않는다.
- 꼭짓점 기준 90도 회전으로 처리한다.
- A, C 꼭짓점을 중심으로 회전하는 구조를 사용한다.

웹앱에서 사각형 C4 계열 유닛을 만들 때는 이 코드를 기준 로직으로 사용한다.

### 2.3 `triangle_heesch_reference.py`

삼각형 기반 테셀레이션 유닛 생성 참고 코드이다.

활용 대상:

- CC6C6
- CC4C4
- CC3C3
- CCC

주의:

- 이 파일 안에는 CGG 관련 코드도 포함되어 있을 수 있지만, 현재 CGG는 원하는 방식으로 안정적으로 구현되지 않은 상태로 판단한다.
- 따라서 웹앱 1차 버전에서는 삼각형 CGG 유형을 목록에서 제외한다.
- 추후 CGG 로직이 검증되면 별도 브랜치나 후속 작업에서 다시 추가한다.

## 3. 웹앱의 핵심 설계 원칙

### 3.1 AI에게 외곽선 생성을 맡기지 않는다

생성형 이미지 AI는 외곽선을 고정된 수학적 제약으로 다루지 못한다. 따라서 AI에게 다음 작업을 맡기지 않는다.

```text
- 테셀레이션 외곽선 생성
- 테셀레이션 유닛 경계 수정
- 반복 배열 규칙 유지
- 최종 테셀레이션 패턴 생성
```

AI에게 맡길 작업은 다음으로 제한한다.

```text
- 내부 캐릭터 디자인 아이디어 생성
- 색상 조합 생성
- 외곽선 없는 장식 이미지 생성
```

### 3.2 외곽선은 웹앱이 프레임으로 제공한다

각 테셀레이션 유닛은 웹앱 내부에서 다음과 같은 프레임 이미지로 제공한다.

```text
외곽선: 검정 또는 사용자가 선택한 색
외곽선 안쪽: 투명
외곽선 바깥쪽: 흰색 또는 투명
```

1차 버전에서는 구현 안정성을 위해 다음 방식을 우선한다.

```text
외곽선 바깥쪽: 흰색
외곽선 안쪽: 투명
```

이 방식은 사용자가 업로드한 내부 디자인 이미지가 외곽선 바깥으로 삐져나와도 프레임 이미지가 위에서 덮어 가려 주는 구조이다.

### 3.3 프레임 이미지는 Python에서 자동 생성한다

기존 Python 유닛 생성 코드에서 외곽선 좌표를 얻은 뒤 다음 산출물을 생성한다.

```text
preview.png
  - 사용자가 유닛을 고를 때 보는 예시 이미지

outline.png
  - 외곽선만 있는 투명 배경 이미지

frame.png
  - 외곽선 바깥쪽은 흰색
  - 외곽선 안쪽은 투명
  - 외곽선은 검정색 또는 지정 색상
```

## 4. 웹앱 MVP 범위

1차 MVP는 다음 기능까지만 구현한다.

```text
1. 유닛 선택 화면
2. 삼각형 / 사각형 필터
3. 헤슈 타입별 예시 유닛 카드
4. 유닛별 추천 주제 표시
5. AI 프롬프트 예시 제공
6. 내부 디자인 이미지 업로드
7. 이미지 위치 조절
8. 이미지 크기 조절
9. 이미지 회전 조절
10. 고정 프레임과 합성 미리보기
11. 최종 PNG 다운로드
```

1차 MVP에서 제외할 기능은 다음과 같다.

```text
- 실시간 AI 이미지 생성
- 자동 테셀레이션 반복 배열
- Canva API 연동
- 학생 계정 저장
- 작품 갤러리
- 굿즈 목업 자동 생성
```

## 5. 추천 기술 스택

장기적으로는 Next.js 기반 웹앱을 추천한다.

```text
Next.js
TypeScript
Tailwind CSS
HTML Canvas API
Vercel
```

이유:

- 이미지 업로드, 드래그, 확대, 회전 UI 구현이 쉽다.
- Canvas API로 최종 PNG export가 가능하다.
- Vercel 배포와 잘 맞는다.
- 기존 MathLab 개발 경험과 연결하기 좋다.

## 6. 화면 구성

### 6.1 유닛 선택 화면

```text
[삼각형] [사각형]

카드 구성:
- 예시 이미지
- 도형 종류
- 헤슈 타입
- 추천 주제 일부
- 선택 버튼
```

### 6.2 유닛 상세 화면

```text
선택한 유닛 이름
헤슈 타입 설명
이 유닛으로 만들기 좋은 주제
AI 프롬프트 예시
내부 디자인 업로드 버튼
```

### 6.3 합성 편집 화면

```text
왼쪽 패널:
- 이미지 업로드
- 확대/축소 슬라이더
- 회전 슬라이더
- 좌우 이동
- 상하 이동
- 초기화
- PNG 다운로드

오른쪽 패널:
- 미리보기 캔버스
- 아래 레이어: 업로드 이미지
- 위 레이어: 테셀레이션 프레임
```

## 7. 기본 데이터 구조 예시

```ts
export type TessellationUnit = {
  id: string;
  baseShape: "triangle" | "square";
  heeschType: string;
  title: string;
  previewImage: string;
  frameImage: string;
  outlineImage: string;
  recommendations: string[];
  promptHint: string;
  enabled: boolean;
};
```

예시:

```ts
export const tessellationUnits: TessellationUnit[] = [
  {
    id: "square-c4-corner-cat-leaf",
    baseShape: "square",
    heeschType: "C4",
    title: "사각형 C4 꼭짓점 회전 유닛",
    previewImage: "/units/square-c4-corner-cat-leaf/preview.png",
    frameImage: "/units/square-c4-corner-cat-leaf/frame.png",
    outlineImage: "/units/square-c4-corner-cat-leaf/outline.png",
    recommendations: ["고양이", "여우 가면", "꽃", "로봇 얼굴"],
    promptHint: "꼭짓점 회전 구조가 있으므로 방향성이 있는 얼굴, 가면, 꽃잎 디자인에 어울립니다.",
    enabled: true
  },
  {
    id: "triangle-cc6c6-leaf",
    baseShape: "triangle",
    heeschType: "CC6C6",
    title: "삼각형 CC6C6 유닛",
    previewImage: "/units/triangle-cc6c6-leaf/preview.png",
    frameImage: "/units/triangle-cc6c6-leaf/frame.png",
    outlineImage: "/units/triangle-cc6c6-leaf/outline.png",
    recommendations: ["나뭇잎", "새", "물방울", "불꽃"],
    promptHint: "삼각형의 방향성이 살아 있으므로 뾰족하거나 흐름이 있는 자연물 디자인에 어울립니다.",
    enabled: true
  }
];
```

## 8. 학생용 AI 프롬프트 예시

```text
테셀레이션 유닛 안에 넣을 내부 디자인 이미지를 만들어 주세요.

조건:
- 테셀레이션 외곽선은 그리지 마세요.
- 검은 윤곽선, 타일 경계선, 퍼즐 외곽선은 만들지 마세요.
- 하나의 독립된 내부 장식 이미지만 만들어 주세요.
- 나중에 웹앱에서 외곽선 프레임 아래에 넣을 예정입니다.
- 굿즈 전사에 어울리도록 단순하고 선명한 색을 사용해 주세요.
- 배경은 흰색 또는 투명 배경으로 해 주세요.
- 너무 작은 글자나 복잡한 배경은 넣지 마세요.

주제:
귀여운 여우 가면 느낌의 디자인
```

## 9. 개발 순서

### 1단계: 참고 코드 정리

- 기존 Python 코드 파일을 `scripts/reference/`에 보관한다.
- 사각형 C4는 수정본을 기준으로 삼는다.
- 삼각형 CGG는 1차 버전에서 제외한다.

### 2단계: Python 에셋 생성 스크립트 제작

새 파일 예시:

```text
scripts/generate_unit_assets.py
```

이 스크립트는 다음을 생성한다.

```text
public/units/{unit_id}/preview.png
public/units/{unit_id}/outline.png
public/units/{unit_id}/frame.png
public/units/{unit_id}/metadata.json
```

### 3단계: Next.js 앱 기본 구조 제작

예상 구조:

```text
src/
  app/
    page.tsx
    units/
      [unitId]/
        page.tsx
    editor/
      [unitId]/
        page.tsx
  components/
    UnitCard.tsx
    UnitEditor.tsx
    ImageTransformControls.tsx
  data/
    tessellationUnits.ts
```

### 4단계: Canvas 편집기 구현

Canvas에서 다음 순서로 그린다.

```text
1. 흰색 배경
2. 사용자가 업로드한 내부 이미지
3. 고정된 frame.png
```

다운로드 시에도 같은 순서로 그린 뒤 PNG로 export한다.

### 5단계: 수업 테스트

확인할 항목:

```text
- 학생이 유닛을 쉽게 선택할 수 있는가
- 추천 주제가 충분히 도움이 되는가
- AI로 외곽선 없는 내부 디자인을 만들 수 있는가
- 업로드한 이미지를 프레임에 맞추기 쉬운가
- 최종 PNG가 Canva에서 잘 사용되는가
```

## 10. 이후 확장 기능

MVP 이후에는 다음 기능을 추가할 수 있다.

```text
- 최종 유닛 자동 반복 배열
- 컵 전사용 긴 직사각형 캔버스 자동 생성
- 에코백 A4 캔버스 자동 생성
- 외곽선 색상 변경
- 빨강/노랑/초록/파랑 색상 버전 자동 생성
- 학생 작품 저장
- 작품 갤러리
- MathLab과 연동
```

## 11. 중요한 구현 메모

- 외곽선 정확도는 AI가 아니라 Python 좌표 생성 로직이 책임진다.
- 사용자가 업로드하는 내부 이미지는 외곽선에 맞춰 잘리는 것이 아니라, 프레임이 위에서 가려 주는 방식으로 구현한다.
- 수학적으로 정확한 테셀레이션 구조를 유지하려면 `frame.png`와 `outline.png`를 절대 AI로 다시 생성하지 않는다.
- 학생에게는 AI 이미지 생성 시 외곽선이나 타일 경계선을 만들지 말라고 명확히 안내한다.
- 삼각형 CGG는 현재 제외한다.
- 사각형 C4는 꼭짓점 기준 C4 수정본을 사용한다.
