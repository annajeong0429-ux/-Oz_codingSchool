from fastapi import APIRouter


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
@router.get("/practice_api/users")
def get_all_users():
    return user_list