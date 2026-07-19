import torch
import torch.nn as nn
import pandas as pd
import numpy as np

class TransformerModel(nn.Module):
    def __init__(self, feature_size=4, num_layers=2, num_heads=4, hidden_dim=64):
        super().__init__()

        self.encoder_layer = nn.TransformerEncoderLayer(
            d_model=feature_size,
            nhead=num_heads,
            dim_feedforward=hidden_dim,
            dropout=0.1,
            batch_first=True
        )

        self.transformer = nn.TransformerEncoder(self.encoder_layer, num_layers=num_layers)
        self.fc = nn.Linear(feature_size, 1)

    def forward(self, x):
        x = self.transformer(x)
        x = self.fc(x[:, -1, :])
        return x


class TransformerPredictor:
    def __init__(self, seq_len=20):
        self.seq_len = seq_len
        self.model = TransformerModel()
        self.loss_fn = nn.MSELoss()
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.001)

    def prepare_sequences(self, df):
        df = df.dropna()
        features = df[["Close", "MA_20", "MA_50", "RSI"]].values

        X, y = [], []
        for i in range(len(features) - self.seq_len):
            X.append(features[i:i+self.seq_len])
            y.append(features[i+self.seq_len][0])  # توقع السعر القادم

        return torch.tensor(np.array(X), dtype=torch.float32), torch.tensor(np.array(y), dtype=torch.float32)

    def train(self, df, epochs=20):
        X, y = self.prepare_sequences(df)

        for epoch in range(epochs):
            pred = self.model(X)
            loss = self.loss_fn(pred.squeeze(), y)

            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

    def predict_next(self, df):
        df = df.dropna()
        features = df[["Close", "MA_20", "MA_50", "RSI"]].values

        seq = features[-self.seq_len:]
        seq = torch.tensor(seq, dtype=torch.float32).unsqueeze(0)

        pred = self.model(seq)
        return float(pred.item())
