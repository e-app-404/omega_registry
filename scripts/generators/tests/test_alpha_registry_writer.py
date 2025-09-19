from pathlib import Path

from scripts.generators.alpha_registry_writer import write_alpha_registry


def test_write_alpha_registry_happy_path(tmp_path: Path):
    items = [
        {
            "entity_id": "sensor.test",
            "platform": "test",
            "device_id": "dev1",
            "area_id": "area1",
        }
    ]
    out_file = tmp_path / "alpha_sensor.json"
    res = write_alpha_registry("sensor", items, out_file, write_output=False)
    assert res["domain"] == "sensor"
    assert res["count"] == 1
    assert "sha256" in res
    assert res["written"] is False


def test_write_alpha_registry_validation_strict(tmp_path: Path):
    # Validator that returns an error for missing friendly_name
    def failing_validator(entities, contract_path=None):
        errors = []
        for e in entities:
            if "friendly_name" not in e:
                errors.append("missing friendly_name")
        return errors

    items = [
        {
            "entity_id": "sensor.test",
            "platform": "test",
            "device_id": "dev1",
            "area_id": "area1",
        }
    ]
    out_file = tmp_path / "alpha_sensor.json"
    # non-strict should not raise but should report errors
    res = write_alpha_registry(
        "sensor",
        items,
        out_file,
        validate_contract=failing_validator,
        write_output=False,
        strict=False,
    )
    assert res["errors"] == ["missing friendly_name"]

    # strict mode should raise
    try:
        write_alpha_registry(
            "sensor",
            items,
            out_file,
            validate_contract=failing_validator,
            write_output=False,
            strict=True,
        )
        raised = False
    except RuntimeError:
        raised = True
    assert raised
