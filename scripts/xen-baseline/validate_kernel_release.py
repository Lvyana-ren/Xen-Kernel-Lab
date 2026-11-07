#!/usr/bin/env python3
"""Validate the patched kernel Makefile and generated Xen release string."""

import argparse
import re
from pathlib import Path


class ReleaseValidationError(ValueError):
    """Raised when the source version or generated release is unexpected."""


# Restrict whitespace matching to horizontal whitespace. In particular, \s
# must not consume the newline after an empty assignment and capture NAME.
_EXTRAVERSION_ASSIGNMENT = re.compile(
    r"^[\t ]*EXTRAVERSION[\t ]*=[\t ]*(.*?)[\t ]*(?:\#.*)?$"
)


def validate_extraversion(makefile_text: str) -> None:
    """Require exactly one uncommented EXTRAVERSION assignment with no value."""
    assignments = []
    for line_number, line in enumerate(makefile_text.splitlines(), start=1):
        if line.lstrip(" \t").startswith("#"):
            continue
        match = _EXTRAVERSION_ASSIGNMENT.fullmatch(line)
        if match:
            assignments.append((line_number, match.group(1)))

    if len(assignments) != 1:
        raise ReleaseValidationError(
            "expected exactly one EXTRAVERSION assignment; "
            f"found {len(assignments)} at lines "
            f"{[number for number, _value in assignments]}"
        )

    line_number, value = assignments[0]
    if value.strip(" \t"):
        raise ReleaseValidationError(
            f"EXTRAVERSION must be empty after the checked release patch "
            f"(line {line_number} contains {value.strip()!r})"
        )


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
