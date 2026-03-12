"""Number theory layer: reciprocal pairs, regularity, smoothness, sieving, factoring."""

from .regularity import RegularityClass, classify_regularity, regularity_spectrum
from .reciprocals import ReciprocalPair, ModularReciprocalPair, ReciprocalTable
from .smoothness import is_b_smooth, is_b_smooth_sexa, SmoothBatch
from .factor_base import StandardFactorBase, SexagesimalFactorBase
from .sieve import QuadraticSieve, SexagesimalQuadraticSieve
from .ecm import ECM, PlimptonECM
from .analysis import SmoothDensityExperiment, FactoringComparison

__all__ = [
    "RegularityClass", "classify_regularity", "regularity_spectrum",
    "ReciprocalPair", "ModularReciprocalPair", "ReciprocalTable",
    "is_b_smooth", "is_b_smooth_sexa", "SmoothBatch",
    "StandardFactorBase", "SexagesimalFactorBase",
    "QuadraticSieve", "SexagesimalQuadraticSieve",
    "ECM", "PlimptonECM",
    "SmoothDensityExperiment", "FactoringComparison",
]
