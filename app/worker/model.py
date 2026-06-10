# app/worker/model.py
# 폐렴 X-ray 예측 서빙 코드
# ConvNeXt-Tiny + DenseNet121 OR 앙상블 + Grad-CAM

import io
import base64
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
MODEL_DIR = Path(__file__).parent / "models"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
IMG_SIZE = 224
N_FOLDS = 5
MODEL_NAME = "convnext_densenet_OR"

# ── 2. 이미지 전처리 ──────────────────────────────────────────────
val_tf = transforms.Compose([
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor(),
    transforms.Normalize(
        [0.485, 0.456, 0.406],
        [0.229, 0.224, 0.225]
    ),
])

# ── 3. 모델 구조 정의 ─────────────────────────────────────────────
def _build_convnext() -> nn.Module:
    model = convnext_tiny(weights=None)
    model.classifier[2] = nn.Linear(
        model.classifier[2].in_features, 2
    )
    return model

def _build_densenet() -> nn.Module:
    model = densenet121(weights=None)
    model.classifier = nn.Linear(
        model.classifier.in_features, 2
    )
    return model

# ── 4. 가중치 로드 ────────────────────────────────────────────────
def _load_model(builder, pth_path: Path) -> nn.Module:
    model = builder()
    state_dict = torch.load(
        pth_path,
        map_location=DEVICE,
        weights_only=True  # 보안: pickle 임의 코드 실행 방지
    )
    model.load_state_dict(state_dict)
    model.to(DEVICE)
    model.eval()
    return model

def _load_fold_models(prefix: str, builder):
    models = []
    for fold in range(1, N_FOLDS + 1):
        pth = MODEL_DIR / f"{prefix}_fold{fold}.pth"
        if pth.exists():
            models.append(_load_model(builder, pth))
            print(f"  ✅ {pth.name} 로드 완료")
        else:
            print(f"  ❌ {pth.name} 없음 - 건너뜀")
    return models

# 전역 변수로 선언만 (실제 로딩은 startup 이벤트에서)
_convnext_models = []
_densenet_models = []

def load_models():
    """
    FastAPI startup 이벤트에서 호출
    서버 시작 시 1회만 모델을 메모리에 올림
    """
    global _convnext_models, _densenet_models
    print("모델 로딩 중...")
    _convnext_models = _load_fold_models("convnext_tiny_solo", _build_convnext)
    _densenet_models = _load_fold_models("densenet121", _build_densenet)
    print(f"ConvNeXt 로드: {len(_convnext_models)}개 fold")
    print(f"DenseNet 로드: {len(_densenet_models)}개 fold")

# ── 5. Grad-CAM ───────────────────────────────────────────────────
class GradCAM:
    """
    Grad-CAM: 모델이 예측 시 어느 부위를 보고 판단했는지 시각화
    폐렴 병변 위치를 히트맵으로 표현
    """
    def __init__(self, model: nn.Module, target_layer: nn.Module):
        self.model = model
        self.gradients = None
        self.activations = None

        # forward/backward hook 등록
        target_layer.register_forward_hook(self._save_activation)
        target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, input, output):
        self.activations = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(self, img_tensor: torch.Tensor, class_idx: int) -> np.ndarray:
        """히트맵 생성 (numpy array, 0~255)"""
        output = self.model(img_tensor)
        self.model.zero_grad()
        output[0, class_idx].backward()

        # 가중치 평균
        weights = self.gradients.mean(dim=(2, 3), keepdim=True)
        cam = (weights * self.activations).sum(dim=1, keepdim=True)
        cam = torch.relu(cam)

        # 정규화
        cam = cam.squeeze().cpu().numpy()
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        cam = (cam * 255).astype(np.uint8)
        return cam


def _get_target_layer(model: nn.Module, model_type: str) -> nn.Module:
    """모델별 Grad-CAM 타겟 레이어 반환"""
    if model_type == "convnext":
        return model.features[-1]
    else:  # densenet
        return model.features.norm5


def _generate_heatmap_base64(
    model: nn.Module,
    img_tensor: torch.Tensor,
    model_type: str,
    class_idx: int,
    original_size: tuple
) -> str:
    """
    Grad-CAM 히트맵 생성 후 base64 인코딩된 PNG 문자열 반환
    실제 서비스에서는 S3 등에 업로드 후 URL 반환
    """
    target_layer = _get_target_layer(model, model_type)
    grad_cam = GradCAM(model, target_layer)

    # 히트맵 생성
    cam = grad_cam.generate(img_tensor, class_idx)

    # 원본 이미지 크기로 리사이즈
    cam_img = Image.fromarray(cam).resize(original_size, Image.BILINEAR)

    # base64 인코딩
    buffer = io.BytesIO()
    cam_img.save(buffer, format="PNG")
    heatmap_b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:image/png;base64,{heatmap_b64}"


# ── 6. 예측 함수 ──────────────────────────────────────────────────
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
            "is_pneumonia": bool,       # True: 폐렴, False: 정상
            "confidence": float,         # 0.00 ~ 100.00 (퍼센트)
                                         # 항상 폐렴 클래스(1)의 확률을 퍼센트로 반환
                                         # (정상일 때도 폐렴 확률을 반환 - 스크리닝 목적)
            "heatmap_url": str,         # Grad-CAM 히트맵 base64 이미지
            "model_name": str,          # 사용한 모델명
        }
    """
    # 이미지 전처리
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    original_size = image.size
    img_tensor = val_tf(image).unsqueeze(0).to(DEVICE)

    # ConvNeXt 예측
    convnext_probs = _get_avg_probs(_convnext_models, img_tensor)
    convnext_pred = int(np.argmax(convnext_probs))

    # DenseNet 예측
    densenet_probs = _get_avg_probs(_densenet_models, img_tensor)
    densenet_pred = int(np.argmax(densenet_probs))

    # OR 앙상블: 두 모델 중 하나라도 폐렴(1)이면 폐렴으로 판단
    is_pneumonia = bool((convnext_pred + densenet_pred) >= 1)

    # confidence: 폐렴 클래스(1) 확률을 퍼센트로 변환 (2안: *100 후 Numeric(5,2) 유지)
    confidence = round(float(max(convnext_probs[1], densenet_probs[1])) * 100, 2)

    # Grad-CAM 히트맵 생성 (예측 확률이 더 높은 모델 사용)
    best_model = _convnext_models[0] if convnext_probs[1] >= densenet_probs[1] else _densenet_models[0]
    model_type = "convnext" if convnext_probs[1] >= densenet_probs[1] else "densenet"
    class_idx = 1  # 폐렴 클래스

# grad-cam은 gradient 필요하므로 no_grad 밖에서 실행
    try:
        img_tensor_grad = val_tf(image).unsqueeze(0).to(DEVICE)
        img_tensor_grad.requires_grad_(True)
        heatmap_url = _generate_heatmap_base64(
            best_model, img_tensor_grad, model_type, class_idx, original_size
        )
    except Exception as e:
        print(f"Grad-CAM 생성 실패: {e}")
        heatmap_url = None

    return {
        "is_pneumonia": is_pneumonia,
        "confidence": confidence,
        "heatmap_url": heatmap_url,
        "model_name": MODEL_NAME,
    }