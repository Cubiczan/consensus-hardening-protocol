"""Refusal-rule suite for the canonical evidence-matrix verifier.

Each refusal rule from the spec gets its own test with a tiny temp repo built
by the ``make_repo`` fixture: the verifier must refuse (exit 1) or refuse as
unusable (exit 2) with a reason line, and the happy path must exit 0 with the
exact ``EVIDENCE MATRIX: VERIFIED (n/n)`` closing line.

The purity guard pins the stdlib-only contract: the canonical verifier file
imports no urllib/requests/socket.
"""
import ast
import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CANONICAL_VERIFIER = REPO_ROOT / "tools" / "verify_evidence_matrix.py"
SEED_CSV_BYTES = b"a,b\n1,2\n"
SEED_CSV_SHA = hashlib.sha256(SEED_CSV_BYTES).hexdigest()


def run_verifier(repo_root, *extra):
    return subprocess.run(
        [sys.executable, str(CANONICAL_VERIFIER), "--repo-root", str(repo_root), *extra],
        capture_output=True,
        text=True,
        timeout=60,
    )


def write(repo: Path, relpath: str, content: str, executable: bool = False) -> Path:
    path = repo / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    if executable:
        path.chmod(0o755)
    return path


GOOD_TEST = "def test_qoq_diff():\n    assert True\n"
GOOD_SCRIPT = '#!/bin/sh\necho "verifying..."\nexit 0\n'
GOOD_MANIFEST = (
    '{"claims": {"parameters": {"scoring_weights": '
    '{"hubspot_weight": 0.4, "npi_weight": 0.6}}}}\n'
)


def GOOD_MATRIX(**overrides):
    """A matrix where every row verifies against the good fixture repo."""
    matrix = f'''schema_version: 1
repo: fixture-repo
claims:
  - id: C001
    claim: >-
      Quarter-over-quarter position diffs across funds with cross-fund consensus scoring.
    source: "README.md#features"
    evidence:
      - type: test
        ref: "tests/test_core.py::test_qoq_diff"
      - type: script
        ref: "scripts/verify_consensus_math.sh"
        timeout_seconds: 30
  - id: C002
    claim: "Published manifest records sources, weights and row counts."
    source: "README.md#architecture"
    evidence:
      - type: manifest_field
        ref: "manifest.json:claims.parameters.scoring_weights"
        equals: {{ hubspot_weight: 0.4, npi_weight: 0.6 }}
  - id: C003
    claim: "Frozen seed dataset used for deterministic scoring."
    source: "README.md#data"
    evidence:
      - type: artifact_hash
        ref: "data/seed.csv"
        sha256: "{SEED_CSV_SHA}"
'''
    for old, new in overrides.items():
        matrix = matrix.replace(old, new)
    return matrix


def RUNNER_MATRIX():
    """Baseline plus a C004 row whose test ref is runner-prefixed (cargo-test)."""
    return GOOD_MATRIX() + '''  - id: C004
    claim: "Rust engine implements cross-fund consensus."
    source: "README.md#architecture"
    evidence:
      - type: test
        ref: "cargo-test:consensus"
'''


@pytest.fixture
def make_repo(tmp_path):
    def _make(matrix: str) -> Path:
        repo = tmp_path / "repo"
        repo.mkdir()
        write(repo, "README.md", "# fixture repo\n\n## Features\n\nClaim one.\n\n## Architecture\n\nClaim two.\n\n## Data\n\nClaim three.\n")
        write(repo, "tests/test_core.py", GOOD_TEST)
        write(repo, "scripts/verify_consensus_math.sh", GOOD_SCRIPT, executable=True)
        write(repo, "manifest.json", GOOD_MANIFEST)
        write(repo, "data/seed.csv", SEED_CSV_BYTES.decode())
        write(repo, "evidence/matrix.yaml", matrix)
        return repo

    return _make


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_happy_path_verifies(make_repo):
    repo = make_repo(GOOD_MATRIX())
    proc = run_verifier(repo)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert proc.stdout.rstrip().endswith("EVIDENCE MATRIX: VERIFIED (3/3)")
    # one verdict line per evidence ref
    assert proc.stdout.count("->  PASS") == 4
    assert "FAIL" not in proc.stdout


# ---------------------------------------------------------------------------
# Refusal rules — exit 1 with a reason, collected rather than first-stop
# ---------------------------------------------------------------------------

def test_tampered_hash_refuses(make_repo):
    repo = make_repo(GOOD_MATRIX())
    (repo / "data/seed.csv").write_text("a,b\n1,9999\n")  # bytes changed, pin unchanged
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "EVIDENCE MATRIX: FAILED (1 of 3 unverified)" in proc.stdout
    assert "artifact hash mismatch" in proc.stdout


