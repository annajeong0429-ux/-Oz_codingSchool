import enum


class GenderEnum(str, enum.Enum):
    male = "male"
    female = "female"


class DepartmentEnum(str, enum.Enum):
    research = "research"      # 연구
    medical = "medical"        # 의료
    development = "development"  # 개발


class RoleEnum(str, enum.Enum):
    pending = "pending"  # 대기자 (가입 시 기본값)
    staff = "staff"      # 스태프
    admin = "admin"      # 어드민
