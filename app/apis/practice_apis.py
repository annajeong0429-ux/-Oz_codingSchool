from fastapi import APIRouter, HTTPException

# 데이터 구조 틀(스키마)은 별도 파일로 분리하여 import
from app.schemas.practice_schemas import UserCreate, UserUpdate, UserResponse


# 라우터(Router) 생성하기
router = APIRouter()

#app/apis/practice_apis.py
user_list = [
    {
        "id": 1,
        "name": "홍길동",
        "age": 24,
        "email": "gildong24@example.com",
        "password": "Password1234!!"
    },
    {
        "id": 2,
        "name": "장문복",
        "age": 21,
        "email": "moonluck12@example.com",
        "password": "Check1321!"
    },
    {
        "id": 3,
        "name": "임우진",
        "age": 31,
        "email": "limousine33@example.com",
        "password": "lwsPAssword12@"
    }
]

# 모든 회원의 정보를 목록으로 조회하는 API
# 1번 (다이님 것에 변경 규칙 적용 시)
@router.get(
        "/practice_api/users", 
        summary="모든 회원 목록 조회",
        response_model=list[UserResponse],
        )   # 목록이라 list[...]
def get_all_users_handler():
    return user_list

# 2번. 특정 회원 조회 API
# 주소의 {user_id} 자리에 들어온 숫자를 user_id로 받음 (: int → 숫자만 허용)
@router.get(
        "/practice_api/users/{user_id}",
        summary="특정 회원 조회 API",
        response_model=UserResponse,
        )
def get_user_handler(user_id: int):
    # user_list를 하나씩 돌면서 id가 일치하는 회원을 찾음
    for user in user_list:
        if user["id"] == user_id:
            return user
    # 끝까지 못 찾으면 404 응답
    raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

# 3번. 회원 추가 API
@router.post(
        "/practice_api/users",
        summary="회원 추가 API",
        response_model=UserResponse,
        )
def create_user_handler(user: UserCreate):   # 위에서 만든 틀로 입력값이 자동 검증됨
    # 이메일 중복 검사 (틀에서는 못 하니 여기서)
    for existing in user_list:
        if existing["email"] == user.email:
            raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다.")

    # id 자동 증가: 기존 id 중 가장 큰 값 + 1 (목록이 비어있으면 1)
    # 추후 DB 연결 시 id는 DB에서 자동 생성(AUTO_INCREMENT)되므로 이 로직은 제거 예정.
    # TODO: DB 연결 시 자동 생성으로 교체
    new_id = max((u["id"] for u in user_list), default=0) + 1

    # 새 회원을 딕셔너리로 만들어 목록에 추가
    new_user = {
        "id": new_id,
        "name": user.name,
        "age": user.age,
        "email": user.email,
        "password": user.password,
    }
    user_list.append(new_user)
    return new_user

# 4번. 회원 정보 수정 API
@router.patch(
        "/practice_api/users/{user_id}",
        summary="회원 정보 수정 API",
        response_model=UserResponse,
        )
def update_user_handler(user_id: int, user_update: UserUpdate):
    # 모든 항목이 비어있으면 400 반환
    if user_update.age is None and user_update.email is None and user_update.password is None:
        raise HTTPException(status_code=400, detail="최소 하나의 항목을 입력해야 합니다.")

    for user in user_list:
        if user["id"] == user_id:
            if user_update.age is not None:
                user["age"] = user_update.age
            if user_update.email is not None:
                user["email"] = user_update.email
            if user_update.password is not None:
                user["password"] = user_update.password
            return user

    raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")

# 5번. 회원 삭제 API
@router.delete(
        "/practice_api/users/{user_id}",
        summary="회원 삭제 API",
        response_model=UserResponse,
        )
def delete_user_handler(user_id: int):
    # user_list를 하나씩 돌면서 id가 일치하는 회원을 찾음
    for user in user_list:
        if user["id"] == user_id:
            user_list.remove(user)   # 목록에서 해당 회원 제거
            return user              # 삭제된 회원 정보를 반환 (2·3·4번과 동일하게 password 제외)
    # 끝까지 못 찾으면 404 응답 (2·4번과 동일한 문구로 통일)
    raise HTTPException(status_code=404, detail="회원을 찾을 수 없습니다.")
