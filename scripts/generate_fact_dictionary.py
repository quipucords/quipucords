#!/usr/bin/env python3
"""
Generate a Discovery Facts Data Dictionary from the quipucords codebase.

Extracts fact definitions from scanner source files and renders them into
a Markdown reference. Standalone -- no Django boot required, only pyyaml.

Usage:
    python scripts/generate_fact_dictionary.py          # writes docs/fact-dictionary.md
    python scripts/generate_fact_dictionary.py --stdout  # prints to stdout
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent / "quipucords"


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class Fact:
    name: str
    source_type: str
    role: str = ""
    command: str = ""
    fingerprint_key: str = ""
    is_internal: bool = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _yaml_tasks(path: Path) -> list[dict]:
    """Load an Ansible tasks YAML file, returning an empty list on non-list data."""
    data = yaml.safe_load(path.read_text())
    if not isinstance(data, list):
        return []
    return data


def _find_node(
    tree: ast.Module, node_type: type, name: str,
) -> ast.AST | None:
    """Walk an AST and return the first node of *node_type* whose name matches."""
    for node in ast.walk(tree):
        if isinstance(node, node_type) and node.name == name:
            return node
    return None


def _resolve_fingerprint(name: str, source_fingerprint: dict[str, str]) -> dict[str, str]:
    """Find fingerprint mapping(s) for a fact name.

    Tries three strategies:
    1. Exact match (network, satellite, vcenter)
    2. Dot-to-underscore translation (openshift: node.name -> node__name)
    3. Prefix match for nested sub-keys (ansible: instance_details -> instance_details__*)
    """
    exact = name.replace(".", "__")
    for key in (name, exact):
        if key in source_fingerprint:
            return {key: source_fingerprint[key]}
    prefix = name + "__"
    return {rk: fk for rk, fk in source_fingerprint.items() if rk.startswith(prefix)}


def _extract_class_string_constants(path: Path, cls: str) -> dict[str, str]:
    """Return {ATTR: "value"} for string constants in a class.

    Finds assignments like ``CPU_COUNT = "vm.cpu_count"`` inside the class
    named *cls* and returns them as a dict. Only plain ``NAME = "literal"``
    assignments are captured; annotated or computed values are skipped.
    """
    tree = ast.parse(path.read_text())
    class_node = _find_node(tree, ast.ClassDef, cls)
    if class_node is None:
        return {}
    constants: dict[str, str] = {}
    for item in class_node.body:
        if not isinstance(item, ast.Assign):
            continue
        if not isinstance(item.value, ast.Constant):
            continue
        if not isinstance(item.value.value, str):
            continue
        for target in item.targets:
            if isinstance(target, ast.Name):
                constants[target.id] = item.value.value
    return constants


def _extract_tuple_strings(path: Path, var_hint: str) -> list[str]:
    """Return list of strings from a tuple assignment like `x = ("a","b")`."""
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and var_hint in t.id:
                    if isinstance(node.value, ast.Tuple):
                        return [
                            e.value for e in node.value.elts
                            if isinstance(e, ast.Constant)
                        ]
    return []


def _extract_dict_literal(path: Path, var_name: str) -> dict[str, str]:
    """Return {k: v} from a simple dict literal assignment."""
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == var_name:
                    if isinstance(node.value, ast.Dict):
                        return {
                            k.value: v.value
                            for k, v in zip(node.value.keys, node.value.values)
                            if isinstance(k, ast.Constant)
                            and isinstance(v, ast.Constant)
                        }
    return {}


# ---------------------------------------------------------------------------
# Extractors (one per source type)
# ---------------------------------------------------------------------------


def extract_network() -> list[Fact]:
    """Parse Ansible role YAML to get fact names + shell commands."""
    facts = []
    roles_dir = ROOT / "scanner/network/runner/roles"
    # Ansible tasks commonly prepend locale exports; strip them for readability
    locale_prefix = re.compile(r"^export\s+LANG=C\s+LC_ALL=C;\s*")

    for role_dir in sorted(roles_dir.iterdir()):
        tasks_file = role_dir / "tasks/main.yml"
        if not tasks_file.exists():
            continue
        role = role_dir.name
        last_cmd = ""
        for task in _yaml_tasks(tasks_file):
            if not isinstance(task, dict):
                continue
            if "raw" in task:
                last_cmd = locale_prefix.sub("", task["raw"].strip())
            if "set_fact" in task and isinstance(task["set_fact"], dict):
                for name in task["set_fact"]:
                    if name == "internal_host_started_processing_role":
                        continue
                    is_internal = name.startswith("internal_")
                    facts.append(Fact(name, "network", role, last_cmd, is_internal=is_internal))
                    if not is_internal:
                        last_cmd = ""

    seen: dict[str, Fact] = {}
    for fact in facts:
        if fact.name not in seen or (not seen[fact.name].command and fact.command):
            seen[fact.name] = fact
    return list(seen.values())


def extract_satellite() -> list[Fact]:
    satellite_dir = ROOT / "scanner/satellite"
    names = _extract_tuple_strings(satellite_dir / "utils.py", "satellite_raw_facts")

    mapping_vars = (
        "FIELDS_MAPPING", "FACTS_MAPPING", "SUBS_FACET_MAPPING",
        "CONTENT_FACET_MAPPING", "VIRTUAL_HOST_MAPPING", "ERRATA_MAPPING",
    )
    api_map: dict[str, str] = {}
    for var in mapping_vars:
        for qpc_key, sat_key in _extract_dict_literal(satellite_dir / "six.py", var).items():
            api_map[qpc_key] = f"Satellite API: {var} -> {sat_key}"

    all_names = list(dict.fromkeys(names + list(api_map.keys())))
    return [
        Fact(name, "satellite", "satellite", api_map.get(name, "Satellite API"))
        for name in all_names
    ]


def extract_vcenter() -> list[Fact]:
    vcenter_utils = ROOT / "scanner/vcenter/utils.py"
    class_to_entity = (
        ("VcenterRawFacts", "vm"),
        ("HostRawFacts", "host"),
        ("ClusterRawFacts", "cluster"),
    )
    facts = []
    for cls, entity in class_to_entity:
        constants = _extract_class_string_constants(vcenter_utils, cls)
        for fact_name in sorted(constants.values()):
            facts.append(Fact(fact_name, "vcenter", f"vcenter/{entity}", f"pyVmomi ({entity})"))
    return facts


def extract_openshift() -> list[Fact]:
    entities_path = ROOT / "scanner/openshift/entities.py"
    tree = ast.parse(entities_path.read_text())

    pydantic_models = (
        ("OCPCluster", "cluster", "OCP API: cluster"),
        ("OCPNode", "node", "OCP API: nodes"),
        ("OCPWorkload", "workload", "OCP API: workloads"),
    )
    # Pydantic internals, not scannable facts
    skip_fields = {"kind", "errors"}

    facts = []
    for cls, kind, api in pydantic_models:
        class_node = _find_node(tree, ast.ClassDef, cls)
        if class_node is None:
            continue
        for item in class_node.body:
            if not isinstance(item, ast.AnnAssign):
                continue
            if not isinstance(item.target, ast.Name):
                continue
            field_name = item.target.id
            if not field_name.startswith("_") and field_name not in skip_fields:
                facts.append(Fact(f"{kind}.{field_name}", "openshift", f"openshift/{kind}", api))

    for extra in ("workloads", "operators", "rhacm_metrics"):
        facts.append(Fact(extra, "openshift", "openshift/cluster", "OCP API: aggregate"))
    return facts


def extract_ansible() -> list[Fact]:
    """Hardcoded -- AAP stores facts as top-level dict keys, not parseable structures."""
    return [
        Fact("instance_details", "ansible", "ansible", "AAP API: /api/v2/ (ping + me)"),
        Fact("hosts", "ansible", "ansible", "AAP API: /api/v2/hosts/"),
        Fact("jobs", "ansible", "ansible", "AAP API: /api/v2/jobs/ or host_metrics"),
        Fact("comparison", "ansible", "ansible", "(computed)"),
    ]


def extract_rhacs() -> list[Fact]:
    """Hardcoded -- RHACS stores facts as top-level dict keys, not parseable structures."""
    return [
        Fact("secured_units_current", "rhacs", "rhacs", "RHACS API: /v1/.../secured-units/current"),
        Fact("secured_units_max", "rhacs", "rhacs", "RHACS API: /v1/.../secured-units/max"),
    ]


# ---------------------------------------------------------------------------
# Fingerprint mappings
# ---------------------------------------------------------------------------


def extract_fingerprint_mappings() -> dict[str, dict[str, str]]:
    """Parse fingerprinter/runner.py to build {source: {raw_key: fingerprint_key}}."""
    runner_path = ROOT / "fingerprinter/runner.py"
    tree = ast.parse(runner_path.read_text())
    result: dict[str, dict[str, str]] = {}

    method_to_source = {
        "_process_network_fact": "network",
        "_process_vcenter_fact": "vcenter",
        "_process_satellite_fact": "satellite",
        "_process_openshift_fact": "openshift",
        "_process_ansible_fact": "ansible",
        "_process_rhacs_fact": "rhacs",
    }

    for method_name, source in method_to_source.items():
        func_node = _find_node(tree, ast.FunctionDef, method_name)
        if func_node is None:
            continue
        mappings: dict[str, str] = {}

        for child in ast.walk(func_node):
            # Pattern 1: batch mapping lists like [(raw_key, fp_key, formatter), ...]
            if (isinstance(child, ast.List)
                    and child.elts
                    and isinstance(child.elts[0], ast.Tuple)):
                for elt in child.elts:
                    if not isinstance(elt, ast.Tuple) or len(elt.elts) < 2:
                        continue
                    raw_key, fingerprint_key = elt.elts[0], elt.elts[1]
                    if isinstance(raw_key, ast.Constant) and isinstance(fingerprint_key, ast.Constant):
                        mappings[raw_key.value] = fingerprint_key.value

            # Pattern 2: self._add_fact_to_fingerprint(source, raw_key, fact, fp_key, fingerprint)
            if (isinstance(child, ast.Call)
                    and isinstance(child.func, ast.Attribute)
                    and child.func.attr == "_add_fact_to_fingerprint"
                    and len(child.args) >= 5):
                raw_key, fingerprint_key = child.args[1], child.args[3]
                if isinstance(raw_key, ast.Constant) and isinstance(fingerprint_key, ast.Constant):
                    mappings[raw_key.value] = fingerprint_key.value

        result[source] = mappings
    return result


# ---------------------------------------------------------------------------
# Markdown renderer
# ---------------------------------------------------------------------------


def _format_fingerprint(mapping: dict[str, str]) -> str:
    """Format a fingerprint mapping dict for display in Markdown."""
    if not mapping:
        return ""
    if len(mapping) == 1:
        return next(iter(mapping.values()))
    return ", ".join(
        f"{raw_key} -> {fingerprint_key}"
        for raw_key, fingerprint_key in sorted(mapping.items())
    )


def _sanitize_command(command: str, fallback: str = "_(post-processed)_") -> str:
    """Escape and truncate a command string for safe Markdown table display."""
    cmd = (command or fallback).replace("|", "\\|").replace("\n", " ")
    if len(cmd) > 80:
        cmd = cmd[:77] + "..."
    return cmd


def render_markdown(
    all_facts: dict[str, list[Fact]],
    fingerprint_map: dict[str, dict[str, str]],
) -> str:
    lines = [
        "# Discovery Facts Data Dictionary\n",
        "> **Auto-generated** from the quipucords source code by",
        "> `scripts/generate_fact_dictionary.py`. Do not edit manually.\n",
    ]

    labels = {
        "network": "Network (SSH/Ansible)",
        "satellite": "Satellite",
        "vcenter": "vCenter",
        "openshift": "OpenShift (OCP)",
        "ansible": "Ansible Automation Platform (AAP)",
        "rhacs": "Red Hat Advanced Cluster Security (RHACS)",
    }

    for source, facts in all_facts.items():
        label = labels.get(source, source)
        source_fingerprint = fingerprint_map.get(source, {})
        public = sorted(
            (fact for fact in facts if not fact.is_internal),
            key=lambda fact: (fact.role, fact.name),
        )
        internal = sorted(
            (fact for fact in facts if fact.is_internal),
            key=lambda fact: (fact.role, fact.name),
        )

        lines.append(f"## {label}\n")
        lines.append("| Raw Fact | Role | Collection Method | Fingerprint Fact |")
        lines.append("|----------|------|-------------------|-----------------|")
        for fact in public:
            cmd = _sanitize_command(fact.command)
            fingerprint_display = _format_fingerprint(
                _resolve_fingerprint(fact.name, source_fingerprint)
            )
            lines.append(f"| `{fact.name}` | {fact.role} | `{cmd}` | {fingerprint_display} |")
        lines.append("")

        if internal:
            lines.append(f"<details><summary>{len(internal)} internal/dependency facts</summary>\n")
            lines.append("| Fact | Role | Command |")
            lines.append("|------|------|---------|")
            for fact in internal:
                cmd = _sanitize_command(fact.command, fallback="_(computed)_")
                lines.append(f"| `{fact.name}` | {fact.role} | `{cmd}` |")
            lines.append("\n</details>\n")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    all_facts = {
        "network": extract_network(),
        "satellite": extract_satellite(),
        "vcenter": extract_vcenter(),
        "openshift": extract_openshift(),
        "ansible": extract_ansible(),
        "rhacs": extract_rhacs(),
    }
    fingerprint_map = extract_fingerprint_mappings()

    for src, facts in all_facts.items():
        source_fingerprint = fingerprint_map.get(src, {})
        for fact in facts:
            fact.fingerprint_key = _format_fingerprint(
                _resolve_fingerprint(fact.name, source_fingerprint)
            )

    md = render_markdown(all_facts, fingerprint_map)

    if "--stdout" in sys.argv:
        print(md)
    else:
        out = Path(__file__).resolve().parent.parent / "docs" / "fact-dictionary.md"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md)
        total = sum(len(facts) for facts in all_facts.values())
        fp_count = sum(len(m) for m in fingerprint_map.values())
        print(f"Generated {out} ({total} facts, {fp_count} fingerprint mappings)")


if __name__ == "__main__":
    main()
