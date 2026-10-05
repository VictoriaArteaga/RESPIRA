from pydantic import BaseModel, ConfigDict


class MunicipalityRead(BaseModel):
    id: int
    name: str
    department: str
    latitude: float
    longitude: float

    model_config = ConfigDict(from_attributes=True)
