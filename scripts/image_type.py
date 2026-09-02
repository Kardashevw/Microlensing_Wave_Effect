from enum import Enum


class ImageType(str, Enum):
    MINIMUM = "minimum"
    SADDLE = "saddle"
    MAXIMUM = "maximum"


def jacobian_eigenvalues(kappa: float, gamma: float) -> tuple[float, float]:
    return 1.0 - kappa + gamma, 1.0 - kappa - gamma


def classify_image(kappa: float, gamma: float) -> ImageType:
    radial, tangential = jacobian_eigenvalues(kappa, gamma)

    if radial == 0.0 or tangential == 0.0:
        raise ValueError(
            "The macro image is critical because one Jacobian eigenvalue is zero."
        )

    if radial > 0.0 and tangential > 0.0:
        return ImageType.MINIMUM
    if radial < 0.0 and tangential < 0.0:
        return ImageType.MAXIMUM
    return ImageType.SADDLE


def saddle_orientation_supported(kappa: float, gamma: float) -> bool:
    radial, tangential = jacobian_eigenvalues(kappa, gamma)
    return radial > 0.0 and tangential < 0.0


def macro_amplitude(kappa: float, gamma: float) -> float:
    determinant = (1.0 - kappa) ** 2 - gamma**2
    if determinant == 0.0:
        raise ValueError("Macro magnification diverges on the critical curve.")
    return abs(1.0 / determinant) ** 0.5


def macro_complex_factor(image_type: ImageType, amplitude: float) -> complex:
    """Positive-frequency smooth macro factor, including the Morse phase."""
    if image_type is ImageType.MINIMUM:
        return complex(amplitude, 0.0)
    if image_type is ImageType.SADDLE:
        return complex(0.0, -amplitude)
    if image_type is ImageType.MAXIMUM:
        return complex(-amplitude, 0.0)
    raise ValueError(f"Unsupported image type: {image_type}")
