"""Publication pipeline: paper generation, figures, tables."""

from .paper import PaperGenerator
from .figures import FigureGenerator
from .tables import TableGenerator

__all__ = ["PaperGenerator", "FigureGenerator", "TableGenerator"]
