import json
from pathlib import Path
import yaml
from jsonschema import Draft7Validator

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "data" / "schema" / "case_schema.json"
CASES_DIR = ROOT / "data" / "cases"

def main():
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft7Validator(schema)

    errors_total = 0

    for path in sorted(CASES_DIR.glob("*.yaml")):
        case = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        errors = sorted(validator.iter_errors(case), key=lambda e: e.path)

        if errors:
            errors_total += len(errors)
            print(f"\n❌ {path.name}")
            for e in errors:
                loc = ".".join([str(x) for x in e.path]) or "(root)"
                print(f"  - {loc}: {e.message}")
        else:
            print(f"✅ {path.name}")

    if errors_total:
        raise SystemExit(f"\nValidation failed with {errors_total} error(s).")
    print("\nAll case files validated successfully.")

if __name__ == "__main__":
    main()
