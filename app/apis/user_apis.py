from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.db.databases import async_get_db
from app.models.user import User, GenderEnum, DepartmentEnum, RoleEnum
from app.schemas.user_schemas import (
    UserCreate, UserLogin, UserLogout,
    UserUpdate, PasswordUpdate, UserDelete,
    UserResponse, TokenResponse
)
import hashlib

router = APIRouter(prefix="/api/v1", tags=["Users"])


# 비밀번호 해시 함수 (간단한 sha256 사용)
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


# ── 1. 회원가입 ────────────────────────────────────────
@router.post(
    "/auth/register/",
    summary="회원가입",
    response_model=UserResponse,
    status_code=201,
)
async def register(user_create: UserCreate, db: AsyncSession = Depends(async_get_db)):
    # 이메일 중복 확인
    result = await db.execute(select(User).where(User.email == user_create.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

    # 전화번호 중복 확인
    result2 = await db.execute(select(User).where(User.phone_number == user_create.phone_number))
    existing2 = result2.scalar_one_or_none()
    if existing2:
        raise HTTPException(status_code=400, detail="이미 사용 중인 전화번호입니다.")

    new_user = User(
        email=user_create.email,
        hashed_password=hash_password(user_create.password),
        name=user_create.name,
        phone_number=user_create.phone_number,
        gender=user_create.gender,
        department=user_create.department,
        role=user_create.role,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


# ── 2. 로그인 ──────────────────────────────────────────
@router.post(
    "/auth/login/",
    summary="로그인",
    status_code=200,
)
async def login(user_login: UserLogin, db: AsyncSession = Depends(async_get_db)):
    result = await db.execute(select(User).where(User.email == user_login.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="이메일 또는 비밀번호가 일치하지 않습니다.")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 계정입니다.")

    return {
        "access_token": f"token_{user.id}",  # 추후 JWT로 교체 예정
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
        }
    }


# ── 3. 로그아웃 ────────────────────────────────────────
@router.post(
    "/auth/logout/",
    summary="로그아웃",
    status_code=200,
)
async def logout(user_logout: UserLogout):
    # 추후 토큰 블랙리스트 처리 예정
    return {"message": "로그아웃 되었습니다."}


# ── 4. 회원 목록 조회 ──────────────────────────────────
@router.get(
    "/users/",
    summary="회원 목록 조회",
    response_model=list[UserResponse],
    status_code=200,
)
async def get_users(db: AsyncSession = Depends(async_get_db)):
    result = await db.execute(select(User).where(User.is_active == True))
    users = result.scalars().all()
    return users


# ── 5. 내 정보 조회 ────────────────────────────────────
@router.get(
    "/users/me/",
    summary="내 정보 조회",
    response_model=UserResponse,
    status_code=200,
)
async def get_me(user_id: int, db: AsyncSession = Depends(async_get_db)):
    # 추후 JWT 토큰에서 user_id 추출 예정
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")
    return user


# ── 6. 내 정보 수정 ────────────────────────────────────
@router.patch(
    "/users/me/",
    summary="내 정보 수정",
    response_model=UserResponse,
    status_code=200,
)
async def update_me(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(async_get_db)):
    # 추후 JWT 토큰에서 user_id 추출 예정
    if user_update.name is None and user_update.phone_number is None:
        raise HTTPException(status_code=400, detail="수정할 항목을 입력해주세요.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

    if user_update.name is not None:
        user.name = user_update.name
    if user_update.phone_number is not None:
        user.phone_number = user_update.phone_number

    await db.commit()
    await db.refresh(user)
    return user


# ── 7. 비밀번호 변경 ───────────────────────────────────
@router.patch(
    "/users/me/password/",
    summary="비밀번호 변경",
    status_code=200,
)
async def update_password(user_id: int, password_update: PasswordUpdate, db: AsyncSession = Depends(async_get_db)):
    # 추후 JWT 토큰에서 user_id 추출 예정
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

    if not verify_password(password_update.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")

    if password_update.current_password == password_update.new_password:
        raise HTTPException(status_code=400, detail="새 비밀번호는 현재 비밀번호와 달라야 합니다.")

    user.hashed_password = hash_password(password_update.new_password)
    await db.commit()
    return {"message": "비밀번호가 변경되었습니다."}


# ── 8. 회원 탈퇴 ───────────────────────────────────────
@router.delete(
    "/users/me/",
    summary="회원 탈퇴",
    status_code=200,
)
async def delete_me(user_id: int, user_delete: UserDelete, db: AsyncSession = Depends(async_get_db)):
    # 추후 JWT 토큰에서 user_id 추출 예정
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

    if not verify_password(user_delete.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")

    user.is_active = False  # 실제 삭제 대신 비활성화 처리
    await db.commit()
    return {"message": "회원 탈퇴가 완료되었습니다."}
