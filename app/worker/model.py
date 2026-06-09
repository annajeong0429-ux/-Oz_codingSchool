# worker/model.py
# 폐렴 X-ray 예측 서빙 코드
# ConvNeXt-Tiny + DenseNet121 OR 앙상블

import io
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms
from torchvision.models import (
    ConvNeXt_Tiny_Weights,
    DenseNet121_Weights,
    convnext_tiny,
    densenet121,
)

# ── 1. 기본 설정 ──────────────────────────────────────────────────
# 가중치 파일이 있는 경로
MODEL_DIR = Path(__file__).parent / "models"

# GPU 있으면 GPU, 없으면 CPU 사용
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

IMG_SIZE = 224   # 학습 때와 동일한 이미지 크기
N_FOLDS = 5      # 학습 때 사용한 fold 수
MODEL_NAME = "convnext_densenet_OR"  # 사용 모델명

# ── 2. 이미지 전처리 ──────────────────────────────────────────────
# 학습 때 val_tf와 동일하게 설정 (학습/서빙 전처리가 달라지면 성능 저하)
val_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    ),
])

# ── 3. 모델 구조 정의 ─────────────────────────────────────────────
# 학습 때와 동일한 구조로 정의해야 가중치를 올바르게 로드할 수 있음
def _build_convnext() -> nn.Module:
    model = convnext_tiny(weights=None)  # 가중치는 .pth에서 로드
    model.classifier[2] = nn.Linear(
        model.classifier[2].in_features, 2  # 2: 정상/폐렴
    )
    return model

def _build_densenet() -> nn.Module:
    model = densenet121(weights=None)  # 가중치는 .pth에서 로드
    model.classifier = nn.Linear(
        model.classifier.in_features, 2  # 2: 정상/폐렴
    )
    return model

# ── 4. 가중치 로드 ────────────────────────────────────────────────
def _load_model(builder, pth_path: Path) -> nn.Module:
    """모델 구조를 만들고 가중치 파일을 로드해서 반환"""
    model = builder()
    state_dict = torch.load(pth_path, map_location=DEVICE)
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()  # 예측 모드로 설정 (dropout, batchnorm 비활성화)
    return model

def _load_fold_models(prefix: str, builder):
    """fold1~5 가중치 파일을 모두 로드해서 리스트로 반환"""
    models = []
    for fold in range(1, N_FOLDS + 1):
        pth = MODEL_DIR / f"{prefix}_fold{fold}.pth"
        if pth.exists():
            models.append(_load_model(builder, pth))
            print(f"  ✅ {pth.name} 로드 완료")
        else:
            print(f"  ❌ {pth.name} 없음 - 건너뜀")
    return models

# 서버 시작 시 1회만 모델을 메모리에 올림
print("모델 로딩 중...")
_convnext_models = _load_fold_models("convnext_tiny_solo", _build_convnext)
_densenet_models = _load_fold_models("densenet121", _build_densenet)
print(f"ConvNeXt 로드: {len(_convnext_models)}개 fold")
print(f"DenseNet 로드: {len(_densenet_models)}개 fold")

# ── 5. 예측 함수 ──────────────────────────────────────────────────
def _get_avg_probs(models: list, img_tensor: torch.Tensor) -> np.ndarray:
    """여러 fold 모델의 softmax 확률 평균 반환"""
    if not models:
        raise RuntimeError("로드된 모델이 없습니다.")

    probs_sum = np.zeros(2)
    with torch.no_grad():
        for model in models:
            output = model(img_tensor)
            prob = torch.softmax(output, dim=1).cpu().numpy()[0]
            probs_sum += prob

    return probs_sum / len(models)


def predict_pneumonia(image_bytes: bytes) -> dict:
    """
    X-ray 이미지 바이트를 받아서 폐렴 예측 결과 반환

    Args:
        image_bytes: 업로드된 X-ray 이미지 바이트

    Returns:
        {
            "is_pneumonia": bool,   # True: 폐렴, False: 정상
            "confidence": float,    # 0.0 ~ 1.0
            "model_name": str,      # 사용한 모델명
        }
    """
    # 이미지 바이트 → PIL Image → 텐서 변환
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_tensor = val_tf(image).unsqueeze(0).to(DEVICE)

    # ConvNeXt 예측
    convnext_probs = _get_avg_probs(_convnext_models, img_tensor)
    convnext_pred = int(np.argmax(convnext_probs))

    # DenseNet 예측
    densenet_probs = _get_avg_probs(_densenet_models, img_tensor)
    densenet_pred = int(np.argmax(densenet_probs))

    # OR 앙상블: 두 모델 중 하나라도 폐렴(1)이면 폐렴으로 판단
    is_pneumonia = bool((convnext_pred + densenet_pred) >= 1)

    # confidence: 폐렴 클래스(1) 확률 중 더 높은 값
    confidence = float(max(convnext_probs[1], densenet_probs[1]))

    return {
        "is_pneumonia": is_pneumonia,
        "confidence": round(confidence, 4),
        "model_name": MODEL_NAME,
    }