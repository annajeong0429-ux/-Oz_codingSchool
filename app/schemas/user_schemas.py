from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re
import enum


# ── Enum ──────────────────────────────────────────────
class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"


class DepartmentEnum(str, enum.Enum):
    radiology = "radiology"
    internal = "internal"
    emergency = "emergency"


class RoleEnum(str, enum.Enum):
    admin = "admin"
    doctor = "doctor"


# ── 회원가입 요청 ──────────────────────────────────────
class UserCreate(BaseModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=20)
    name: str = Field(min_length=2, max_length=20)
    phone_number: str = Field(max_length=20)
    gender: GenderEnum
    department: DepartmentEnum
    role: RoleEnum

    @field_validator("email")
    @classmethod
    def check_email(cls, value):
        pattern = r"^[\w.-]+@[\w.-]+\.\w+$"
        if not re.match(pattern, value):
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        return value

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        if not re.search(r"[A-Z]", value):
            raise ValueError("비밀번호에 대문자가 1개 이상 필요합니다.")
        if not re.search(r"[a-z]", value):
            raise ValueError("비밀번호에 소문자가 1개 이상 필요합니다.")
        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("비밀번호에 특수문자가 1개 이상 필요합니다.")
        return value


# ── 로그인 요청 ────────────────────────────────────────
class UserLogin(BaseModel):
    email: str
    password: str


# ── 로그아웃 요청 ──────────────────────────────────────
class UserLogout(BaseModel):
    refresh_token: str


# ── 내 정보 수정 요청 ──────────────────────────────────
class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=20)
    phone_number: Optional[str] = Field(default=None, max_length=20)


# ── 비밀번호 변경 요청 ─────────────────────────────────
class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=20)

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, value):
        if not re.search(r"[A-Z]", value):
            raise ValueError("비밀번호에 대문자가 1개 이상 필요합니다.")
        if not re.search(r"[a-z]", value):
            raise ValueError("비밀번호에 소문자가 1개 이상 필요합니다.")
        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("비밀번호에 특수문자가 1개 이상 필요합니다.")
        return value


# ── 회원 탈퇴 요청 ─────────────────────────────────────
class UserDelete(BaseModel):
    password: str


# ── 응답 ───────────────────────────────────────────────
class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    phone_number: Optional[str] = None
    gender: GenderEnum
    department: DepartmentEnum
    role: RoleEnum
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
