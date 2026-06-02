# 2일차 - Git 브랜치 전략 (Git Flow & GitHub Flow)

> 프로젝트 코드 버전 관리를 위해 Git/GitHub를 사용할 때, 여러 명의 개발자가 서로 영향을 주지 않고 동시에 작업하기 위한 규칙이 **브랜치 전략**이다. 이 문서에서는 대표적인 두 가지 전략인 **Git Flow**와 **GitHub Flow**를 정리한다.
>
> 📚 참고자료
> - [주니어 개발자의 현업에서 배운 Git Flow](https://velog.io/@myoungji-kim/git-flow)
> - [Git Branch 전략 비교 - DevOcean SK](https://devocean.sk.com/blog/techBoardDetail.do?ID=165571&boardType=techBlog)
> - [사례로 이해하는 GitHub Flow - HEROPY](https://www.heropy.dev/p/6hdJi6)

---

## 1. 브랜치 전략은 왜 필요한가?

여러 사람이 하나의 저장소에서 동시에 작업하면, 누가 어떤 코드를 언제 어디에 합치는지 규칙이 없을 경우 충돌과 혼란이 발생한다. 브랜치 전략은 다음을 가능하게 한다.

- **동시 작업**: 개발자들이 서로의 작업에 영향을 주지 않고 병렬로 개발
- **작업 추적**: 브랜치를 특정 기능 / 이슈 단위로 운영하여 변경 이력을 추적
- **버전 관리**: 배포 가능한 코드와 개발 중인 코드를 분리해 관리
- **배포 안정성**: 릴리스 준비·버그 수정 등 단계를 명확히 나누어 안정적으로 배포

대표 전략으로 **Git Flow**(다양한 브랜치로 세분화)와 **GitHub Flow**(단순한 2-브랜치 운영)가 있다.

---

## 2. Git Flow

### 2.1 개요

Vincent Driessen이 2010년 *A successful Git branching model* 글에서 제안한 모델이다.
제품 출시 버전, 개발 버전, 기능, 출시 준비, 버그 수정 등 **역할이 다른 여러 종류의 브랜치**를 두고 관리한다.
명확한 릴리스 주기를 가진 큰 프로젝트나 여러 버전을 동시에 유지보수해야 하는 환경에 적합하다.

### 2.2 브랜치 종류와 역할

| 구분 | 브랜치 | 역할 |
|------|--------|------|
| 항상 유지 | **main** | 실제 운영(배포)에 반영되는 안정된 코드 |
| 항상 유지 | **develop** | 개발 중인 코드를 통합하는 브랜치 |
| 임시 생성 | **feature/** | 새로운 기능 개발. `develop`에서 생성, 완료 후 `develop`으로 병합 |
| 임시 생성 | **release/** | 배포 준비. QA·버그 수정 후 `main`과 `develop`에 병합 |
| 임시 생성 | **hotfix/** | 긴급 버그 수정. `main`에서 생성, 수정 후 `main`·`develop`에 병합 |

> 💡 실무에서는 `feature` 안에서 부모/자식 브랜치(`feature/10` → `feature/10-1`)로 나누어
> 코드 리뷰 단위를 관리하기도 한다.

### 2.3 흐름 다이어그램

```
main ───────────────────●──────────────●─────  (배포)
        \              / \             /
release  \            ●   \           ●         (출시 준비/QA)
          \          /     \         /
develop ───●────●───●───────●───●───●──────────  (개발 통합)
            \  /         \  /
feature      ●            ●                     (기능 개발)
```

### 2.4 기본 흐름

1. `develop`에서 `feature/기능명` 브랜치를 생성한다.
2. `feature` 브랜치에서 기능을 개발하고, PR로 코드 리뷰 후 `develop`에 병합한다.
3. 배포 시점에 `develop`에서 `release` 브랜치를 생성해 QA와 버그 수정을 진행한다.
4. QA가 끝나면 `release`를 `main`에 병합하여 배포하고, `develop`에도 동기화한다.
5. 긴급 버그 발생 시 `main`에서 `hotfix` 브랜치를 만들어 수정 후 `main`과 `develop`에 병합한다.

> ⚠️ **배포 후에는 반드시 브랜치 최신화!**
> `main` 배포 후 `develop`이 `main`의 커밋을 모두 갖도록 동기화하지 않으면
> 나중에 충돌이 발생하고 해결이 어려워진다.

### 2.5 장단점

| 장점 | 단점 |
|------|------|
| 체계적인 버전 관리, 대규모 팀에 적합 | 브랜치가 많아 복잡함 |
| 명확한 릴리스 주기 관리 | 빠른 배포 환경에는 무겁고 보수적 |
| 여러 버전 동시 유지보수 가능 | 학습 곡선이 있음 |

---

## 3. GitHub Flow

### 3.1 개요

Git Flow가 GitHub에서 쓰기엔 복잡하다는 문제의식에서 나온 **단순한 전략**이다.
`main` 브랜치 하나와 기능별 `feature` 브랜치만으로 운영한다.
**CI/CD가 자동화되어 수시로 배포하는 프로젝트**에 적합하다.

**핵심 원칙: `main` 브랜치는 항상 배포 가능한 상태여야 한다.**

### 3.2 흐름 다이어그램

```
main ──●─────────────────●──────────────●─────  (항상 배포 가능)
        \               / \            /
feature  ●──●──●──(PR)─●   ●──(PR)────●         (기능/버그 브랜치)
```

### 3.3 기본 흐름

1. `main`에서 새 브랜치를 만든다. 이름은 어떤 작업인지 명확히 알 수 있게 짓는다.
2. 해당 브랜치에서 작업하고 의미 있는 단위로 커밋한다.
3. GitHub에서 Pull Request(PR)를 생성해 리뷰를 요청한다.
4. 리뷰어의 피드백을 반영하고, CI에서 자동 테스트를 수행한다.
5. 리뷰가 승인되면 PR을 `main`에 병합한다.
6. 병합되면 자동으로 배포되고, 사용한 브랜치는 삭제한다.

### 3.4 PR 병합 옵션 3가지

| 옵션 | 설명 | 사용 시점 |
|------|------|----------|
| **Create a merge commit** | 모든 커밋 + 병합 커밋 생성 | 병합 이력을 명확히 남기고 싶을 때 |
| **Squash and merge** | 모든 커밋을 하나로 압축 후 병합 | 자잘한 커밋을 정리하고 싶을 때 |
| **Rebase and merge** | 커밋을 직렬로 추가 (병합 커밋 없음) | 깔끔한 선형 히스토리를 원할 때 |

### 3.5 이슈 연동

커밋 메시지에 `close #이슈번호`를 추가하면 PR Merge 시 이슈가 자동으로 닫힌다.

```bash
git commit -m "✨ feat: 폐렴 판독 API 추가. close #1"
```

### 3.6 장단점

| 장점 | 단점 |
|------|------|
| 단순하고 이해하기 쉬움 | 명시적 릴리스 관리 어려움 |
| 빠른 배포, CI/CD와 궁합이 좋음 | 여러 버전 동시 지원 어려움 |
| 소규모 팀에 최적 | |

---

## 4. Git Flow vs GitHub Flow 비교

| 항목 | Git Flow | GitHub Flow |
|------|----------|-------------|
| 브랜치 종류 | main, develop, feature, release, hotfix | main, feature |
| 복잡도 | 높음 | 낮음 |
| 배포 주기 | 정해진 릴리스 주기 | 수시 배포 (CI/CD) |
| 적합한 환경 | 버전·릴리스 관리가 중요한 대규모 프로젝트 | 빠른 배포가 필요한 소규모/웹 서비스 |
| 여러 버전 동시 관리 | 가능 | 어려움 |
| 실무 사례 | 배달의민족 (2017년부터 Git Flow 전환) | 소규모 스타트업, 오픈소스 |

> 정리: **명확한 버전·릴리스 관리가 중요하면 Git Flow**,
> **빠르고 잦은 배포가 중요하고 CI/CD가 갖춰져 있으면 GitHub Flow**를 선택한다.

---

## 5. 충돌(Conflict) 해결 방법

작업 중 같은 파일의 같은 줄을 서로 다르게 수정하면 충돌이 발생한다.

### 충돌 발생 시 코드 예시

```bash
<<<<<<< HEAD         ← 현재 브랜치 변경사항
print("hello")
=======
print("hi")          ← 내 feature 브랜치 변경사항
>>>>>>> feature/login
```

### 해결 순서

```bash
# 1. 충돌 파일 열어서 원하는 코드만 남기고 마커 제거
# 2. 수정 완료 후 스테이징
git add 수정한파일

# 3. 계속 진행
git rebase --continue   # rebase 중이었다면
git merge --continue    # merge 중이었다면

# 취소하고 싶을 때
git rebase --abort
git merge --abort
```

> 💡 **핵심**: 혼자 해결하기 어려우면 해당 코드를 작성한 팀원과 소통하여 함께 해결하자!

---

## 6. 자주 쓰는 Git 명령어 정리

```bash
# 브랜치
git switch main                  # main 브랜치로 이동
git switch -c feature/기능명      # 새 브랜치 생성 + 이동
git branch                       # 브랜치 목록 확인
git branch -d feature/기능명      # 브랜치 삭제

# 최신화
git fetch                        # 원격 변경사항 가져오기 (병합 X)
git pull origin main             # 원격 main을 가져와 병합
git pull origin main --rebase    # rebase 방식으로 최신화

# 커밋 & 푸시
git add .                        # 변경 파일 스테이징
git status                       # 현재 상태 확인
git commit -m "[#이슈] 메시지"    # 커밋
git push origin feature/기능명    # 원격에 push
git push -f origin feature/기능명 # 리베이스 후 강제 push (개인 브랜치만!)

# 이력 확인
git log --oneline --graph        # 커밋 이력 그래프로 확인
```

---

## 7. 우리 팀 하이브리드 브랜치 전략

### 개요

Git Flow의 체계적인 버전 관리와 GitHub Flow의 단순함을 결합한 **하이브리드 전략**을 사용한다.
`main → develop → 부모 feature → 자식 feature` 구조로 운영하여
팀원별 작업을 명확히 분리하면서도 기능 단위로 안정적으로 통합한다.

### 브랜치 구조

```
main
│   배포 가능한 안정 버전 (직접 push 금지)
│
develop
│   개발 통합 브랜치
│
└── feature/기능명 (부모 브랜치)
        │   하나의 기능 단위를 묶는 브랜치
        │
        ├── feature/기능명-홍길동 (자식 브랜치)
        ├── feature/기능명-김철수 (자식 브랜치)
        └── feature/기능명-이영희 (자식 브랜치)
```

### 전체 흐름

```
develop
    ↓  분기
feature/기능명 (부모) ← 기능 단위로 묶는 브랜치
    ↓  분기
feature/기능명-팀원명 (자식) ← 팀원이 자유롭게 개발
    ↓  PR & Merge (자식 → 부모)
feature/기능명 (부모) ← 통합 테스트
    ↓  PR & Merge (부모 → develop)
develop ← 개발 통합
    ↓  PR & Merge (develop → main)
main ← 배포
```

### 실전 명령어

```bash
# ======== 팀장: 부모 브랜치 생성 ========
git switch develop
git pull origin develop
git switch -c feature/user-api
git push origin feature/user-api

# ======== 팀원: 자식 브랜치 생성 & 개발 ========
git switch feature/user-api
git pull origin feature/user-api
git switch -c feature/user-api-홍길동

# 자유롭게 개발 후
git add .
git commit -m "✨ feat: 회원 조회 API 구현"
git push origin feature/user-api-홍길동

# GitHub에서 PR 생성
# base: feature/user-api (부모)
# compare: feature/user-api-홍길동 (자식)

# ======== 부모 → develop Merge ========
# 자식들이 모두 부모로 Merge된 후
# GitHub에서 PR 생성
# base: develop
# compare: feature/user-api (부모)
```

### 브랜치 네이밍 규칙

```
# 부모 브랜치
feature/기능명
예) feature/user-api, feature/xray-predict

# 자식 브랜치
feature/기능명-팀원명
예) feature/user-api-홍길동, feature/xray-predict-김철수
```

### 커밋 메시지 컨벤션

```
✨ feat:      새로운 기능 추가
🐛 fix:       버그 수정
📝 docs:      문서 수정
♻️ refactor:  코드 리팩토링
✅ test:      테스트 코드
🚑 hotfix:    긴급 수정
💡 chore:     기타 수정 (주석, 오타 등)
```

```bash
# 이슈번호 포함 예시
git commit -m "[#10] ✨ feat: 폐렴 판독 API 추가"
```

### PR 흐름 한눈에 보기

```
자식 브랜치 → 부모 브랜치  (PR #1: 팀원 코드 리뷰)
                  ↓
부모 브랜치 → develop      (PR #2: 기능 통합 리뷰)
                  ↓
develop     → main         (PR #3: 최종 배포 리뷰)
```

### 장단점

| 장점 | 단점 |
|------|------|
| 팀원별 작업이 명확히 분리됨 | 브랜치 depth가 깊어짐 |
| 충돌 범위가 좁아져 해결이 쉬움 | PR이 2단계라 시간이 걸림 |
| 코드 리뷰를 더 세밀하게 진행 가능 | 처음엔 복잡하게 느껴질 수 있음 |
| 자식 브랜치에서 자유롭게 실험 가능 | |

> 💡 **팁**: 자식 브랜치에서는 자유롭게 개발하고,
> 부모 브랜치로 Merge할 때 코드 리뷰를 통해 품질을 검증하자!
> develop으로 올라가는 코드는 항상 검증된 상태여야 한다.

---

## 8. push 방법 (단계 완료 조건)

```bash
# 1. main 최신화
git switch main
git pull origin main

# 2. 파일 추가 및 커밋
git add docs/2일차_git_branch_전략.md
git commit -m "📝 docs: 2일차 Git 브랜치 전략 학습 정리 추가"

# 3. main 브랜치에 push
git push origin main
```

> ✅ **완료 조건**: 작성된 `docs/2일차_git_branch_전략.md` 파일이
> 원격 GitHub Repository의 `main` 브랜치에서 확인 가능해야 한다.