def test_unknown_evidence_type_refuses(make_repo):
    repo = make_repo(GOOD_MATRIX(**{"type: test": "type: seance"}))
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "unknown evidence type" in proc.stdout


def test_missing_test_file_refuses(make_repo):
    repo = make_repo(GOOD_MATRIX())
    (repo / "tests/test_core.py").unlink()
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "test file not found in tree: tests/test_core.py" in proc.stdout


def test_missing_test_node_refuses(make_repo):
    repo = make_repo(GOOD_MATRIX())
    write(repo, "tests/test_core.py", "def test_renamed_diff():\n    assert True\n")
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "test node not found in tests/test_core.py: test_qoq_diff" in proc.stdout


def test_unknown_test_runner_refuses(make_repo):
    repo = make_repo(RUNNER_MATRIX().replace("cargo-test:", "carg-test:"))
    write(repo, "Cargo.toml", '[package]\nname = "x"\nversion = "0.1.0"\n')
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "unknown test runner prefix" in proc.stdout


def test_runner_manifest_required(make_repo):
    repo = make_repo(RUNNER_MATRIX())
    # no Cargo.toml anywhere in the tree
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "cargo-test ref requires Cargo.toml" in proc.stdout
    # with the manifest present the same ref verifies
    write(repo, "Cargo.toml", '[package]\nname = "x"\nversion = "0.1.0"\n')
    proc = run_verifier(repo)
    assert proc.returncode == 0, proc.stdout
    assert proc.stdout.rstrip().endswith("EVIDENCE MATRIX: VERIFIED (4/4)")


def test_empty_evidence_row_refuses(make_repo):
    # strip both of C001's evidence entries -> evidence: null
    repo = make_repo(GOOD_MATRIX(**{
        '      - type: test\n        ref: "tests/test_core.py::test_qoq_diff"\n': "",
        '      - type: script\n        ref: "scripts/verify_consensus_math.sh"\n        timeout_seconds: 30\n': "",
    }))
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "zero-evidence row" in proc.stdout


def test_duplicate_claim_id_refuses(make_repo):
    repo = make_repo(GOOD_MATRIX(**{"id: C003": "id: C001"}))
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "duplicate claim id: C001" in proc.stdout


def test_manifest_field_mismatch_refuses(make_repo):
    repo = make_repo(GOOD_MATRIX(**{"hubspot_weight: 0.4": "hubspot_weight: 0.9"}))
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "manifest field mismatch" in proc.stdout


def test_manifest_dotted_path_missing_refuses(make_repo):
    repo = make_repo(
        GOOD_MATRIX(**{"manifest.json:claims.parameters.scoring_weights": "manifest.json:claims.parameters.missing_key"})
    )
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "dotted path not found" in proc.stdout


def test_nonexistent_source_locator_refuses(make_repo):
    repo = make_repo(GOOD_MATRIX(**{"README.md#data": "docs/deleted.md#data"}))
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "source locator points at a file that does not exist: docs/deleted.md" in proc.stdout


def test_all_failures_collected_not_first_stop(make_repo):
    # two broken rows -> both reasons printed in the same run
    repo = make_repo(GOOD_MATRIX(**{
        "sha256: \"" + SEED_CSV_SHA + "\"": "sha256: \"" + "0" * 64 + "\"",
        "README.md#architecture": "docs/deleted.md#architecture",
    }))
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "artifact hash mismatch" in proc.stdout
    assert "source locator points at a file that does not exist" in proc.stdout
    assert "EVIDENCE MATRIX: FAILED (2 of 3 unverified)" in proc.stdout


def test_zero_claims_matrix_refuses(make_repo):
    repo = make_repo("schema_version: 1\nrepo: fixture-repo\nclaims: []\n")
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "matrix declares no claims" in proc.stdout
    assert "EVIDENCE MATRIX: FAILED (0 of 0 unverified)" in proc.stdout


def test_unknown_top_level_field_refuses(make_repo):
    repo = make_repo(GOOD_MATRIX(**{"repo: fixture-repo": "repo: fixture-repo\nclaimz: []"}))
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "unknown top-level field(s): claimz" in proc.stdout


def test_missing_matrix_is_unusable(tmp_path):
    proc = run_verifier(tmp_path)
    assert proc.returncode == 2
    assert "no evidence matrix found" in proc.stderr


def test_malformed_yaml_is_unusable(make_repo):
    repo = make_repo("claims: [unclosed\n  bad: : :\n")
    proc = run_verifier(repo)
    assert proc.returncode == 2
    assert "malformed YAML" in proc.stderr


def test_schema_version_bump_is_unusable(make_repo):
    repo = make_repo(GOOD_MATRIX(**{"schema_version: 1": "schema_version: 2"}))
    proc = run_verifier(repo)
    assert proc.returncode == 2
    assert "unsupported schema_version 2" in proc.stderr


