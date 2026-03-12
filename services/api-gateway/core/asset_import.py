"""
Parsers for dependency files and SBOM formats.
Extracts package name + version for asset import.
"""
from __future__ import annotations

import json
import re
from typing import Any

# Supported formats and their typical extensions
SUPPORTED_EXTENSIONS = {
    "package-lock.json",
    "package.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "pipfile",
    "pipfile.lock",
    "gemfile",
    "gemfile.lock",
    "composer.json",
    "composer.lock",
    "pom.xml",
    "build.gradle",
    "pubspec.yaml",
    "package.swift",
    "package.resolved",
    "Cargo.toml",
    "Cargo.lock",
    "go.sum",
    "bom.json",
    "sbom.json",
    ".cyclonedx.json",
    ".spdx.json",
}


def _normalize_name(name: str) -> str:
    """Normalize package name for deduplication."""
    return name.strip().lower() if name else ""


def _safe_str(v: Any) -> str:
    return str(v).strip() if v is not None else ""


def parse_package_lock(content: str, filename: str = "package-lock.json") -> list[dict[str, str]]:
    """Parse npm package-lock.json. Extracts direct and transitive deps."""
    data = json.loads(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    packages = data.get("packages") or {}
    # packages: {"": {...}, "node_modules/foo": {...}, "node_modules/foo/node_modules/bar": {...}}
    for path, pkg in packages.items():
        if not isinstance(pkg, dict):
            continue
        name = pkg.get("name")
        if not name or path == "":
            continue
        version = _safe_str(pkg.get("version"))
        key = f"{_normalize_name(name)}@{version}" if version else _normalize_name(name)
        if key in seen:
            continue
        seen.add(key)
        result.append({"name": name.strip(), "version": version or None, "source_file": filename})
    # Fallback for lockfileVersion 1 (packages as array)
    if not result and "dependencies" in data:
        _collect_npm_deps(data.get("dependencies") or {}, result, seen, filename)
    return result


def _collect_npm_deps(
    deps: dict[str, Any],
    result: list[dict[str, str]],
    seen: set[str],
    filename: str,
    depth: int = 0,
) -> None:
    """Recursively collect from npm v1 lockfile structure."""
    if depth > 20:
        return
    for name, spec in deps.items():
        if not isinstance(spec, dict):
            continue
        pkg_name = spec.get("version") or name
        version = _safe_str(spec.get("version", ""))
        key = f"{_normalize_name(name)}@{version}" if version else _normalize_name(name)
        if key not in seen:
            seen.add(key)
            result.append({"name": name.strip(), "version": version or None, "source_file": filename})
        _collect_npm_deps(spec.get("dependencies") or {}, result, seen, filename, depth + 1)


def parse_package_json(content: str, filename: str = "package.json") -> list[dict[str, str]]:
    """Parse package.json dependencies and devDependencies."""
    data = json.loads(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for key in ("dependencies", "devDependencies", "peerDependencies", "optionalDependencies"):
        deps = data.get(key)
        if not isinstance(deps, dict):
            continue
        for name, ver_spec in deps.items():
            if not name or not isinstance(ver_spec, str):
                continue
            # Strip range: ^1.2.3 -> 1.2.3, ~2.0.0 -> 2.0.0
            version = _strip_version_spec(ver_spec)
            nkey = _normalize_name(name)
            if nkey in seen:
                continue
            seen.add(nkey)
            result.append({"name": name.strip(), "version": version, "source_file": filename})
    return result


def _strip_version_spec(spec: str) -> str | None:
    """Extract base version from semver spec if possible."""
    spec = spec.strip()
    if not spec or spec.startswith("file:") or spec.startswith("link:"):
        return None
    # Remove ^ ~ >= <=
    m = re.match(r"^[\^~>=<]*\s*([\d.]+[\w.-]*)", spec)
    return m.group(1) if m else (spec if re.match(r"^[\d.]", spec) else None)


def parse_requirements_txt(content: str, filename: str = "requirements.txt") -> list[dict[str, str]]:
    """Parse requirements.txt. Handles package==1.0, package>=1.0, -r other.txt."""
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for line in content.splitlines():
        line = line.split("#")[0].strip()
        if not line or line.startswith("-") or line.startswith("["):
            continue
        # package==1.0.0 or package>=1.0 or package
        m = re.match(r"^([a-zA-Z0-9_-]+)\s*([=<>!~]+)\s*([\w.]+)", line)
        if m:
            name, op, ver = m.group(1), m.group(2), m.group(3)
            version = ver if "==" in op else None
        else:
            m2 = re.match(r"^([a-zA-Z0-9_-]+)", line)
            if m2:
                name, version = m2.group(1), None
            else:
                continue
        nkey = _normalize_name(name)
        if nkey in seen:
            continue
        seen.add(nkey)
        result.append({"name": name.strip(), "version": version, "source_file": filename})
    return result


def _load_toml(content: str) -> dict:
    """Load TOML; use tomllib (3.11+) or tomli."""
    try:
        import tomllib
        return tomllib.loads(content)
    except ImportError:
        import tomli as t
        return t.loads(content)


def parse_pyproject_toml(content: str, filename: str = "pyproject.toml") -> list[dict[str, str]]:
    """Parse pyproject.toml [project.dependencies] or [tool.poetry.dependencies]."""
    data = _load_toml(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    # PEP 621
    project = data.get("project") or {}
    deps = project.get("dependencies") or []
    for dep in deps if isinstance(deps, list) else []:
        if isinstance(dep, str):
            name, version = _parse_pep508_dep(dep)
            if name and _normalize_name(name) not in seen:
                seen.add(_normalize_name(name))
                result.append({"name": name, "version": version, "source_file": filename})
    # Poetry [tool.poetry.dependencies]
    poetry = data.get("tool", {}).get("poetry", {})
    for key in ("dependencies", "dev-dependencies"):
        pdeps = poetry.get(key)
        if not isinstance(pdeps, dict):
            continue
        for name, spec in pdeps.items():
            if name in ("python",) or not isinstance(spec, (str, dict)):
                continue
            version = spec.get("version", spec) if isinstance(spec, dict) else spec
            version = _strip_version_spec(str(version)) if version else None
            nkey = _normalize_name(name)
            if nkey not in seen:
                seen.add(nkey)
                result.append({"name": name.strip(), "version": version, "source_file": filename})
    return result


def _parse_pep508_dep(dep: str) -> tuple[str, str | None]:
    """Parse PEP 508 dependency string: 'package>=1.0' -> (package, 1.0)."""
    m = re.match(r"^([a-zA-Z0-9_-]+)\s*([\[=<>!~].*)?$", dep.strip())
    if not m:
        return ("", None)
    name = m.group(1)
    rest = (m.group(2) or "").strip()
    version = None
    if rest and rest[0] in "=<>!~":
        vm = re.search(r"([\d.]+[\w.-]*)", rest)
        version = vm.group(1) if vm else None
    return (name, version)


def parse_poetry_lock(content: str, filename: str = "poetry.lock") -> list[dict[str, str]]:
    """Parse poetry.lock [[package]] sections."""
    data = _load_toml(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for pkg in data.get("package", []) or []:
        if not isinstance(pkg, dict):
            continue
        name = pkg.get("name")
        if not name:
            continue
        version = _safe_str(pkg.get("version"))
        nkey = f"{_normalize_name(name)}@{version}" if version else _normalize_name(name)
        if nkey not in seen:
            seen.add(nkey)
            result.append({"name": name.strip(), "version": version or None, "source_file": filename})
    return result


def parse_cargo_toml(content: str, filename: str = "Cargo.toml") -> list[dict[str, str]]:
    """Parse Cargo.toml [dependencies] and [dev-dependencies]."""
    data = _load_toml(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for key in ("dependencies", "dev-dependencies", "build-dependencies"):
        deps = data.get(key)
        if not isinstance(deps, dict):
            continue
        for name, spec in deps.items():
            if not name:
                continue
            version = None
            if isinstance(spec, str):
                version = _strip_version_spec(spec) if not spec.startswith("{") else None
            elif isinstance(spec, dict):
                version = _safe_str(spec.get("version"))
            nkey = _normalize_name(name)
            if nkey not in seen:
                seen.add(nkey)
                result.append({"name": name.strip(), "version": version, "source_file": filename})
    return result


def parse_cargo_lock(content: str, filename: str = "Cargo.lock") -> list[dict[str, str]]:
    """Parse Cargo.lock [[package]] sections."""
    data = _load_toml(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for pkg in data.get("package", []) or []:
        if not isinstance(pkg, dict):
            continue
        name = pkg.get("name")
        if not name:
            continue
        version = _safe_str(pkg.get("version"))
        nkey = f"{_normalize_name(name)}@{version}" if version else _normalize_name(name)
        if nkey not in seen:
            seen.add(nkey)
            result.append({"name": name.strip(), "version": version or None, "source_file": filename})
    return result


def parse_cyclonedx(content: str, filename: str = "bom.json") -> list[dict[str, str]]:
    """Parse CycloneDX SBOM JSON. components[].name, version."""
    data = json.loads(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    components = data.get("components") or []
    for comp in components:
        if not isinstance(comp, dict):
            continue
        name = comp.get("name") or comp.get("purl", "")
        if not name:
            continue
        if "purl" in comp and isinstance(comp["purl"], str):
            # purl: pkg:npm/foo@1.0 -> extract name
            purl = comp["purl"]
            if "/" in purl and "@" in purl:
                name = purl.split("/")[-1].split("@")[0]
            elif "/" in purl:
                name = purl.split("/")[-1]
        version = _safe_str(comp.get("version"))
        nkey = f"{_normalize_name(name)}@{version}" if version else _normalize_name(name)
        if nkey not in seen:
            seen.add(nkey)
            result.append({"name": str(name).strip(), "version": version or None, "source_file": filename})
    return result


def parse_spdx(content: str, filename: str = "sbom.json") -> list[dict[str, str]]:
    """Parse SPDX JSON. packages[].name, versionInfo."""
    data = json.loads(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    packages = data.get("packages") or []
    for pkg in packages:
        if not isinstance(pkg, dict):
            continue
        name = pkg.get("name") or pkg.get("SPDXID", "")
        if not name:
            continue
        version = _safe_str(pkg.get("versionInfo"))
        nkey = f"{_normalize_name(name)}@{version}" if version else _normalize_name(name)
        if nkey not in seen:
            seen.add(nkey)
            result.append({"name": str(name).strip(), "version": version or None, "source_file": filename})
    return result


def parse_go_sum(content: str, filename: str = "go.sum") -> list[dict[str, str]]:
    """Parse go.sum: module path version."""
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for line in content.splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        mod = parts[0]
        if not mod or mod.startswith("//"):
            continue
        version = parts[1] if len(parts) > 1 else None
        nkey = f"{_normalize_name(mod)}@{version}" if version else _normalize_name(mod)
        if nkey not in seen:
            seen.add(nkey)
            result.append({"name": mod.strip(), "version": version, "source_file": filename})
    return result


def _load_yaml(content: str) -> dict:
    """Load YAML."""
    import yaml
    return yaml.safe_load(content) or {}


def parse_yarn_lock(content: str, filename: str = "yarn.lock") -> list[dict[str, str]]:
    """Parse yarn.lock. Format: 'package@version, package@^x.y:' then '  version "1.0.0"'."""
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    current_name: str | None = None
    current_version: str | None = None
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            if current_name and current_version:
                nkey = f"{_normalize_name(current_name)}@{current_version}"
                if nkey not in seen:
                    seen.add(nkey)
                    result.append({"name": current_name, "version": current_version, "source_file": filename})
            current_name = None
            current_version = None
            continue
        if stripped.endswith(":") and '"' not in stripped:
            # Header: "package@1.0.0, package@^1.0:"
            parts = stripped[:-1].split(",")
            for part in parts:
                m = re.match(r'^"?([^"@]+)"?@', part.strip())
                if m:
                    current_name = m.group(1).strip()
                    break
        elif stripped.startswith("version "):
            m = re.search(r'version\s+"([^"]+)"', stripped)
            if m:
                current_version = m.group(1)
    if current_name and current_version and f"{_normalize_name(current_name)}@{current_version}" not in seen:
        result.append({"name": current_name, "version": current_version, "source_file": filename})
    return result


def parse_pnpm_lock(content: str, filename: str = "pnpm-lock.yaml") -> list[dict[str, str]]:
    """Parse pnpm-lock.yaml packages section."""
    data = _load_yaml(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    packages = data.get("packages") or {}
    for path, pkg in packages.items():
        if not isinstance(path, str) or path.startswith("file:"):
            continue
        # path like "/lodash@4.17.21" or "registry.npmjs.org/lodash@4.17.21"
        parts = path.strip("/").split("/")
        last = parts[-1] if parts else ""
        if "@" in last:
            name, version = last.rsplit("@", 1)
        else:
            name = last
            version = pkg.get("version") if isinstance(pkg, dict) else None
        if not name or name in (".", ""):
            continue
        version = _safe_str(version) if version else None
        nkey = f"{_normalize_name(name)}@{version}" if version else _normalize_name(name)
        if nkey not in seen:
            seen.add(nkey)
            result.append({"name": name.strip(), "version": version, "source_file": filename})
    return result


def parse_pipfile(content: str, filename: str = "Pipfile") -> list[dict[str, str]]:
    """Parse Pipfile [packages] and [dev-packages]."""
    data = _load_toml(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for key in ("packages", "dev-packages"):
        deps = data.get(key)
        if not isinstance(deps, dict):
            continue
        for name, spec in deps.items():
            if not name or name == "*":
                continue
            version = _strip_version_spec(str(spec)) if spec else None
            nkey = _normalize_name(name)
            if nkey not in seen:
                seen.add(nkey)
                result.append({"name": name.strip(), "version": version, "source_file": filename})
    return result


def parse_pipfile_lock(content: str, filename: str = "Pipfile.lock") -> list[dict[str, str]]:
    """Parse Pipfile.lock default._meta.requires and default/package."""
    data = json.loads(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    default = data.get("default") or {}
    for name, spec in default.items():
        if not isinstance(spec, dict):
            continue
        version = _safe_str(spec.get("version"))
        nkey = f"{_normalize_name(name)}@{version}" if version else _normalize_name(name)
        if nkey not in seen:
            seen.add(nkey)
            result.append({"name": name.strip(), "version": version or None, "source_file": filename})
    return result


def parse_gemfile_lock(content: str, filename: str = "Gemfile.lock") -> list[dict[str, str]]:
    """Parse Gemfile.lock. Format: GEM name (version) or GEM name-version."""
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("PLATFORMS") or line.startswith("DEPENDENCIES") or line.startswith("BUNDLED"):
            continue
        # "    foo (1.2.3)" or "    foo-1.2.3"
        m = re.match(r"^\s*([a-zA-Z0-9_-]+)\s*[\(-]\s*([\d.]+[\w.-]*)\)?", line)
        if m:
            name, version = m.group(1), m.group(2)
            nkey = f"{_normalize_name(name)}@{version}"
            if nkey not in seen:
                seen.add(nkey)
                result.append({"name": name.strip(), "version": version, "source_file": filename})
    return result


def parse_composer_json(content: str, filename: str = "composer.json") -> list[dict[str, str]]:
    """Parse composer.json require and require-dev."""
    data = json.loads(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for key in ("require", "require-dev"):
        deps = data.get(key)
        if not isinstance(deps, dict):
            continue
        for name, spec in deps.items():
            if not name or name in ("php", "ext-*"):
                continue
            version = _strip_version_spec(str(spec)) if spec else None
            nkey = _normalize_name(name)
            if nkey not in seen:
                seen.add(nkey)
                result.append({"name": name.strip(), "version": version, "source_file": filename})
    return result


def parse_composer_lock(content: str, filename: str = "composer.lock") -> list[dict[str, str]]:
    """Parse composer.lock packages and packages-dev."""
    data = json.loads(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for key in ("packages", "packages-dev"):
        for pkg in data.get(key) or []:
            if not isinstance(pkg, dict):
                continue
            name = pkg.get("name")
            if not name:
                continue
            version = _safe_str(pkg.get("version"))
            nkey = f"{_normalize_name(name)}@{version}" if version else _normalize_name(name)
            if nkey not in seen:
                seen.add(nkey)
                result.append({"name": name.strip(), "version": version or None, "source_file": filename})
    return result


def parse_pom_xml(content: str, filename: str = "pom.xml") -> list[dict[str, str]]:
    """Parse pom.xml dependencies. Extracts groupId:artifactId."""
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    dep_blocks = re.findall(r"<dependency>(.*?)</dependency>", content, re.DOTALL | re.IGNORECASE)
    for block in dep_blocks:
        ga = re.search(r"<groupId>([^<]+)</groupId>", block, re.IGNORECASE)
        ar = re.search(r"<artifactId>([^<]+)</artifactId>", block, re.IGNORECASE)
        ver = re.search(r"<version>([^<]+)</version>", block, re.IGNORECASE)
        if ga and ar:
            group = ga.group(1).strip()
            artifact = ar.group(1).strip()
            name = f"{group}:{artifact}" if group != artifact else artifact
            version = ver.group(1).strip() if ver else None
            nkey = f"{_normalize_name(name)}@{version}" if version else _normalize_name(name)
            if nkey not in seen:
                seen.add(nkey)
                result.append({"name": name.strip(), "version": version, "source_file": filename})
    return result


def parse_build_gradle(content: str, filename: str = "build.gradle") -> list[dict[str, str]]:
    """Parse build.gradle implementation/compile lines. Group:artifact:version."""
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    # implementation 'group:artifact:version' or implementation "group:artifact:version"
    patterns = [
        r"(?:implementation|api|compile|runtimeOnly)\s+['\"]([^'\"]+)['\"]",
        r"(?:implementation|api|compile|runtimeOnly)\s+\(['\"]([^'\"]+)['\"]\)",
    ]
    for pattern in patterns:
        for m in re.finditer(pattern, content):
            spec = m.group(1)
            parts = spec.split(":")
            if len(parts) >= 2:
                name = ":".join(parts[:2]) if len(parts) > 2 else parts[0]
                version = parts[2] if len(parts) > 2 else None
            else:
                name = parts[0] if parts else ""
                version = None
            if name and _normalize_name(name) not in seen:
                seen.add(_normalize_name(name))
                result.append({"name": name.strip(), "version": version, "source_file": filename})
    return result


def parse_pubspec_yaml(content: str, filename: str = "pubspec.yaml") -> list[dict[str, str]]:
    """Parse pubspec.yaml dependencies and dev_dependencies."""
    data = _load_yaml(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for key in ("dependencies", "dev_dependencies"):
        deps = data.get(key)
        if not isinstance(deps, dict):
            continue
        for name, spec in deps.items():
            if not name or name in ("flutter", "sdk"):
                continue
            version = None
            if isinstance(spec, str):
                version = _strip_version_spec(spec)
            elif isinstance(spec, dict) and "version" in spec:
                version = _safe_str(spec.get("version"))
            nkey = _normalize_name(name)
            if nkey not in seen:
                seen.add(nkey)
                result.append({"name": name.strip(), "version": version, "source_file": filename})
    return result


def parse_package_swift(content: str, filename: str = "Package.swift") -> list[dict[str, str]]:
    """Parse Package.swift .package(url:..., from: ...) or .package(name:...)."""
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    # .package(url: "https://...", from: "1.0.0") or .package(name: "Foo", url: "https://...", from: "1.0.0")
    # .package(name: "Foo", "1.0.0"..<"2.0.0")
    for m in re.finditer(pattern=r'\.package\s*\([^)]+\)', string=content, flags=re.DOTALL):
        block = m.group(0)
        name_match = re.search(r'name:\s*["\']([^"\']+)["\']', block)
        url_match = re.search(r'url:\s*["\']([^"\']+)["\']', block)
        from_match = re.search(r'from:\s*["\']([^"\']+)["\']', block)
        exact_match = re.search(r'["\']([\d.]+)["\']', block)
        name = name_match.group(1).strip() if name_match else None
        if not name and url_match:
            url = url_match.group(1)
            name = url.split("/")[-1].replace(".git", "").strip()
        version = (from_match or exact_match)
        version = version.group(1) if version else None
        if name and _normalize_name(name) not in seen:
            seen.add(_normalize_name(name))
            result.append({"name": name.strip(), "version": version, "source_file": filename})
    return result


def parse_package_resolved(content: str, filename: str = "Package.resolved") -> list[dict[str, str]]:
    """Parse Package.resolved (Swift SPM) JSON."""
    data = json.loads(content)
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    pins = data.get("pins") or data.get("object", {}).get("pins") or []
    for pin in pins:
        if not isinstance(pin, dict):
            continue
        identity = pin.get("identity") or pin.get("package")
        if not identity:
            continue
        name = identity if isinstance(identity, str) else identity.get("name", "")
        if not name:
            continue
        state = pin.get("state") or pin.get("revision")
        version = None
        if isinstance(state, dict):
            version = _safe_str(state.get("version"))
        elif isinstance(state, str):
            version = state[:20] if len(state) > 20 else state
        nkey = f"{_normalize_name(name)}@{version}" if version else _normalize_name(name)
        if nkey not in seen:
            seen.add(nkey)
            result.append({"name": name.strip(), "version": version or None, "source_file": filename})
    return result


def detect_and_parse(content: bytes | str, filename: str) -> list[dict[str, str]]:
    """
    Detect file format by filename/content and parse.
    Returns list of {name, version?, source_file}.
    """
    text = content.decode("utf-8", errors="replace") if isinstance(content, bytes) else content
    fn_lower = filename.lower().strip()

    if "package-lock.json" in fn_lower or fn_lower.endswith("package-lock.json"):
        return parse_package_lock(text, filename)
    if "package.json" in fn_lower or fn_lower.endswith("package.json"):
        return parse_package_json(text, filename)
    if "yarn.lock" in fn_lower or fn_lower.endswith("yarn.lock"):
        return parse_yarn_lock(text, filename)
    if "pnpm-lock.yaml" in fn_lower or fn_lower.endswith("pnpm-lock.yaml"):
        return parse_pnpm_lock(text, filename)
    if "requirements.txt" in fn_lower or fn_lower.endswith("requirements.txt"):
        return parse_requirements_txt(text, filename)
    if "pyproject.toml" in fn_lower or fn_lower.endswith("pyproject.toml"):
        return parse_pyproject_toml(text, filename)
    if "poetry.lock" in fn_lower or fn_lower.endswith("poetry.lock"):
        return parse_poetry_lock(text, filename)
    if "pipfile.lock" in fn_lower or fn_lower.endswith("pipfile.lock"):
        return parse_pipfile_lock(text, filename)
    if "pipfile" in fn_lower or fn_lower.endswith("pipfile"):
        return parse_pipfile(text, filename)
    if "gemfile.lock" in fn_lower or fn_lower.endswith("gemfile.lock"):
        return parse_gemfile_lock(text, filename)
    if "composer.json" in fn_lower or fn_lower.endswith("composer.json"):
        return parse_composer_json(text, filename)
    if "composer.lock" in fn_lower or fn_lower.endswith("composer.lock"):
        return parse_composer_lock(text, filename)
    if "pom.xml" in fn_lower or fn_lower.endswith("pom.xml"):
        return parse_pom_xml(text, filename)
    if "build.gradle" in fn_lower or fn_lower.endswith("build.gradle"):
        return parse_build_gradle(text, filename)
    if "pubspec.yaml" in fn_lower or fn_lower.endswith("pubspec.yaml"):
        return parse_pubspec_yaml(text, filename)
    if "package.swift" in fn_lower or fn_lower.endswith("package.swift"):
        return parse_package_swift(text, filename)
    if "package.resolved" in fn_lower or fn_lower.endswith("package.resolved"):
        return parse_package_resolved(text, filename)
    if "cargo.toml" in fn_lower or fn_lower.endswith("cargo.toml"):
        return parse_cargo_toml(text, filename)
    if "cargo.lock" in fn_lower or fn_lower.endswith("cargo.lock"):
        return parse_cargo_lock(text, filename)
    if "go.sum" in fn_lower or fn_lower.endswith("go.sum"):
        return parse_go_sum(text, filename)

    # Try JSON for SBOM
    if fn_lower.endswith(".json") or "bom" in fn_lower or "sbom" in fn_lower:
        try:
            data = json.loads(text)
            if "components" in data:
                return parse_cyclonedx(text, filename)
            if "packages" in data and isinstance(data.get("packages"), list):
                first = data["packages"][0] if data["packages"] else {}
                if isinstance(first, dict) and ("SPDXID" in first or "name" in first):
                    return parse_spdx(text, filename)
        except json.JSONDecodeError:
            pass

    return []
