import unittest

from validate_kernel_release import (
    ReleaseValidationError,
    validate_extraversion,
    validate_kernel_release,
)


class ExtraversionValidationTests(unittest.TestCase):
    def test_empty_extraversion_before_kernel_codename(self):
        text = "EXTRAVERSION =\nNAME = Petit Gorille\n"
        validate_extraversion(text)
        self.assertEqual(
            validate_kernel_release(text, "4.14.357-Xen+4", "xen", "4"),
            "4.14.357-Xen+4",
        )

    def test_horizontal_whitespace_variants_are_supported(self):
        for line in (
            "EXTRAVERSION=\t\n",
            "\tEXTRAVERSION \t= \t # release suffix intentionally empty\n",
        ):
            with self.subTest(line=repr(line)):
                validate_extraversion(line)

    def test_commented_assignments_are_ignored(self):
        validate_extraversion(
            "# EXTRAVERSION = stale\n"
            "  # EXTRAVERSION = also-stale\n"
            "EXTRAVERSION =\n"
        )

    def test_comment_only_assignment_is_missing(self):
        with self.assertRaisesRegex(ReleaseValidationError, "found 0"):
            validate_extraversion("# EXTRAVERSION =\n")

    def test_duplicate_assignments_fail(self):
        with self.assertRaisesRegex(ReleaseValidationError, "found 2"):
            validate_extraversion("EXTRAVERSION =\nEXTRAVERSION =\n")

    def test_nonempty_assignment_fails(self):
        with self.assertRaisesRegex(ReleaseValidationError, "must be empty"):
            validate_extraversion("EXTRAVERSION = -openela\n")

    def test_resulting_release_must_match_flavor_and_generation(self):
        text = "EXTRAVERSION =\nNAME = Petit Gorille\n"
        with self.assertRaisesRegex(ReleaseValidationError, "does not match expected"):
            validate_kernel_release(text, "4.14.357-Xen+3", "xen", "4")


if __name__ == "__main__":
    unittest.main()
