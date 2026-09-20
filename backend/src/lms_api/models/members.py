from pydantic import BaseModel, ConfigDict, Field


class MemberProfile(BaseModel):
    member_id: int
    first_name: str
    last_name: str
    email: str
    phone: str | None
    member_status: str


class MemberContactUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = Field(min_length=1, max_length=80)
    phone: str | None = Field(default=None, max_length=20)
