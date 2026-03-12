"""CUNEIFORM Experiments — reproducible research tools.

Phase 7: The experiment runner, discovery logger, and validation
framework that turns the survival guide into executable code.
"""

from .smooth_density import SmoothDensityExperiment
from .plimpton_tabulate import PlimptonTabulator
from .discovery_log import DiscoveryLog, Observation
from .benchmark import Benchmark
from .validation import SelfValidator
from .paper_pipeline import PaperPipeline, PipelineResults
