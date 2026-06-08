import enum

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