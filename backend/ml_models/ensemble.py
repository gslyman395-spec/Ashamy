"""
Ensemble model that averages predictions from LSTM, GRU, and Transformer.
"""
import torch
import torch.nn as nn
import numpy as np
from typing import List
from loguru import logger

from .lstm_model import LSTMModel
from .gru_model import GRUModel
from .transformer import TransformerModel


class EnsembleModel(nn.Module):
    """
    Weighted ensemble of LSTM, GRU, and Transformer models.

    Weights are learnable via a softmax layer trained jointly or can be
    set manually.
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 3,
        d_model: int = 128,
        nhead: int = 8,
        transformer_layers: int = 4,
        output_size: int = 1,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.lstm = LSTMModel(input_size, hidden_size, num_layers, output_size, dropout)
        self.gru = GRUModel(input_size, hidden_size, num_layers, output_size, dropout)
        self.transformer = TransformerModel(
            input_size, d_model, nhead, transformer_layers, d_model * 4, dropout, output_size
        )
        # Learnable mixing weights (one per model)
        self.weights = nn.Parameter(torch.ones(3) / 3)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Weighted average of all three sub-models.
        """
        w = torch.softmax(self.weights, dim=0)
        p_lstm = self.lstm(x)
        p_gru = self.gru(x)
        p_transformer = self.transformer(x)
        return w[0] * p_lstm + w[1] * p_gru + w[2] * p_transformer

    def predict(self, x: np.ndarray) -> np.ndarray:
        self.eval()
        with torch.no_grad():
            tensor = torch.tensor(x, dtype=torch.float32)
            if tensor.ndim == 2:
                tensor = tensor.unsqueeze(0)
            output = self(tensor)
        return output.numpy()

    def get_weights(self) -> dict:
        w = torch.softmax(self.weights, dim=0).detach().numpy()
        return {"lstm": float(w[0]), "gru": float(w[1]), "transformer": float(w[2])}

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
