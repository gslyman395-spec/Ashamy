"""
Signal Aggregator - نظام تجميع الإشارات من 10 مصادر عالمية
"""

from signal_aggregator.sources.connector import SourceConnector
from signal_aggregator.aggregation.engine import AggregationEngine
from signal_aggregator.fusion.ai_fusion import AIFusion
from signal_aggregator.scoring.scorer import SignalScorer

__all__ = ["SourceConnector", "AggregationEngine", "AIFusion", "SignalScorer"]
__version__ = "1.0.0"
