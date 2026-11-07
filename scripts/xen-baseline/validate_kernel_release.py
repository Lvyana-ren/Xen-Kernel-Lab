#!/usr/bin/env python3
"""Validate the patched kernel Makefile and generated Xen release string."""

import argparse
import re
from pathlib import Path


class ReleaseValidationError(ValueError):
    """Raised when the source version or generated release is unexpected."""


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


def validate_kernel_release(
    makefile_text: str, release: str, flavor: str, generation: str
) -> str:
    validate_extraversion(makefile_text)
    expected = expected_release(flavor, generation)
    if release != expected:
        raise ReleaseValidationError(
            f"generated kernel release {release!r} does not match expected {expected!r}"
        )
    return expected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--makefile", type=Path, required=True)
    parser.add_argument("--release", required=True)
    parser.add_argument("--flavor", choices=("xen", "ksun"), required=True)
    parser.add_argument("--generation", required=True)
    args = parser.parse_args()

    try:
        validate_kernel_release(
            args.makefile.read_text(encoding="utf-8"),
            args.release,
            args.flavor,
            args.generation,
        )
    except (OSError, ReleaseValidationError) as error:
        parser.error(str(error))
    print(f"Validated kernel release: {args.release}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
