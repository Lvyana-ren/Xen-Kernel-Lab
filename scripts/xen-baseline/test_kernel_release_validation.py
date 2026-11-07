import contextlib
import io
import subprocess
import unittest
from unittest import mock

from validate_kernel_release import (
    ReleaseValidationError,
    extract_extraversion_values,
    extract_kernel_release,
    run_make_kernelrelease,
    validate_extraversion,
    validate_kernel_release,
)


class ExtraversionValidationTests(unittest.TestCase):
    def test_empty_extraversion_before_kernel_codename(self):
        text = "EXTRAVERSION =\nNAME = Petit Gorille\n"
        self.assertEqual(extract_extraversion_values(text), [""])
        validate_extraversion(text)
        self.assertEqual(
            validate_kernel_release(text, "4.14.357-Xen+4\n", "xen", "4"),
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


class KernelReleaseOutputTests(unittest.TestCase):
    expected = "4.14.357-Xen+4"

    def test_clean_release_output(self):
        self.assertEqual(extract_kernel_release(self.expected + "\n", "xen", "4"), self.expected)

    def test_recursive_make_directory_messages(self):
        output = (
            "make[1]: Entering directory '/tmp/out'\n"
            + self.expected
            + "\nmake[1]: Leaving directory '/tmp/out'\n"
        )
        self.assertEqual(extract_kernel_release(output, "xen", "4"), self.expected)

    def test_gen_makefile_output(self):
        output = "GEN ./Makefile\n" + self.expected + "\n"
        self.assertEqual(extract_kernel_release(output, "xen", "4"), self.expected)

    def test_silentoldconfig_output(self):
        output = "scripts/config/conf --silentoldconfig Kconfig\n" + self.expected + "\n"
        self.assertEqual(extract_kernel_release(output, "xen", "4"), self.expected)

    def test_incorrect_release_is_rejected(self):
        with self.assertRaisesRegex(ReleaseValidationError, "does not match expected"):
            extract_kernel_release("4.14.357-Xen+3\n", "xen", "4")

    def test_empty_output_is_rejected(self):
        with self.assertRaisesRegex(ReleaseValidationError, "empty"):
            extract_kernel_release(" \n\t\n", "xen", "4")

    def test_multiple_release_like_lines_are_rejected(self):
        output = self.expected + "\n4.14.357-Xen+5\n"
        with self.assertRaisesRegex(ReleaseValidationError, "exactly one"):
            extract_kernel_release(output, "xen", "4")

    def test_release_embedded_in_arbitrary_log_line_is_rejected(self):
        with self.assertRaisesRegex(ReleaseValidationError, "complete output line"):
            extract_kernel_release("kernel version: " + self.expected + "\n", "xen", "4")

    def test_make_failure_preserves_stderr_and_exit_code(self):
        completed = subprocess.CompletedProcess(
            args=["make"], returncode=17, stdout="GEN ./Makefile\n", stderr="make: failed\n"
        )
        diagnostic = io.StringIO()
        with mock.patch("validate_kernel_release.subprocess.run", return_value=completed):
            with contextlib.redirect_stderr(diagnostic):
                with self.assertRaisesRegex(ReleaseValidationError, "exit code 17"):
                    run_make_kernelrelease(["make", "kernelrelease"])
        self.assertIn("GEN ./Makefile", diagnostic.getvalue())
        self.assertIn("make: failed", diagnostic.getvalue())


if __name__ == "__main__":
    unittest.main()
