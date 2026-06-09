from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.core.db.databases import async_get_db
from app.models.user import User
from app.models.enums import RoleEnum
from app.schemas.user_schemas import (
    UserCreate, UserLogin, UserLogout,
    UserUpdate, PasswordUpdate, UserDelete,
    UserResponse, TokenResponse
)
import hashlib

router = APIRouter(prefix="/api/v1", tags=["Users"])


# 비밀번호 해시 함수 (sha256 - 추후 bcrypt/argon2로 교체 권장)
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
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

    # 전화번호 중복 확인
    result2 = await db.execute(select(User).where(User.phone_number == user_create.phone_number))
    if result2.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 사용 중인 전화번호입니다.")

    new_user = User(
        email=user_create.email,
        hashed_password=hash_password(user_create.password),
        name=user_create.name,
        phone_number=user_create.phone_number,
        gender=user_create.gender,
        department=user_create.department,
        role=RoleEnum.pending,  # 가입 시 기본값 대기자 (REQ-USER-005)
    )
    try:
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일 또는 전화번호입니다.")
    return new_user


# ── 2. 로그인 ──────────────────────────────────────────
@router.post(
    "/auth/login/",
    summary="로그인",
    response_model=TokenResponse,
    status_code=200,
)
async def login(user_login: UserLogin, db: AsyncSession = Depends(async_get_db)):
    result = await db.execute(select(User).where(User.email == user_login.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="이메일 또는 비밀번호가 일치하지 않습니다.")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 계정입니다.")

    # TODO: 추후 JWT(access 30분/refresh 7일, http_only 쿠키)로 교체 예정
    return TokenResponse(
        access_token=f"token_{user.id}",
        user=user,
    )


# ── 3. 로그아웃 ────────────────────────────────────────
@router.post(
    "/auth/logout/",
    summary="로그아웃",
    status_code=200,
)
async def logout(user_logout: UserLogout):
    # TODO: 추후 토큰 블랙리스트 처리 예정
    return {"message": "로그아웃 되었습니다."}


# ── 4. 회원 목록 조회 (관리자 전용) ────────────────────
@router.get(
    "/users/",
    summary="회원 목록 조회",
    response_model=list[UserResponse],
    status_code=200,
)
async def get_users(
    email: str = None,
    name: str = None,
    department: str = None,
    db: AsyncSession = Depends(async_get_db),
):
    # TODO: 추후 JWT에서 Admin 권한 체크 추가 예정
    query = select(User)  # is_active 필터 제거 → 전체 목록 조회

    # 이메일 검색
    if email:
        query = query.where(User.email.contains(email))
    # 이름 검색
    if name:
        query = query.where(User.name.contains(name))
    # 부서 필터
    if department:
        query = query.where(User.department == department)

    result = await db.execute(query)
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
    # TODO: 추후 JWT 토큰에서 user_id 추출 예정
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")
    return user


# ── 6. 내 정보 수정 (부서 + 휴대폰번호) ───────────────
@router.patch(
    "/users/me/",
    summary="내 정보 수정",
    response_model=UserResponse,
    status_code=200,
)
async def update_me(user_id: int, user_update: UserUpdate, db: AsyncSession = Depends(async_get_db)):
    # TODO: 추후 JWT 토큰에서 user_id 추출 예정
    if user_update.department is None and user_update.phone_number is None:
        raise HTTPException(status_code=400, detail="수정할 항목을 입력해주세요.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

    if user_update.department is not None:
        user.department = user_update.department
    if user_update.phone_number is not None:
        # 전화번호 중복 확인
        result2 = await db.execute(
            select(User).where(User.phone_number == user_update.phone_number, User.id != user_id)
        )
        if result2.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="이미 사용 중인 전화번호입니다.")
        user.phone_number = user_update.phone_number

    try:
        await db.commit()
        await db.refresh(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="이미 사용 중인 전화번호입니다.")
    return user


# ── 7. 비밀번호 변경 ───────────────────────────────────
@router.patch(
    "/users/me/password/",
    summary="비밀번호 변경",
    status_code=200,
)
async def update_password(user_id: int, password_update: PasswordUpdate, db: AsyncSession = Depends(async_get_db)):
    # TODO: 추후 JWT 토큰에서 user_id 추출 예정
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


# ── 8. 회원 탈퇴 (하드 삭제) ───────────────────────────
@router.delete(
    "/users/me/",
    summary="회원 탈퇴",
    status_code=200,
)
async def delete_me(user_id: int, user_delete: UserDelete, db: AsyncSession = Depends(async_get_db)):
    # TODO: 추후 JWT 토큰에서 user_id 추출 예정
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

    if not verify_password(user_delete.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")

    # 하드 삭제 (REQ-USER-009: 즉시 삭제)
    await db.delete(user)
    await db.commit()
    return {"message": "회원 탈퇴가 완료되었습니다."}
