import json
from pathlib import Path

from scripts.generators.alpha_registry_writer import write_alpha_registry


def failing_validator(items, contract_path=None):
    # return a list of errors to trigger compliance report path
    return ["missing friendly_name on some items"]


def test_write_alpha_registry_integration(tmp_path, monkeypatch):
    # Arrange: create sample items and a temporary canonical dir
    items = [{"entity_id": "sensor.test_1", "platform": "mqtt"}]
    out_dir = tmp_path / "canonical"
    out_dir.mkdir()
    out_path = out_dir / "alpha_sensors.json"

    # Force provenance manifest into temp location
    prov_path = tmp_path / "omega_registry_master.provenance.json"
    monkeypatch.setenv("OMEGA_PROVENANCE_MANIFEST", str(prov_path))

    # Force compliance dir into temp location
    comp_dir = out_dir / "logs" / "audit" / "contract_compliance"
    monkeypatch.setenv("OMEGA_COMPLIANCE_DIR", str(comp_dir))

    # Act
    result = write_alpha_registry(
        domain="alpha_sensors",
        items=items,
        out_path=str(out_path),
        contract_path=None,
        validate_contract=failing_validator,
        write_output=True,
        strict=False,
    )

    # Assert: file written
    assert out_path.exists(), "Alpha registry output file should be written"

    # Assert: provenance manifest contains the path and matching sha256 (accept absolute or repo-relative keys)
    prov = json.loads(prov_path.read_text(encoding="utf-8"))
    abs_key = str(out_path)
    try:
        rel_key = str(Path(out_path).relative_to(Path.cwd()))
    except Exception:
        rel_key = None

    # Find whichever key the writer stored
    manifest_key = None
    for k in (rel_key, abs_key):
        if k and k in prov:
            manifest_key = k
            break
    assert manifest_key, (
        f"Provenance manifest should contain either {rel_key} or {abs_key}"
    )
    assert prov[manifest_key]["sha256"] == result["sha256"]

    # Assert: compliance report created
    reports = list(comp_dir.glob("*_compliance_*.json"))
    assert len(reports) >= 1, (
        "Compliance report file should be created when validator returns errors"
    )
    # Assert: provenance manifest entry includes compliance_report
    assert prov[manifest_key].get("compliance_report"), (
        "Provenance entry should include compliance_report path"
    )
