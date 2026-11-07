#!/usr/bin/env python3
"""Validate the patched kernel Makefile and generated Xen release string."""

import argparse
import re
import subprocess
import sys
from pathlib import Path


class ReleaseValidationError(ValueError):
    """Raised when the source version or generated release is unexpected."""


_RELEASE_TOKEN = re.compile(r"4\.14\.357-Xen(?:-KSUN)?\+[0-9]+")
_RELEASE_LINE = re.compile(r"4\.14\.357-Xen(?:-KSUN)?\+[1-9][0-9]*")
_EXTRAVERSION_ASSIGNMENT_LINE = re.compile(r"^(EXTRAVERSION)[ \t]*=(.*)$")


def extract_extraversion_values(makefile_text: str) -> list[str]:
    """Return values from exact EXTRAVERSION assignments, line by line."""
    lines = makefile_text.splitlines()
    # Normalize horizontal whitespace only, then apply the exact matcher below.
    # This also gives an empty RHS the horizontal separator required by that
    # expression without allowing it to cross the next Makefile line.
    normalized_lines = []
    for line in lines:
        assignment = _EXTRAVERSION_ASSIGNMENT_LINE.fullmatch(line)
        if assignment:
            value = assignment.group(2).lstrip(" \t")
            line = f"{assignment.group(1)} = {value}"
        normalized_lines.append(line)
    normalized_text = "\n".join(normalized_lines)
    matches = re.findall(r"(?m)^EXTRAVERSION[ \t]=[ \t](.*)$", normalized_text)
    return [value.strip(" \t") for value in matches]


def validate_extraversion(makefile_text: str) -> None:
    """Require exactly one uncommented EXTRAVERSION assignment with no value."""
    matches = extract_extraversion_values(makefile_text)
    if len(matches) != 1:
        raise ReleaseValidationError(
            "expected exactly one EXTRAVERSION assignment; "
            f"found {len(matches)}"
        )

    value = matches[0]
    if value.strip(" \t"):
        raise ReleaseValidationError("EXTRAVERSION must be empty after the checked release patch")


def expected_release(flavor: str, generation: str) -> str:
    if not re.fullmatch(r"[1-9][0-9]*", generation):
        raise ReleaseValidationError("release generation must be a positive integer")
    if flavor == "xen":
        suffix = "-Xen"
    elif flavor == "ksun":
        suffix = "-Xen-KSUN"
    else:
        raise ReleaseValidationError(f"unsupported release flavor: {flavor!r}")
    return f"4.14.357{suffix}+{generation}"


def extract_kernel_release(make_stdout: str, flavor: str, generation: str) -> str:
    """Extract one release line from GNU Make output, rejecting log substrings."""
    if not make_stdout.strip():
        raise ReleaseValidationError("GNU Make produced empty kernelrelease output")

    expected = expected_release(flavor, generation)
    release_tokens = []
    exact_lines = []
    for line in make_stdout.splitlines():
        stripped = line.strip()
        tokens = _RELEASE_TOKEN.findall(stripped)
        release_tokens.extend(tokens)
        if _RELEASE_LINE.fullmatch(stripped):
            exact_lines.append(stripped)

    if len(release_tokens) != 1:
        raise ReleaseValidationError(
            "expected exactly one kernel release candidate in GNU Make output; "
            f"found {release_tokens!r}"
        )
    if len(exact_lines) != 1 or exact_lines[0] != release_tokens[0]:
        raise ReleaseValidationError(
            "kernel release candidate must occupy its own complete output line"
        )
    if exact_lines[0] != expected:
        raise ReleaseValidationError(
            f"generated kernel release {exact_lines[0]!r} does not match expected {expected!r}"
        )
    return exact_lines[0]


def run_make_kernelrelease(command: list[str]) -> tuple[str, int]:
    """Capture GNU Make output and forward diagnostics without losing its status."""
    if not command:
        raise ReleaseValidationError("GNU Make command is empty")
    completed = subprocess.run(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    # Keep recursive Make/GEN/configuration output and all stderr visible in
    # the Actions log while reserving this process's stdout for the release.
    if completed.stdout:
        sys.stderr.write(completed.stdout)
    if completed.stderr:
        sys.stderr.write(completed.stderr)
    if completed.returncode != 0:
        raise ReleaseValidationError(
            f"GNU Make kernelrelease command failed with exit code {completed.returncode}"
        )
    return completed.stdout, completed.returncode


def validate_kernel_release(
    makefile_text: str, make_stdout: str, flavor: str, generation: str
) -> str:
    validate_extraversion(makefile_text)
    return extract_kernel_release(make_stdout, flavor, generation)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--makefile", type=Path, required=True)
    parser.add_argument("--flavor", choices=("xen", "ksun"), required=True)
    parser.add_argument("--generation", required=True)
    parser.add_argument("--make-command", nargs=argparse.REMAINDER, required=True)
    args = parser.parse_args()

    try:
        make_command = args.make_command
        if make_command and make_command[0] == "--":
            make_command = make_command[1:]
        stdout, _returncode = run_make_kernelrelease(make_command)
        release = validate_kernel_release(
            args.makefile.read_text(encoding="utf-8"),
            stdout,
            args.flavor,
            args.generation,
        )
    except (OSError, ReleaseValidationError) as error:
        parser.error(str(error))
    print(release)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
