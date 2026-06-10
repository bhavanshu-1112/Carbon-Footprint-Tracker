import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

@pytest.fixture
def mock_db(tmp_path):
    test_db = tmp_path / "database.json"
    test_db.write_text("""{
      "emission_factors": {
        "transport": {
          "driving_gasoline": 0.170,
          "driving_diesel": 0.171,
          "driving_electric": 0.050,
          "motorcycle": 0.100,
          "public_transit_bus": 0.089,
          "public_transit_train": 0.035,
          "flight_short_haul": 0.250,
          "flight_long_haul": 0.190,
          "walking_biking": 0.0
        },
        "diet": {
          "meat_heavy": 7.2,
          "average_meat": 5.6,
          "no_beef": 4.6,
          "vegetarian": 3.8,
          "vegan": 2.9
        },
        "energy": {
          "electricity_grid": 0.400,
          "electricity_green": 0.0,
          "natural_gas_kwh": 0.180
        },
        "waste": {
          "unsorted_waste_kg": 0.5,
          "recycled_waste_kg": 0.1
        }
      },
      "logs": []
    }""", encoding="utf-8")
    
    with patch("backend.main.DB_PATH", test_db):
        yield test_db

@pytest.fixture
def client(mock_db):
    from backend.main import app
    with TestClient(app) as c:
        yield c
