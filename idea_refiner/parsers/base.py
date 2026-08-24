import abc
from typing import List
from decision_engine.input_layer.schemas import UnvalidatedArchitectureHypothesis

class BaseIdeaParser(abc.ABC):
    """
    Abstract base class for parsing natural language ideas into UnvalidatedArchitectureHypothesis candidates.
    """
    @abc.abstractmethod
    def parse_idea_to_graph(self, idea: str) -> List[UnvalidatedArchitectureHypothesis]:
        pass
