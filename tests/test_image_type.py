import math
import unittest

from scripts.image_type import (
    ImageType,
    classify_image,
    macro_amplitude,
    macro_complex_factor,
    maximum_from_reversed_factor,
    saddle_orientation_supported,
)


class ImageTypeTests(unittest.TestCase):
    def test_minimum_classification(self):
        self.assertIs(classify_image(0.45, 0.45), ImageType.MINIMUM)

    def test_saddle_classification(self):
        self.assertIs(classify_image(0.8, 0.4), ImageType.SADDLE)
        self.assertTrue(saddle_orientation_supported(0.8, 0.4))

    def test_maximum_classification(self):
        self.assertIs(classify_image(1.2, 0.1), ImageType.MAXIMUM)

    def test_opposite_saddle_orientation_is_detected_but_not_supported(self):
        self.assertIs(classify_image(1.2, -0.3), ImageType.SADDLE)
        self.assertFalse(saddle_orientation_supported(1.2, -0.3))

    def test_critical_curve_is_rejected(self):
        with self.assertRaises(ValueError):
            classify_image(0.5, 0.5)

    def test_macro_amplitude(self):
        self.assertAlmostEqual(macro_amplitude(0.45, 0.45), math.sqrt(10.0))

    def test_macro_morse_factors(self):
        amplitude = 3.0
        self.assertEqual(
            macro_complex_factor(ImageType.MINIMUM, amplitude),
            3.0 + 0.0j,
        )
        self.assertEqual(
            macro_complex_factor(ImageType.SADDLE, amplitude),
            0.0 - 3.0j,
        )
        self.assertEqual(
            macro_complex_factor(ImageType.MAXIMUM, amplitude),
            -3.0 + 0.0j,
        )

    def test_maximum_time_reversal_mapping(self):
        reversed_factor = 2.0 + 5.0j
        self.assertEqual(
            maximum_from_reversed_factor(reversed_factor),
            -2.0 + 5.0j,
        )


if __name__ == "__main__":
    unittest.main()
