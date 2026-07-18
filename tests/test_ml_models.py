"""
Tests for ML models (shape / forward-pass only – no real training).
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

import pytest
import torch
import numpy as np

from ml_models.lstm_model import LSTMModel
from ml_models.gru_model import GRUModel
from ml_models.transformer import TransformerModel, PositionalEncoding
from ml_models.ensemble import EnsembleModel


INPUT_SIZE = 10
SEQ_LEN = 30
BATCH = 4
OUTPUT_SIZE = 1


@pytest.fixture
def sample_batch():
    return torch.randn(BATCH, SEQ_LEN, INPUT_SIZE)


class TestLSTMModel:
    def test_output_shape(self, sample_batch):
        model = LSTMModel(input_size=INPUT_SIZE, hidden_size=32, num_layers=2)
        out = model(sample_batch)
        assert out.shape == (BATCH, OUTPUT_SIZE)

    def test_predict_numpy(self):
        model = LSTMModel(input_size=INPUT_SIZE, hidden_size=32, num_layers=2)
        x = np.random.randn(SEQ_LEN, INPUT_SIZE).astype(np.float32)
        pred = model.predict(x)
        assert pred.shape[1] == OUTPUT_SIZE

    def test_parameter_count_positive(self):
        model = LSTMModel(input_size=INPUT_SIZE)
        assert model.count_parameters() > 0


class TestGRUModel:
    def test_output_shape(self, sample_batch):
        model = GRUModel(input_size=INPUT_SIZE, hidden_size=32, num_layers=2)
        out = model(sample_batch)
        assert out.shape == (BATCH, OUTPUT_SIZE)

    def test_predict_numpy(self):
        model = GRUModel(input_size=INPUT_SIZE, hidden_size=32, num_layers=2)
        x = np.random.randn(SEQ_LEN, INPUT_SIZE).astype(np.float32)
        pred = model.predict(x)
        assert pred.shape[1] == OUTPUT_SIZE


class TestPositionalEncoding:
    def test_output_same_shape(self):
        pe = PositionalEncoding(d_model=64, dropout=0.0)
        x = torch.zeros(2, SEQ_LEN, 64)
        out = pe(x)
        assert out.shape == x.shape


class TestTransformerModel:
    def test_output_shape(self, sample_batch):
        model = TransformerModel(
            input_size=INPUT_SIZE, d_model=32, nhead=4, num_layers=2
        )
        out = model(sample_batch)
        assert out.shape == (BATCH, OUTPUT_SIZE)

    def test_predict_numpy(self):
        model = TransformerModel(
            input_size=INPUT_SIZE, d_model=32, nhead=4, num_layers=2
        )
        x = np.random.randn(SEQ_LEN, INPUT_SIZE).astype(np.float32)
        pred = model.predict(x)
        assert pred.shape[1] == OUTPUT_SIZE


class TestEnsembleModel:
    def test_output_shape(self, sample_batch):
        model = EnsembleModel(
            input_size=INPUT_SIZE,
            hidden_size=32,
            num_layers=2,
            d_model=32,
            nhead=4,
            transformer_layers=2,
        )
        out = model(sample_batch)
        assert out.shape == (BATCH, OUTPUT_SIZE)

    def test_weights_sum_to_one(self):
        model = EnsembleModel(input_size=INPUT_SIZE, hidden_size=32, num_layers=2, d_model=32, nhead=4, transformer_layers=2)
        w = model.get_weights()
        total = w["lstm"] + w["gru"] + w["transformer"]
        assert abs(total - 1.0) < 1e-5

    def test_predict_numpy(self):
        model = EnsembleModel(input_size=INPUT_SIZE, hidden_size=32, num_layers=2, d_model=32, nhead=4, transformer_layers=2)
        x = np.random.randn(SEQ_LEN, INPUT_SIZE).astype(np.float32)
        pred = model.predict(x)
        assert pred.shape[1] == OUTPUT_SIZE
