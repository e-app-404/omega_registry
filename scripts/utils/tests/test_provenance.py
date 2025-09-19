from scripts.utils import provenance


def test_compute_and_file_sha256(tmp_path):
    data = b"hello-provenance"
    h = provenance.compute_sha256_bytes(data)
    # write file
    p = tmp_path / "f.bin"
    p.write_bytes(data)
    hf = provenance.file_sha256(p)
    assert h == hf


def test_tz_now_iso_returns_iso():
    ts = provenance.tz_now_iso()
    # should be parseable by fromisoformat
    from datetime import datetime

    dt = datetime.fromisoformat(ts)
    assert dt.tzinfo is not None


def test_read_write_and_upsert_manifest(tmp_path, monkeypatch):
    mfile = tmp_path / "prov.json"
    # point env to temp manifest
    monkeypatch.setenv("OMEGA_PROVENANCE_MANIFEST", str(mfile))
    # ensure read on missing returns {}
    assert provenance.read_manifest() == {}
    # write a manifest
    manifest = {"/abs/path": {"sha256": "deadbeef"}}
    provenance.write_manifest(manifest)
    got = provenance.read_manifest()
    assert got.get("/abs/path", {}).get("sha256") == "deadbeef"
    # upsert another entry
    provenance.upsert_manifest_entry("/other", {"sha256": "cafebabe"})
    got2 = provenance.read_manifest()
    assert "/other" in got2
    assert got2["/other"]["sha256"] == "cafebabe"
