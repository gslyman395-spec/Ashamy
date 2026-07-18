"""
GRU model for stock price prediction.
"""
import torch
import torch.nn as nn
import numpy as np


class GRUModel(nn.Module):
    """
    Gated Recurrent Unit model.

    Faster to train than LSTM with competitive performance on shorter sequences.
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

        self.gru = nn.GRU(
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
        gru_out, _ = self.gru(x)
        last_step = gru_out[:, -1, :]
        return self.fc(self.dropout(last_step))

    def predict(self, x: np.ndarray) -> np.ndarray:
        self.eval()
        with torch.no_grad():
            tensor = torch.tensor(x, dtype=torch.float32)
            if tensor.ndim == 2:
                tensor = tensor.unsqueeze(0)
            output = self(tensor)
        return output.numpy()

    def count_parameters(self) -> int:
        return sum(p.numel() for p in self.parameters() if p.requires_grad)