def test_schema_version_missing_is_unusable(make_repo):
    repo = make_repo(GOOD_MATRIX(**{"schema_version: 1\n": ""}))
    proc = run_verifier(repo)
    assert proc.returncode == 2
    assert "schema_version" in proc.stderr


def test_script_must_exit_zero(make_repo):
    repo = make_repo(GOOD_MATRIX())
    write(repo, "scripts/verify_consensus_math.sh", '#!/bin/sh\necho "boom" >&2\nexit 3\n', executable=True)
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "script exited 3" in proc.stdout
    assert "boom" in proc.stdout


def test_script_must_be_executable(make_repo):
    repo = make_repo(GOOD_MATRIX())
    (repo / "scripts/verify_consensus_math.sh").chmod(0o644)
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "not executable" in proc.stdout


def test_script_timeout_is_enforced(make_repo):
    repo = make_repo(GOOD_MATRIX())
    write(repo, "scripts/verify_consensus_math.sh", "#!/bin/sh\nsleep 30\n", executable=True)
    # replace the per-row timeout with 1s so the suite stays fast
    matrix = (repo / "evidence/matrix.yaml").read_text().replace("timeout_seconds: 30", "timeout_seconds: 1")
    (repo / "evidence/matrix.yaml").write_text(matrix)
    proc = run_verifier(repo)
    assert proc.returncode == 1
    assert "timed out after 1s" in proc.stdout


def test_script_default_timeout_is_120s():
    from pathlib import Path as _P
    src = CANONICAL_VERIFIER.read_text(encoding="utf-8")
    assert "DEFAULT_SCRIPT_TIMEOUT_SECONDS = 120" in src


# ---------------------------------------------------------------------------
# Fallback YAML parser — must agree with PyYAML on schema-v1 files
# ---------------------------------------------------------------------------

def _load_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("vem", CANONICAL_VERIFIER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fallback_parser_matches_pyyaml_on_schema_v1_matrix(make_repo):
    module = _load_module()
    matrix_text = GOOD_MATRIX()
    try:
        import yaml  # noqa: F401

        pyyaml_doc = yaml.safe_load(matrix_text)
    except ImportError:
        pytest.skip("PyYAML not installed — fallback is the only parser")
    fallback_doc = module.parse_yaml_subset(matrix_text)
    assert fallback_doc == pyyaml_doc


def test_fallback_parser_handles_block_scalars_flow_and_lists():
    module = _load_module()
    text = (
        "# comment line\n"
        "schema_version: 1\n"
        "repo: \"x-repo\"\n"
        "claims:\n"
        "  - id: C001\n"
        "    claim: >-\n"
        "      folded claim text\n"
        "      across two lines.\n"
        "    source: README.md#features\n"
        "    evidence:\n"
        "      - type: manifest_field\n"
        "        ref: \"manifest.json:a.b\"\n"
        "        equals: { hubspot_weight: 0.4, npi_weight: 0.6 }\n"
        "      - type: artifact_hash\n"
        "        ref: data/seed.csv\n"
        "        sha256: \"" + SEED_CSV_SHA + "\"\n"
    )
    doc = module.parse_yaml_subset(text)
    assert doc["schema_version"] == 1
    assert doc["repo"] == "x-repo"
    assert len(doc["claims"]) == 1
    claim = doc["claims"][0]
    assert claim["id"] == "C001"
    assert claim["claim"] == "folded claim text across two lines."  # >- strips the newline
    assert claim["evidence"][0]["equals"] == {"hubspot_weight": 0.4, "npi_weight": 0.6}
    assert claim["evidence"][1]["sha256"] == SEED_CSV_SHA


def test_fallback_refuses_tab_indentation():
    module = _load_module()
    with pytest.raises(module.YamlSubsetError):
        module.parse_yaml_subset("claims:\n\t- id: C001\n")


# ---------------------------------------------------------------------------
# Purity + stamp contract on the canonical file itself
# ---------------------------------------------------------------------------

def test_verifier_is_stdlib_pure_no_network_imports():
    tree = ast.parse(CANONICAL_VERIFIER.read_text(encoding="utf-8"))
    forbidden = {"urllib", "requests", "socket"}
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    offenders = sorted(imported & forbidden)
    assert not offenders, f"network imports found in canonical verifier: {offenders}"


def test_verifier_carries_version_stamp_and_canonical_commit():
    src = CANONICAL_VERIFIER.read_text(encoding="utf-8")
    assert 'EVIDENCE_MATRIX_VERIFIER_VERSION = "1.0.0"' in src
    assert "Canonical kit commit:" in src
    assert "icohangar-ops/consensus-hardening-protocol" in src


def test_verifier_has_no_skip_flags_or_quiet_modes():
    src = CANONICAL_VERIFIER.read_text(encoding="utf-8")
    for banned in ("--skip", "--quiet", "--allowlist", "--no-verify", "--warn-only"):
        assert banned not in src
