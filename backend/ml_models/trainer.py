"""
Trainer - handles training, validation, and persistence of ML models.
"""
import os
import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from sklearn.model_selection import TimeSeriesSplit
from loguru import logger
from typing import Tuple, Optional

from .ensemble import EnsembleModel


class ModelTrainer:
    """
    Trains and evaluates the ensemble deep-learning model.

    Uses time-series cross-validation (walk-forward) to prevent look-ahead bias.
    """

    def __init__(
        self,
        input_size: int,
        model_dir: str = "models",
        hidden_size: int = 128,
        num_layers: int = 3,
        d_model: int = 128,
        nhead: int = 8,
        transformer_layers: int = 4,
        output_size: int = 1,
        dropout: float = 0.2,
        lr: float = 0.001,
        batch_size: int = 32,
        epochs: int = 100,
        patience: int = 15,
    ):
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        self.batch_size = batch_size
        self.epochs = epochs
        self.patience = patience

        self.model = EnsembleModel(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            d_model=d_model,
            nhead=nhead,
            transformer_layers=transformer_layers,
            output_size=output_size,
            dropout=dropout,
        )
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=1e-5)
        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode="min", patience=5, factor=0.5
        )
        self.criterion = nn.HuberLoss()
        self.history: dict = {"train_loss": [], "val_loss": []}

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_val: Optional[np.ndarray] = None,
        y_val: Optional[np.ndarray] = None,
    ) -> dict:
        """
        Train the ensemble model with early stopping.

        Args:
            X_train: (samples, seq_len, features)
            y_train: (samples, horizon)
            X_val: validation features (optional)
            y_val: validation targets (optional)

        Returns:
            Training history dict
        """
        train_dataset = TensorDataset(
            torch.tensor(X_train, dtype=torch.float32),
            torch.tensor(y_train, dtype=torch.float32),
        )
        train_loader = DataLoader(train_dataset, batch_size=self.batch_size, shuffle=False)

        use_val = X_val is not None and y_val is not None
        best_val_loss = float("inf")
        epochs_no_improve = 0
        best_state = None

        self.model.train()
        for epoch in range(1, self.epochs + 1):
            epoch_loss = self._train_epoch(train_loader)
            self.history["train_loss"].append(epoch_loss)

            if use_val:
                val_loss = self._eval(X_val, y_val)
                self.history["val_loss"].append(val_loss)
                self.scheduler.step(val_loss)

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    epochs_no_improve = 0
                    best_state = {k: v.clone() for k, v in self.model.state_dict().items()}
                else:
                    epochs_no_improve += 1
                    if epochs_no_improve >= self.patience:
                        logger.info(f"Early stopping at epoch {epoch}")
                        break

                if epoch % 10 == 0:
                    logger.info(
                        f"Epoch {epoch}/{self.epochs} | train_loss={epoch_loss:.6f} | val_loss={val_loss:.6f}"
                    )
            else:
                if epoch % 10 == 0:
                    logger.info(f"Epoch {epoch}/{self.epochs} | train_loss={epoch_loss:.6f}")

        if best_state is not None:
            self.model.load_state_dict(best_state)

        return self.history

    def _train_epoch(self, loader: DataLoader) -> float:
        self.model.train()
        total_loss = 0.0
        for X_batch, y_batch in loader:
            self.optimizer.zero_grad()
            pred = self.model(X_batch)
            loss = self.criterion(pred, y_batch)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            self.optimizer.step()
            total_loss += loss.item()
        return total_loss / len(loader)

    def _eval(self, X: np.ndarray, y: np.ndarray) -> float:
        self.model.eval()
        with torch.no_grad():
            X_t = torch.tensor(X, dtype=torch.float32)
            y_t = torch.tensor(y, dtype=torch.float32)
            pred = self.model(X_t)
            loss = self.criterion(pred, y_t)
        return loss.item()

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Return predictions as numpy array."""
        return self.model.predict(X)

    def save(self, path: Optional[str] = None):
        """Persist model weights to disk."""
        if path is None:
            path = os.path.join(self.model_dir, "ensemble_model.pt")
        torch.save(self.model.state_dict(), path)
        logger.info(f"Model saved to {path}")

    def load(self, path: Optional[str] = None):
        """Load model weights from disk."""
        if path is None:
            path = os.path.join(self.model_dir, "ensemble_model.pt")
        self.model.load_state_dict(torch.load(path, map_location="cpu"))
        logger.info(f"Model loaded from {path}")

    def cross_validate(
        self, X: np.ndarray, y: np.ndarray, n_splits: int = 5
    ) -> dict:
        """
        Walk-forward time-series cross-validation.

        Returns mean and std of validation losses.
        """
        tscv = TimeSeriesSplit(n_splits=n_splits)
        val_losses = []

        for fold, (train_idx, val_idx) in enumerate(tscv.split(X)):
            X_tr, X_vl = X[train_idx], X[val_idx]
            y_tr, y_vl = y[train_idx], y[val_idx]

            # Re-initialize model for each fold
            self.model.apply(self._reset_weights)
            self.optimizer = torch.optim.AdamW(
                self.model.parameters(), lr=self.optimizer.param_groups[0]["lr"]
            )

            self.train(X_tr, y_tr, X_vl, y_vl)
            val_loss = self._eval(X_vl, y_vl)
            val_losses.append(val_loss)
            logger.info(f"CV Fold {fold + 1}/{n_splits}: val_loss={val_loss:.6f}")

        return {
            "val_losses": val_losses,
            "mean_val_loss": float(np.mean(val_losses)),
            "std_val_loss": float(np.std(val_losses)),
        }

    @staticmethod
    def _reset_weights(module):
        if hasattr(module, "reset_parameters"):
            module.reset_parameters()
