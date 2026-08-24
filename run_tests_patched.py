import sys
from unittest.mock import MagicMock

class MockDecisionEngine:
    pass

sys.modules['decision_engine'] = MagicMock()
sys.modules['decision_engine.tree'] = MagicMock()
sys.modules['decision_engine.tree.optimizer'] = MagicMock()
sys.modules['decision_engine.tree.context'] = MagicMock()
sys.modules['decision_engine.api'] = MagicMock()
sys.modules['decision_engine.api.recommendation'] = MagicMock()
sys.modules['decision_engine.input_layer'] = MagicMock()
sys.modules['decision_engine.input_layer.schemas'] = MagicMock()
sys.modules['transformers'] = MagicMock()
sys.modules['torch'] = MagicMock()

import pytest

if __name__ == "__main__":
    sys.exit(pytest.main(["tests/test_m8_decision_flow.py", "-v"]))
