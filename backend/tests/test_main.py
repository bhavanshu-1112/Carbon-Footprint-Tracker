import pytest

def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_get_constants(client):
    response = client.get("/api/constants")
    assert response.status_code == 200
    data = response.json()
    assert "transport" in data
    assert "diet" in data
    assert "energy" in data
    assert "waste" in data
    assert data["transport"]["driving_gasoline"] == 0.170

def test_calculate_success_gasoline_meat(client):
    payload = {
        "transport": {
            "transport_type": "driving_gasoline",
            "distance_km": 100.0
        },
        "diet": {
            "diet_type": "meat_heavy",
            "days": 7
        },
        "energy": {
            "electricity_kwh": 150.0,
            "electricity_type": "electricity_grid",
            "gas_kwh": 50.0
        },
        "waste": {
            "unsorted_waste_kg": 10.0,
            "recycled_waste_kg": 5.0
        }
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 201
    data = response.json()
    
    assert "id" in data
    assert "timestamp" in data
    assert data["total_co2_kg"] > 0
    
    # Check breakdown matches calculation
    # Transport: 100 * 0.17 = 17
    # Diet: 7 * 7.2 = 50.4
    # Energy: 150 * 0.40 + 50 * 0.18 = 60 + 9 = 69
    # Waste: 10 * 0.5 + 5 * 0.1 = 5 + 0.5 = 5.5
    # Total: 17 + 50.4 + 69 + 5.5 = 141.9
    assert data["breakdown"]["transport"] == 17.0
    assert data["breakdown"]["diet"] == 50.4
    assert data["breakdown"]["energy"] == 69.0
    assert data["breakdown"]["waste"] == 5.5
    assert data["total_co2_kg"] == 141.9
    
    # Savings (Potential Savings):
    # Diet saving (meat_heavy to vegan): (7.2 - 2.9) * 7 = 4.3 * 7 = 30.1
    # Transport saving (driving_gasoline to train): (0.170 - 0.035) * 100 = 0.135 * 100 = 13.5
    assert data["savings"]["diet_saving_kg"] == 30.1
    assert data["savings"]["transport_saving_kg"] == 13.5
    
    # Check recommendations exist
    assert len(data["recommendations"]) > 0
    
    # Check eco score and micro insight
    assert data["eco_score"] == 0
    assert "micro_insight" in data
    assert isinstance(data["micro_insight"], str)


def test_calculate_success_vegan_train(client):
    payload = {
        "transport": {
            "transport_type": "public_transit_train",
            "distance_km": 100.0
        },
        "diet": {
            "diet_type": "vegan",
            "days": 7
        },
        "energy": {
            "electricity_kwh": 150.0,
            "electricity_type": "electricity_green",
            "gas_kwh": 0.0
        },
        "waste": {
            "unsorted_waste_kg": 0.0,
            "recycled_waste_kg": 5.0
        }
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 201
    data = response.json()
    
    # Transport: 100 * 0.035 = 3.5
    # Diet: 7 * 2.9 = 20.3
    # Energy: 150 * 0 + 0 * 0.18 = 0.0
    # Waste: 0 * 0.5 + 5 * 0.1 = 0.5
    # Total: 3.5 + 20.3 + 0 + 0.5 = 24.3
    assert data["breakdown"]["transport"] == 3.5
    assert data["breakdown"]["diet"] == 20.3
    assert data["breakdown"]["energy"] == 0.0
    assert data["breakdown"]["waste"] == 0.5
    assert data["total_co2_kg"] == 24.3

    # Savings:
    # Diet (already vegan): (7.2 - 2.9) * 7 = 30.1 (saved compared to meat heavy)
    # Transport (already train): (0.170 - 0.035) * 100 = 13.5 (saved compared to driving gasoline)
    assert data["savings"]["diet_saving_kg"] == 30.1
    assert data["savings"]["transport_saving_kg"] == 13.5

    # Check eco score and micro insight
    assert data["eco_score"] == 71
    assert "micro_insight" in data
    assert isinstance(data["micro_insight"], str)


def test_calculate_validation_errors(client):
    # Test invalid transport type
    payload = {
        "transport": {"transport_type": "rocket_ship", "distance_km": 100.0},
        "diet": {"diet_type": "vegan", "days": 1},
        "energy": {"electricity_kwh": 0, "electricity_type": "electricity_green", "gas_kwh": 0},
        "waste": {"unsorted_waste_kg": 0, "recycled_waste_kg": 0}
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 422
    
    # Test negative distance
    payload = {
        "transport": {"transport_type": "driving_gasoline", "distance_km": -5.0},
        "diet": {"diet_type": "vegan", "days": 1},
        "energy": {"electricity_kwh": 0, "electricity_type": "electricity_green", "gas_kwh": 0},
        "waste": {"unsorted_waste_kg": 0, "recycled_waste_kg": 0}
    }
    response = client.post("/api/calculate", json=payload)
    assert response.status_code == 422

def test_history_crud(client):
    # History starts empty
    response = client.get("/api/history")
    assert response.status_code == 200
    assert len(response.json()) == 0

    # Add an entry
    payload = {
        "transport": {"transport_type": "driving_gasoline", "distance_km": 10.0},
        "diet": {"diet_type": "vegan", "days": 1},
        "energy": {"electricity_kwh": 10.0, "electricity_type": "electricity_grid", "gas_kwh": 0.0},
        "waste": {"unsorted_waste_kg": 0.0, "recycled_waste_kg": 0.0}
    }
    res_post = client.post("/api/calculate", json=payload)
    assert res_post.status_code == 201
    assert "eco_score" in res_post.json()
    assert "micro_insight" in res_post.json()
    log_id = res_post.json()["id"]

    # History should have 1 entry
    response = client.get("/api/history")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["id"] == log_id

    # Delete non-existent ID
    res_del_fake = client.delete("/api/history/fake-id")
    assert res_del_fake.status_code == 404

    # Delete real ID
    res_del = client.delete(f"/api/history/{log_id}")
    assert res_del.status_code == 204

    # History should be empty again
    response = client.get("/api/history")
    assert len(response.json()) == 0

    # Test clear all
    client.post("/api/calculate", json=payload)
    client.post("/api/calculate", json=payload)
    assert len(client.get("/api/history").json()) == 2
    
    res_clear = client.delete("/api/history")
    assert res_clear.status_code == 204
    assert len(client.get("/api/history").json()) == 0
