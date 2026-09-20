from pydantic import BaseModel


class MemberProfile(BaseModel):
    member_id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    member_status: str
