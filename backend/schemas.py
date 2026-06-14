"""Pydantic schemas and Enum types for the Carbon Footprint Awareness Platform.

Defines strict input validation models using Enum-based type constraints
and structured response models for the calculation API.
"""

from enum import Enum
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class TransportType(str, Enum):
    """Valid transportation modes with associated emission factor keys."""

    DRIVING_GASOLINE = "driving_gasoline"
    DRIVING_DIESEL = "driving_diesel"
    DRIVING_ELECTRIC = "driving_electric"
    MOTORCYCLE = "motorcycle"
    PUBLIC_TRANSIT_BUS = "public_transit_bus"
    PUBLIC_TRANSIT_TRAIN = "public_transit_train"
    FLIGHT_SHORT_HAUL = "flight_short_haul"
    FLIGHT_LONG_HAUL = "flight_long_haul"
    WALKING_BIKING = "walking_biking"


class DietType(str, Enum):
    """Valid diet pattern classifications."""

    MEAT_HEAVY = "meat_heavy"
    AVERAGE_MEAT = "average_meat"
    NO_BEEF = "no_beef"
    VEGETARIAN = "vegetarian"
    VEGAN = "vegan"


class ElectricityType(str, Enum):
    """Electricity source classifications."""

    GRID = "electricity_grid"
    GREEN = "electricity_green"


class TransportInput(BaseModel):
    """User input for transportation activity."""

    transport_type: TransportType = Field(..., description="Type of transportation used")
    distance_km: float = Field(..., ge=0.0, description="Distance traveled in kilometers")


class DietInput(BaseModel):
    """User input for dietary pattern."""

    diet_type: DietType = Field(..., description="Type of diet pattern")
    days: int = Field(1, ge=0, description="Number of days for this diet pattern")


class EnergyInput(BaseModel):
    """User input for home energy consumption."""

    electricity_kwh: float = Field(0.0, ge=0.0, description="Electricity consumed in kWh")
    electricity_type: ElectricityType = Field(
        ElectricityType.GRID, description="Grid electricity or green energy"
    )
    gas_kwh: float = Field(0.0, ge=0.0, description="Natural gas consumed in kWh")


class WasteInput(BaseModel):
    """User input for waste output."""

    unsorted_waste_kg: float = Field(0.0, ge=0.0, description="Amount of unsorted waste in kg")
    recycled_waste_kg: float = Field(0.0, ge=0.0, description="Amount of recycled waste in kg")


class CalculationRequest(BaseModel):
    """Complete calculation request payload containing all emission categories."""

    model_config = ConfigDict(use_enum_values=True)

    transport: TransportInput
    diet: DietInput
    energy: EnergyInput
    waste: WasteInput


class Breakdown(BaseModel):
    """Per-category CO2 emission breakdown in kg."""

    transport: float
    diet: float
    energy: float
    waste: float


class SavingsComparison(BaseModel):
    """Potential or realized CO2 savings from sustainable alternatives."""

    diet_saving_kg: float
    transport_saving_kg: float


class CalculationResponse(BaseModel):
    """Full calculation result returned to the client."""

    id: str
    timestamp: str
    inputs: CalculationRequest
    breakdown: Breakdown
    total_co2_kg: float
    savings: SavingsComparison
    recommendations: List[str]
    eco_score: int = Field(..., ge=0, le=100, description="Personal carbon efficiency score out of 100")
    micro_insight: str = Field(..., description="LLM-powered or fallback witty micro-insight tip")
