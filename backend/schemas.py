from pydantic import BaseModel, Field, field_validator
from typing import List

class TransportInput(BaseModel):
    transport_type: str = Field(..., description="Type of transportation used")
    distance_km: float = Field(..., ge=0.0, description="Distance traveled in kilometers")

    @field_validator('transport_type')
    @classmethod
    def validate_transport_type(cls, v: str) -> str:
        valid_types = [
            "driving_gasoline", "driving_diesel", "driving_electric", "motorcycle",
            "public_transit_bus", "public_transit_train", "flight_short_haul",
            "flight_long_haul", "walking_biking"
        ]
        if v not in valid_types:
            raise ValueError(f"Invalid transport_type. Must be one of {valid_types}")
        return v

class DietInput(BaseModel):
    diet_type: str = Field(..., description="Type of diet pattern")
    days: int = Field(1, ge=0, description="Number of days for this diet pattern")

    @field_validator('diet_type')
    @classmethod
    def validate_diet_type(cls, v: str) -> str:
        valid_types = ["meat_heavy", "average_meat", "no_beef", "vegetarian", "vegan"]
        if v not in valid_types:
            raise ValueError(f"Invalid diet_type. Must be one of {valid_types}")
        return v

class EnergyInput(BaseModel):
    electricity_kwh: float = Field(0.0, ge=0.0, description="Electricity consumed in kWh")
    electricity_type: str = Field("electricity_grid", description="Grid electricity or green energy")
    gas_kwh: float = Field(0.0, ge=0.0, description="Natural gas consumed in kWh")

    @field_validator('electricity_type')
    @classmethod
    def validate_electricity_type(cls, v: str) -> str:
        valid_types = ["electricity_grid", "electricity_green"]
        if v not in valid_types:
            raise ValueError(f"Invalid electricity_type. Must be one of {valid_types}")
        return v

class WasteInput(BaseModel):
    unsorted_waste_kg: float = Field(0.0, ge=0.0, description="Amount of unsorted waste in kg")
    recycled_waste_kg: float = Field(0.0, ge=0.0, description="Amount of recycled waste in kg")

class CalculationRequest(BaseModel):
    transport: TransportInput
    diet: DietInput
    energy: EnergyInput
    waste: WasteInput

class Breakdown(BaseModel):
    transport: float
    diet: float
    energy: float
    waste: float

class SavingsComparison(BaseModel):
    diet_saving_kg: float
    transport_saving_kg: float

class CalculationResponse(BaseModel):
    id: str
    timestamp: str
    inputs: CalculationRequest
    breakdown: Breakdown
    total_co2_kg: float
    savings: SavingsComparison
    recommendations: List[str]
    eco_score: int = Field(..., ge=0, le=100, description="Personal carbon efficiency score out of 100")
    micro_insight: str = Field(..., description="LLM-powered or fallback witty micro-insight tip")
