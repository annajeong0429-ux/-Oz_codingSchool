# app/apis/user_apis.py
from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    get_current_admin,
    get_current_user,
    get_user_from_refresh_token,
    hash_password,
    verify_password,
)
from app.core.db.databases import async_get_db
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.user_schemas import (
    AdminRoleUpdate,
    PasswordUpdate,
    TokenResponse,
    UserCreate,
    UserDelete,
    UserResponse,
    UserUpdate,
)

router = APIRouter(prefix="/api/v1", tags=["Users"])

REFRESH_COOKIE = "refresh_token"


# ── 1. 회원가입 ────────────────────────────────────────
@router.post("/users/signup", summary="회원가입", response_model=UserResponse, status_code=201)
async def signup(user_create: UserCreate, db: AsyncSession = Depends(async_get_db)):
    result = await db.execute(select(User).where(User.email == user_create.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")

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
        role=RoleEnum.pending,
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
# 프론트가 FormData(username/password)로 보내므로 OAuth2PasswordRequestForm 사용
@router.post("/users/login", summary="로그인", response_model=TokenResponse)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(async_get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="이메일 또는 비밀번호가 일치하지 않습니다.")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="비활성화된 계정입니다.")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # refresh token → HTTP-only 쿠키
    response.set_cookie(
        key=REFRESH_COOKIE,
        value=refresh_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )
    return TokenResponse(access_token=access_token, user=user)


# ── 3. 토큰 갱신 ───────────────────────────────────────
@router.post("/users/refresh", summary="토큰 갱신", response_model=TokenResponse)
async def refresh_token(
    response: Response,
    user: User = Depends(get_user_from_refresh_token),
):
    access_token = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)

    response.set_cookie(
        key=REFRESH_COOKIE,
        value=new_refresh,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
    )
    return TokenResponse(access_token=access_token, user=user)


# ── 4. 로그아웃 ────────────────────────────────────────
@router.post("/users/logout", summary="로그아웃", status_code=200)
async def logout(response: Response, current_user: User = Depends(get_current_user)):
    response.delete_cookie(key=REFRESH_COOKIE)
    return {"message": "로그아웃 되었습니다."}


# ── 5. 내 정보 조회 ────────────────────────────────────
@router.get("/users/me", summary="내 정보 조회", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# ── 6. 내 정보 수정 ────────────────────────────────────
@router.patch("/users/me", summary="내 정보 수정", response_model=UserResponse)
async def update_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    if user_update.department is None and user_update.phone_number is None:
        raise HTTPException(status_code=400, detail="수정할 항목을 입력해주세요.")

    if user_update.department is not None:
        current_user.department = user_update.department
    if user_update.phone_number is not None:
        result = await db.execute(
            select(User).where(User.phone_number == user_update.phone_number, User.id != current_user.id)
        )
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="이미 사용 중인 전화번호입니다.")
        current_user.phone_number = user_update.phone_number

    try:
        await db.commit()
        await db.refresh(current_user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="이미 사용 중인 전화번호입니다.")
    return current_user


# ── 7. 비밀번호 변경 ───────────────────────────────────
@router.patch("/users/me/password", summary="비밀번호 변경", status_code=200)
async def update_password(
    password_update: PasswordUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="현재 비밀번호가 일치하지 않습니다.")
    if password_update.current_password == password_update.new_password:
        raise HTTPException(status_code=400, detail="새 비밀번호는 현재 비밀번호와 달라야 합니다.")

    current_user.hashed_password = hash_password(password_update.new_password)
    await db.commit()
    return {"message": "비밀번호가 변경되었습니다."}


# ── 8. 회원 탈퇴 ───────────────────────────────────────
@router.delete("/users/me", summary="회원 탈퇴", status_code=200)
async def delete_me(
    user_delete: UserDelete,
    response: Response,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
):
    if not verify_password(user_delete.password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다.")

    try:
        await db.delete(current_user)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="삭제 처리 중 오류가 발생했습니다.")

    response.delete_cookie(key=REFRESH_COOKIE)
    return {"message": "회원 탈퇴가 완료되었습니다."}


# ── 9. 관리자 - 전체 유저 목록 ────────────────────────
@router.get("/admin/users", summary="전체 유저 목록 (관리자)", response_model=list[UserResponse])
async def admin_get_users(
    email: str | None = None,
    name: str | None = None,
    department: str | None = None,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(async_get_db),
):
    query = select(User)
    if email:
        query = query.where(User.email.contains(email))
    if name:
        query = query.where(User.name.contains(name))
    if department:
        query = query.where(User.department == department)

    result = await db.execute(query)
    return result.scalars().all()


# ── 10. 관리자 - 권한 변경 ────────────────────────────
@router.patch("/admin/users/role", summary="유저 권한 변경 (관리자)", response_model=UserResponse)
async def admin_update_role(
    role_data: AdminRoleUpdate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(async_get_db),
):
    result = await db.execute(select(User).where(User.id == role_data.user_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

    target.role = role_data.role
    await db.commit()
    await db.refresh(target)
    return target
