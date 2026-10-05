from pydantic import BaseModel, ConfigDict, Field


class IraCaseRead(BaseModel):
    id: int
    municipality_id: int
    epidemiological_week: int = Field(ge=1, le=53)
    year: int = Field(ge=2000)
    cases: int = Field(ge=0)
    temperature: float
    precipitation: float = Field(ge=0)
    humidity: float = Field(ge=0, le=100)

    model_config = ConfigDict(from_attributes=True)
