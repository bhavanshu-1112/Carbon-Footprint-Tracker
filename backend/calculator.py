"""Carbon footprint calculation engine.

Computes per-category CO2 emissions, generates savings comparisons,
and produces actionable recommendations based on user activity inputs.
"""

import uuid
from datetime import datetime, timezone

from backend.gemini_service import generate_witty_tip
from backend.schemas import (
    CalculationRequest,
    CalculationResponse,
    Breakdown,
    DietType,
    SavingsComparison,
    TransportType,
)


async def calculate_footprint(
    request: CalculationRequest, factors: dict[str, dict]
) -> CalculationResponse:
    """Calculate total carbon footprint and return a structured response.

    Computes CO2 emissions across four categories (transport, diet, energy,
    waste), determines potential or realized savings from sustainable
    alternatives, generates ranked recommendations, and fetches an
    AI-powered micro-insight for the highest-emitting category.

    Args:
        request: Validated user inputs for all emission categories.
        factors: Emission factor lookup table loaded from the database.

    Returns:
        A fully populated CalculationResponse with breakdown, savings,
        recommendations, eco score, and micro-insight.
    """
    # Extract factors
    transport_factors: dict[str, float] = factors["transport"]
    diet_factors: dict[str, float] = factors["diet"]
    energy_factors: dict[str, float] = factors["energy"]
    waste_factors: dict[str, float] = factors["waste"]

    # 1. Transport Calculation
    t_input = request.transport
    t_factor = transport_factors.get(t_input.transport_type, 0.0)
    transport_co2 = t_input.distance_km * t_factor

    # 2. Diet Calculation
    d_input = request.diet
    d_factor = diet_factors.get(d_input.diet_type, 0.0)
    diet_co2 = d_input.days * d_factor

    # 3. Energy Calculation
    e_input = request.energy
    e_factor = energy_factors.get(e_input.electricity_type, 0.0)
    electricity_co2 = e_input.electricity_kwh * e_factor
    gas_co2 = e_input.gas_kwh * energy_factors.get("natural_gas_kwh", 0.0)
    energy_co2 = electricity_co2 + gas_co2

    # 4. Waste Calculation
    w_input = request.waste
    unsorted_co2 = w_input.unsorted_waste_kg * waste_factors.get("unsorted_waste_kg", 0.0)
    recycled_co2 = w_input.recycled_waste_kg * waste_factors.get("recycled_waste_kg", 0.0)
    waste_co2 = unsorted_co2 + recycled_co2

    total_co2 = transport_co2 + diet_co2 + energy_co2 + waste_co2

    # --- Savings Comparison ---
    meat_heavy_factor = diet_factors[DietType.MEAT_HEAVY]
    vegan_factor = diet_factors[DietType.VEGAN]

    if d_input.diet_type in (DietType.VEGAN, DietType.VEGETARIAN):
        # Show how much they saved compared to a heavy meat diet
        diet_saving = (meat_heavy_factor - d_factor) * d_input.days
    else:
        # Show how much they could save by shifting to a vegan diet
        diet_saving = (d_factor - vegan_factor) * d_input.days

    # Transport saving: Compare current mode to train/bus if driving/flying
    driving_gas_factor = transport_factors[TransportType.DRIVING_GASOLINE]
    train_factor = transport_factors[TransportType.PUBLIC_TRANSIT_TRAIN]

    high_emission_transport = (
        TransportType.DRIVING_GASOLINE,
        TransportType.DRIVING_DIESEL,
        TransportType.MOTORCYCLE,
        TransportType.FLIGHT_SHORT_HAUL,
        TransportType.FLIGHT_LONG_HAUL,
    )
    if t_input.transport_type in high_emission_transport:
        transport_saving = (t_factor - train_factor) * t_input.distance_km
    else:
        transport_saving = (driving_gas_factor - t_factor) * t_input.distance_km

    # --- Recommendations ---
    recommendations: list[str] = []

    if t_input.transport_type in (TransportType.DRIVING_GASOLINE, TransportType.DRIVING_DIESEL):
        electric_factor = transport_factors[TransportType.DRIVING_ELECTRIC]
        recommendations.append(
            f"Consider switching to public transit or an electric vehicle. "
            f"Driving gasoline/diesel emits ~{t_factor:.3f} kg CO2/km compared to "
            f"electric (~{electric_factor:.3f} kg) or train (~{train_factor:.3f} kg)."
        )
    elif t_input.transport_type in (TransportType.FLIGHT_SHORT_HAUL, TransportType.FLIGHT_LONG_HAUL):
        recommendations.append(
            "Air travel is highly carbon-intensive. For short distances, try high-speed rail, "
            "or consider offsetting your flight carbon via verified programs."
        )

    if d_input.diet_type in (DietType.MEAT_HEAVY, DietType.AVERAGE_MEAT):
        recommendations.append(
            f"Reduce meat intake. Switching from a heavy meat diet to a vegetarian or vegan diet "
            f"saves up to {(meat_heavy_factor - vegan_factor):.1f} kg CO2 per day."
        )
    elif d_input.diet_type == DietType.VEGETARIAN:
        recommendations.append(
            "Great job eating vegetarian! Transitioning to a fully plant-based (vegan) diet "
            "could reduce your food footprint by another 0.9 kg CO2 per day."
        )

    if e_input.electricity_type == "electricity_grid" and e_input.electricity_kwh > 0:
        recommendations.append(
            "Contact your energy provider to switch to a 100% green/renewable energy tariff, "
            "which reduces electricity emissions to 0 kg CO2/kWh."
        )
    if e_input.gas_kwh > 0:
        recommendations.append(
            "Investigate home electrification (heat pumps, induction stoves) to replace "
            "natural gas consumption."
        )

    if w_input.unsorted_waste_kg > w_input.recycled_waste_kg:
        recommendations.append(
            "Improve waste sorting. Recycled waste has a significantly lower carbon footprint "
            "(~0.1 kg CO2/kg) compared to landfilled waste (~0.5 kg CO2/kg)."
        )

    if not recommendations:
        recommendations.append(
            "Excellent work! Your carbon footprint is already optimized. "
            "Keep promoting sustainable habits!"
        )

    # Identify category with the highest emission
    categories: dict[str, float] = {
        "transport": transport_co2,
        "diet": diet_co2,
        "energy": energy_co2,
        "waste": waste_co2,
    }
    highest_category = max(categories, key=categories.get)  # type: ignore[arg-type]
    highest_co2 = categories[highest_category]

    # Generate micro insight via Gemini / fallback
    micro_insight = await generate_witty_tip(highest_category, highest_co2, total_co2)

    # Calculate Eco Score (0 to 100)
    eco_score = max(0, min(100, round(100 - (total_co2 * 1.2))))

    return CalculationResponse(
        id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        inputs=request,
        breakdown=Breakdown(
            transport=round(transport_co2, 3),
            diet=round(diet_co2, 3),
            energy=round(energy_co2, 3),
            waste=round(waste_co2, 3),
        ),
        total_co2_kg=round(total_co2, 3),
        savings=SavingsComparison(
            diet_saving_kg=round(diet_saving, 3),
            transport_saving_kg=round(transport_saving, 3),
        ),
        recommendations=recommendations,
        eco_score=eco_score,
        micro_insight=micro_insight,
    )
