import unittest

from validate_kernel_release import (
    ReleaseValidationError,
    extract_extraversion_values,
    validate_extraversion,
    validate_kernel_release,
)


class ExtraversionValidationTests(unittest.TestCase):
    def test_empty_extraversion_before_kernel_codename(self):
        text = "EXTRAVERSION =\nNAME = Petit Gorille\n"
        self.assertEqual(extract_extraversion_values(text), [""])
        validate_extraversion(text)
        self.assertEqual(
            validate_kernel_release(text, "4.14.357-Xen+4", "xen", "4"),
            "4.14.357-Xen+4",
        )

    def test_next_makefile_assignment_is_not_consumed(self):
        text = "EXTRAVERSION =\nSUBLEVEL = 357\n"
        self.assertEqual(extract_extraversion_values(text), [""])

    def test_horizontal_whitespace_variants_are_supported(self):
        for line in (
            "EXTRAVERSION\t=\t\n",
            "EXTRAVERSION  =   \n",
            "EXTRAVERSION =\t\n",
        ):
            with self.subTest(line=repr(line)):
                validate_extraversion(line)

    def test_commented_assignments_are_ignored(self):
        text = "# EXTRAVERSION = stale\n  # EXTRAVERSION = stale\nEXTRAVERSION =\n"
        self.assertEqual(extract_extraversion_values(text), [""])
        validate_extraversion(text)

    def test_comment_only_assignment_is_missing(self):
        with self.assertRaisesRegex(ReleaseValidationError, "found 0"):
            validate_extraversion("# EXTRAVERSION =\n")

    def test_duplicate_assignments_fail(self):
        self.assertEqual(
            extract_extraversion_values("EXTRAVERSION =\nEXTRAVERSION =\n"), ["", ""]
        )
        with self.assertRaisesRegex(ReleaseValidationError, "found 2"):
            validate_extraversion("EXTRAVERSION =\nEXTRAVERSION =\n")

    def test_nonempty_assignment_fails(self):
        self.assertEqual(extract_extraversion_values("EXTRAVERSION = -openela\n"), ["-openela"])
        with self.assertRaisesRegex(ReleaseValidationError, "must be empty"):
            validate_extraversion("EXTRAVERSION = -openela\n")

    def test_resulting_release_must_match_flavor_and_generation(self):
        text = "EXTRAVERSION =\nNAME = Petit Gorille\n"
        with self.assertRaisesRegex(ReleaseValidationError, "does not match expected"):
            validate_kernel_release(text, "4.14.357-Xen+3", "xen", "4")


if __name__ == "__main__":
    unittest.main()
