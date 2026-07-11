from pathlib import Path


def test_production_code_does_not_import_backup_files():
    roots = [Path("app"), Path("tests"), Path("scripts")]
    backup_suffix = "." + "backup"
    backup_module = "agent_orchestrator" + backup_suffix
    offenders = []

    for root in roots:
        for path in root.rglob("*.py"):
            if backup_suffix in path.name:
                continue

            text = path.read_text(encoding="utf-8")
            if backup_suffix in text or backup_module in text:
                offenders.append(str(path))

    assert offenders == []
