"""
decoder.py -- Reconstruction decoder and Sales regressor for the Reconstructed VAE.

Implements:
  ReconstructionDecoder: reconstructs X, A, B from sampled latent variables
  SalesRegressor:        predicts Sales from posterior mu values (Eq. 14)

References:
  - Base paper Eq. 14, Section 5.3-5.4
  - MicroBizAI_Architecture.md Section 5.3-5.4
"""

import torch
import torch.nn as nn


class ReconstructionDecoder(nn.Module):
    """
    Three small decoder heads reconstructing X, A, B from the sampled latents.

    Wiring (implementation choice, documented):
      x_hat = dec_x(concat(z, s))    -- X uses z (global group-level) and s (global feature)
      a_hat = dec_a(concat(v, s))    -- A uses v (functional local) and s (global connector)
      b_hat = dec_b(concat(d, s))    -- B uses d (non-functional local) and s (global connector)

    NOTE: The paper is not fully explicit about which latents feed which
    reconstruction head beyond "z,v,d point to x*,A*,B* respectively, and s
    connects them all." This wiring is a reasonable, documented interpretation
    where s acts as the shared global feature that bridges all reconstructions,
    while z/v/d provide the group-specific information. This is an implementation
    choice, not a verbatim paper quote.

    Args:
        latent_dim: dimensionality of each latent variable (default 64)
        x_dim:      output dim for X reconstruction (default 14)
        a_dim:      output dim for A reconstruction (default 7)
        b_dim:      output dim for B reconstruction (default 4)
        hidden_dim: hidden layer dim in each decoder head (default 128)
    """

    def __init__(self, latent_dim=64, x_dim=14, a_dim=7, b_dim=4, hidden_dim=128):
        super().__init__()

        # Each head takes concat of two latent vectors (2 * latent_dim)
        decoder_input_dim = latent_dim * 2

        # X decoder: concat(z, s) -> hidden -> x_hat
        self.dec_x = nn.Sequential(
            nn.Linear(decoder_input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, x_dim),
        )

        # A decoder: concat(v, s) -> hidden -> a_hat
        self.dec_a = nn.Sequential(
            nn.Linear(decoder_input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, a_dim),
        )

        # B decoder: concat(d, s) -> hidden -> b_hat
        self.dec_b = nn.Sequential(
            nn.Linear(decoder_input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, b_dim),
        )

    def forward(self, z, s, v, d):
        """
        Args:
            z: (batch_size, latent_dim) -- sampled global group-level latent
            s: (batch_size, latent_dim) -- sampled global feature latent
            v: (batch_size, latent_dim) -- sampled functional local latent
            d: (batch_size, latent_dim) -- sampled non-functional local latent

        Returns:
            x_hat: (batch_size, x_dim)  -- reconstructed X
            a_hat: (batch_size, a_dim)  -- reconstructed A
            b_hat: (batch_size, b_dim)  -- reconstructed B
        """
        x_hat = self.dec_x(torch.cat([z, s], dim=1))
        a_hat = self.dec_a(torch.cat([v, s], dim=1))
        b_hat = self.dec_b(torch.cat([d, s], dim=1))
        return x_hat, a_hat, b_hat


class SalesRegressor(nn.Module):
    """
    2-layer sales regressor per the paper's Eq. 14.

    Takes the POSTERIOR mu values (not sampled latents) for all four latent
    variables and predicts Sales.

    Architecture:
      concat(mu_z, mu_s, mu_v, mu_d) -> Linear -> Sigmoid -> Linear -> y_hat

    NOTE: Sigmoid is applied after fc1 as the activation (per Eq. 14).
    No activation after fc2 since Sales is a continuous, unbounded target.

    Args:
        latent_dim: dim of each latent variable (default 64, so input = 4*64 = 256)
        hidden_dim: hidden layer dim (default 128)
    """

    def __init__(self, latent_dim=64, hidden_dim=128):
        super().__init__()

        input_dim = latent_dim * 4  # concat of 4 mu vectors

        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.activation = nn.Sigmoid()  # Per Eq. 14 in the paper
        self.fc2 = nn.Linear(hidden_dim, 1)

    def forward(self, mu_z, mu_s, mu_v, mu_d):
        """
        Args:
            mu_z: (batch_size, latent_dim) -- posterior mu for z
            mu_s: (batch_size, latent_dim) -- posterior mu for s
            mu_v: (batch_size, latent_dim) -- posterior mu for v
            mu_d: (batch_size, latent_dim) -- posterior mu for d

        Returns:
            y_hat: (batch_size, 1) -- predicted sales (raw, unbounded)
        """
        h = torch.cat([mu_z, mu_s, mu_v, mu_d], dim=1)
        h = self.activation(self.fc1(h))
        y_hat = self.fc2(h)
        return y_hat
