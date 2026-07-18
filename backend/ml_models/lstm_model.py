"""
LSTM model for time-series stock price prediction.
"""
import torch
import torch.nn as nn
import numpy as np
from loguru import logger


class LSTMModel(nn.Module):
    """
    Multi-layer LSTM with dropout for stock price prediction.

    Architecture:
        - Input projection layer
        - Stacked LSTM layers with dropout
        - Fully-connected output head
    """

    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 3,
        output_size: int = 1,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, hidden_size // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_size // 2, output_size),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: (batch, seq_len, input_size)
        Returns:
            (batch, output_size)
        """
        lstm_out, _ = self.lstm(x)
        last_step = lstm_out[:, -1, :]
        out = self.dropout(last_step)
        return self.fc(out)

    def predict(self, x: np.ndarray) -> np.ndarray:
        """Run inference on a numpy array."""
        self.eval()
        with torch.no_grad():
            tensor = torch.tensor(x, dtype=torch.float32)
            if tensor.ndim == 2:
                tensor = tensor.unsqueeze(0)
            output = self(tensor)
        return output.numpy()

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
