from __future__ import annotations

import yaml

from dbt_data_engineering_toolkit_compiler.brokers.files import LocalFileBroker
from dbt_data_engineering_toolkit_compiler.prove import ProjectProofService


def test_local_package_root_resolves_repo_layout_to_project_directories(tmp_path) -> None:
    repo = tmp_path / "repo"
    canonical = repo / "dbt"
    alias = repo / "aliases" / "de_toolkit"
    canonical.mkdir(parents=True)
    alias.mkdir(parents=True)
    (canonical / "dbt_project.yml").write_text("name: dbt_data_engineering_toolkit\n")
    (alias / "dbt_project.yml").write_text("name: de_toolkit\n")

    project = repo / "generated"
    project.mkdir()

    ProjectProofService(files=LocalFileBroker())._use_local_packages(project, repo)

    payload = yaml.safe_load((project / "packages.yml").read_text(encoding="utf-8"))
    assert payload["packages"][0]["local"] == str(canonical)
    assert payload["packages"][1]["local"] == str(alias)
