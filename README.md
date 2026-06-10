# AI Health Web Assignment

## Alembic Migration Guide

이 프로젝트는 데이터베이스 마이그레이션을 위해 Alembic을 사용합니다.

### 1. 마이그레이션 파일 생성 (자동 생성)
모델(`app/models/`)이 변경된 경우 다음 명령어를 실행하여 마이그레이션 파일을 생성합니다.
```bash
uv run alembic revision --autogenerate -m "변경 내용 설명"
```

### 2. 데이터베이스에 반영
생성된 마이그레이션을 데이터베이스에 적용하려면 다음 명령어를 실행합니다.
```bash
uv run alembic upgrade head
```

### 3. 이전 상태로 되돌리기 (Rollback)
마지막 마이그레이션을 취소하려면 다음 명령어를 실행합니다.
```bash
uv run alembic downgrade -1
```

### 4. 모델 가중치 크기 문제로 가중치 파일 링크 공유합니다.
https://drive.google.com/drive/folders/1x8TnELyNyFajk-VBzJw8z21yUm1EDKDR?usp=sharing


### 5. 모델 가중치 파일 설정

가중치 파일은 용량 문제로 Git에 포함되지 않습니다.
아래 Google Drive에서 다운로드 후 `app/worker/models/` 폴더에 저장해주세요.

**다운로드 링크:**
https://drive.google.com/drive/folders/1x8TnELyNyFajk-VBzJw8z21yUm1EDKDR?usp=sharing

**파일 목록:**
| 파일명 | 모델 |
|---|---|
| `convnext_tiny_solo_fold1.pth` | ConvNeXt-Tiny Fold 1 |
| `convnext_tiny_solo_fold2.pth` | ConvNeXt-Tiny Fold 2 |
| `convnext_tiny_solo_fold3.pth` | ConvNeXt-Tiny Fold 3 |
| `convnext_tiny_solo_fold4.pth` | ConvNeXt-Tiny Fold 4 |
| `convnext_tiny_solo_fold5.pth` | ConvNeXt-Tiny Fold 5 |
| `densenet121_fold1.pth` | DenseNet121 Fold 1 |
| `densenet121_fold2.pth` | DenseNet121 Fold 2 |
| `densenet121_fold3.pth` | DenseNet121 Fold 3 |
| `densenet121_fold4.pth` | DenseNet121 Fold 4 |
| `densenet121_fold5.pth` | DenseNet121 Fold 5 |

**저장 경로:**
```
app/
└── worker/
    └── models/
        ├── convnext_tiny_solo_fold1.pth
        ├── convnext_tiny_solo_fold2.pth
        ├── ...
        ├── densenet121_fold1.pth
        └── densenet121_fold5.pth
```