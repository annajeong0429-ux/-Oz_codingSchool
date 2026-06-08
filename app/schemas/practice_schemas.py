from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re   # 정규표현식(이메일·비밀번호 검사)용


# 3번에서 입력받을 데이터의 "틀" + 검증 규칙
class UserCreate(BaseModel):
    # 이름: 2~10글자
    name: str = Field(min_length=2, max_length=10)
    # 나이: 14 이상 (ge = greater than or equal)
    age: int = Field(ge=14)
    # 이메일: 최대 30자 (형식·중복은 아래에서 따로 검사)
    email: str = Field(max_length=30)
    # 비밀번호: 8~20자 (대소문자·특수문자 포함 여부는 아래에서 검사)
    password: str = Field(min_length=8, max_length=20)

    # 이메일 형식을 정규표현식으로 검사
    @field_validator("email")
    @classmethod
    def check_email(cls, value):
        pattern = r"^[\w.-]+@[\w.-]+\.\w+$"
        if not re.match(pattern, value):
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        return value

    # 비밀번호에 대문자·소문자·특수문자가 각각 1개 이상 있는지 검사
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


# 4번에서 입력받을 데이터의 틀 (모든 항목 선택 입력)
class UserUpdate(BaseModel):
    age: Optional[int] = Field(default=None, ge=14)
    email: Optional[str] = Field(default=None, max_length=30)
    password: Optional[str] = Field(default=None, min_length=8, max_length=20)

    @field_validator("email")
    @classmethod
    def check_email(cls, value):
        if value is None:
            return value
        pattern = r"^[\w.-]+@[\w.-]+\.\w+$"
        if not re.match(pattern, value):
            raise ValueError("올바른 이메일 형식이 아닙니다.")
        return value

    @field_validator("password")
    @classmethod
    def check_password(cls, value):
        if value is None:
            return value
        if not re.search(r"[A-Z]", value):
            raise ValueError("비밀번호에 대문자가 1개 이상 필요합니다.")
        if not re.search(r"[a-z]", value):
            raise ValueError("비밀번호에 소문자가 1개 이상 필요합니다.")
        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("비밀번호에 특수문자가 1개 이상 필요합니다.")
        return value


# 응답으로 내보낼 데이터의 틀 (password 제외 → 자동으로 안 나감)
class UserResponse(BaseModel):
    id: int
    name: str
    age: int
    email: str
