#!/usr/bin/env python3
"""Scan frappe codebase and produce structured inventory."""

import json
import os
import subprocess
import sys

PROJECT_ROOT = "/Users/vovanduc/Code/dcnet/frappe"
OUTPUT = os.path.join(PROJECT_ROOT, ".understand-anything/intermediate/scan-result.json")

SOURCE_EXTS = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript (JSX)",
    ".ts": "TypeScript", ".tsx": "TypeScript (TSX)", ".vue": "Vue",
    ".svelte": "Svelte", ".go": "Go", ".rs": "Rust", ".java": "Java",
    ".rb": "Ruby", ".cpp": "C++", ".cc": "C++", ".cxx": "C++",
    ".h": "C/C++ Header", ".hpp": "C++ Header", ".c": "C",
    ".cs": "C#", ".swift": "Swift", ".kt": "Kotlin", ".php": "PHP",
    ".sh": "Shell", ".bash": "Shell",
}

EXCLUDE_DIRS = {"node_modules/", ".git/", "vendor/", "venv/", "__pycache__/", "dist/", "build/", "coverage/", ".next/", ".cache/", "target/"}
EXCLUDE_PATTERNS = {".min.js", ".min.css", ".map", ".d.ts", ".generated."}


def should_exclude(path):
    for d in EXCLUDE_DIRS:
        if f"/{d}" in f"/{path}" or path.startswith(d):
            return True
    for p in EXCLUDE_PATTERNS:
        if p in path:
            return True
    return False


def get_ext(path):
    # Handle .d.ts specially
    if path.endswith(".d.ts"):
        return ".d.ts"
    _, ext = os.path.splitext(path)
    return ext.lower()


def classify_complexity(lines):
    if lines <= 20:
        return "small"
    elif lines <= 100:
        return "moderate"
    elif lines <= 500:
        return "large"
    return "very-large"


def detect_frameworks():
    frameworks = []
    # Check package.json
    pkg_path = os.path.join(PROJECT_ROOT, "package.json")
    if os.path.exists(pkg_path):
        with open(pkg_path) as f:
            pkg = json.load(f)
        all_deps = {}
        all_deps.update(pkg.get("dependencies", {}))
        all_deps.update(pkg.get("devDependencies", {}))
        fw_map = {
            "vue": "Vue.js", "react": "React", "angular": "Angular",
            "svelte": "Svelte", "express": "Express", "next": "Next.js",
            "nuxt": "Nuxt.js", "socket.io": "Socket.IO", "esbuild": "esbuild",
            "tailwindcss": "Tailwind CSS", "bootstrap": "Bootstrap",
        }
        for dep, name in fw_map.items():
            if dep in all_deps:
                frameworks.append(name)

    # Check pyproject.toml
    pyproject_path = os.path.join(PROJECT_ROOT, "pyproject.toml")
    if os.path.exists(pyproject_path):
        with open(pyproject_path) as f:
            content = f.read()
        py_fw = {
            "Django": "django", "Flask": "flask", "Werkzeug": "werkzeug",
            "Jinja2": "jinja2", "Redis": "redis", "Gunicorn": "gunicorn",
            "Celery": "celery", "SQLAlchemy": "sqlalchemy",
        }
        for name, pkg in py_fw.items():
            if pkg.lower() in content.lower():
                frameworks.append(name)

    return sorted(set(frameworks))


def main():
    # Get tracked files
    result = subprocess.run(
        ["git", "ls-files"], capture_output=True, text=True, cwd=PROJECT_ROOT
    )
    all_files = result.stdout.strip().split("\n")

    # Filter to source files
    source_files = []
    for f in all_files:
        if should_exclude(f):
            continue
        ext = get_ext(f)
        if ext in SOURCE_EXTS:
            source_files.append(f)

    # Count lines in batches
    line_counts = {}
    batch_size = 500
    for i in range(0, len(source_files), batch_size):
        batch = source_files[i:i + batch_size]
        abs_batch = [os.path.join(PROJECT_ROOT, f) for f in batch]
        result = subprocess.run(
            ["wc", "-l"] + abs_batch, capture_output=True, text=True
        )
        lines = result.stdout.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line:
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                count_str, path = parts
                try:
                    count = int(count_str)
                except ValueError:
                    continue
                # Skip "total" lines from wc
                if path == "total":
                    continue
                rel = os.path.relpath(path, PROJECT_ROOT)
                line_counts[rel] = count

    # Build file entries
    languages = {}
    files_array = []
    for f in source_files:
        ext = get_ext(f)
        lang = SOURCE_EXTS.get(ext, "Unknown")
        lines = line_counts.get(f, 0)
        complexity = classify_complexity(lines)
        languages[lang] = languages.get(lang, 0) + 1
        files_array.append({
            "path": f,
            "language": lang,
            "lines": lines,
            "complexity": complexity,
        })

    # Sort languages by count
    sorted_langs = sorted(languages.items(), key=lambda x: -x[1])
    lang_list = [{"name": name, "fileCount": count} for name, count in sorted_langs]

    frameworks = detect_frameworks()

    # Project info
    project_name = "frappe"
    description = "Metadata-driven, full-stack low-code web framework in Python and JavaScript, powering ERPNext."

    total_files = len(files_array)
    total_lines = sum(f["lines"] for f in files_array)

    if total_lines > 100000:
        est_complexity = "very-large"
    elif total_lines > 30000:
        est_complexity = "large"
    elif total_lines > 5000:
        est_complexity = "moderate"
    else:
        est_complexity = "small"

    output = {
        "name": project_name,
        "description": description,
        "languages": lang_list,
        "frameworks": frameworks,
        "totalFiles": total_files,
        "totalLines": total_lines,
        "estimatedComplexity": est_complexity,
        "files": files_array,
    }

    if total_files > 200:
        output["note"] = f"Large project with {total_files} source files. Consider scoping analysis to specific modules or subsystems."

    with open(OUTPUT, "w") as f:
        json.dump(output, f, indent=2)

    print(f"Scan complete: {total_files} files, {total_lines} lines")
    print(f"Languages: {', '.join(n for n, _ in sorted_langs)}")
    print(f"Complexity: {est_complexity}")


if __name__ == "__main__":
    main()
