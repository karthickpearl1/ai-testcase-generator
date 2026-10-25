"""The committed sample-output/ must match what the code generates today.

If a change to the rules or code generators is intentional, run `make sample` and review the
diff of the generated tests in the pull request, the same way you would review a snapshot.
"""

import json

from ai_testgen.config import load_config
from ai_testgen.pipeline import generate_artefacts


def test_sample_output_is_current(root, tmp_path):
    generate_artefacts(load_config(root / "testgen.yaml"), tmp_path)
    sample = root / "sample-output"
    assert json.loads((tmp_path / "cases.json").read_text()) == json.loads(
        (sample / "cases.json").read_text()
    )
    for relative in [
        *(p.relative_to(tmp_path) for p in (tmp_path / "tests").rglob("*") if p.is_file()),
        *(p.relative_to(tmp_path) for p in (tmp_path / "exports").rglob("*")),
    ]:
        assert (tmp_path / relative).read_text() == (sample / relative).read_text(), relative
