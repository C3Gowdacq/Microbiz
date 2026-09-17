"""
encoder.py -- Prior and Posterior networks for the Reconstructed VAE.

Implements the four latent variables (z, s, v, d) per the base paper's Eq. 4-13
and Section 5.3 of MicroBizAI_Architecture.md.

Latent semantics:
  z: global group-level representation  (from X, A)
  s: global feature representation      (from X, A, B)
  v: local functional representation    (from A)
  d: local non-functional representation(from B)

Classes:
  PriorNetwork:     p(z,s,v,d | A, B, c_n)  -- prior conditioned on store attrs + cluster
  PosteriorNetwork: q(z,s,v,d | X, A, B, c_n) -- posterior conditioned on all observed data
  reparameterize(): mu + sigma * eps, eps ~ N(0, I)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


def reparameterize(mu, sigma):
    """
    Reparameterization trick: sample = mu + sigma * eps, eps ~ N(0, I).

    Called once per latent variable in the training loop (not baked into
    the network forward() so we can control sampling vs. deterministic mode).

    Args:
        mu:    (batch_size, latent_dim)
        sigma: (batch_size, latent_dim), must be positive

    Returns:
        sample: (batch_size, latent_dim)
    """
    eps = torch.randn_like(mu)
    return mu + sigma * eps


class PriorNetwork(nn.Module):
    """
    Prior network: p(z, s, v, d | A, B, c_n).

    Encodes store attributes A, B and cluster embedding c_n into
    prior distributions (mu, sigma) for each of the four latent variables.

    Architecture:
      enc_A(A) -> e_A           (one Linear layer)
      enc_B(B) -> e_B           (one Linear layer)
      concat [e_A, e_B, c_n] -> shared dense trunk h_prior
      Four separate mu/sigma heads on h_prior

    Args:
        a_dim:          dimensionality of A tensor (default 7)
        b_dim:          dimensionality of B tensor (default 4)
        c_dim:          dimensionality of cluster embedding c_n (default 10)
        encoder_dim:    output dim of enc_A and enc_B (default 64)
        hidden_dim:     dim of shared trunk h_prior (default 256)
        latent_dim:     dim of each latent variable z, s, v, d (default 64)
    """

    def __init__(self, a_dim=7, b_dim=4, c_dim=10,
                 encoder_dim=64, hidden_dim=256, latent_dim=64):
        super().__init__()

        # Small encoders for A and B (one Linear layer each, per the paper)
        self.enc_A = nn.Sequential(
            nn.Linear(a_dim, encoder_dim),
            nn.ReLU(),
        )
        self.enc_B = nn.Sequential(
            nn.Linear(b_dim, encoder_dim),
            nn.ReLU(),
        )

        # Shared dense trunk: concat(e_A, e_B, c_n) -> h_prior
        trunk_input_dim = encoder_dim + encoder_dim + c_dim
        self.trunk = nn.Sequential(
            nn.Linear(trunk_input_dim, hidden_dim),
            nn.ReLU(),
        )

        # Four separate mu/sigma head pairs (z, s, v, d)
        self.latent_names = ["z", "s", "v", "d"]

        self.mu_heads = nn.ModuleDict({
            name: nn.Linear(hidden_dim, latent_dim)
            for name in self.latent_names
        })
        self.sigma_heads = nn.ModuleDict({
            name: nn.Linear(hidden_dim, latent_dim)
            for name in self.latent_names
        })

    def forward(self, A, B, c_n):
        """
        Args:
            A:   (batch_size, a_dim)
            B:   (batch_size, b_dim)
            c_n: (batch_size, c_dim) -- cluster embedding from ClusterEmbedding

        Returns:
            dict: {name: (mu, sigma)} for name in ['z', 's', 'v', 'd']
                  mu, sigma each have shape (batch_size, latent_dim)
                  sigma is always positive (via softplus)
        """
        e_A = self.enc_A(A)
        e_B = self.enc_B(B)

        h_prior = self.trunk(torch.cat([e_A, e_B, c_n], dim=1))

        result = {}
        for name in self.latent_names:
            mu = self.mu_heads[name](h_prior)
            # Softplus ensures sigma > 0 (Eq. 7-8 in the paper)
            sigma = F.softplus(self.sigma_heads[name](h_prior))
            result[name] = (mu, sigma)

        return result


class PosteriorNetwork(nn.Module):
    """
    Posterior network: q(z, s, v, d | X, A, B, c_n).

    Encodes all observed data into posterior distributions for each latent,
    following the paper's exact latent semantics:
      e_z = enc(concat(X, A))      -> z   (global group-level + functional)
      e_s = enc(concat(X, A, B))   -> s   (global feature from all three)
      e_v = enc(A)                 -> v   (local functional)
      e_d = enc(B)                 -> d   (local non-functional)

    For each latent:
      mu   = BatchNorm(Linear(concat(e_*, c_n)))
      sigma = softplus(Dropout(PReLU(Linear(concat(e_*, c_n)))))

    Args:
        x_dim:          dimensionality of X tensor (default 14)
        a_dim:          dimensionality of A tensor (default 7)
        b_dim:          dimensionality of B tensor (default 4)
        c_dim:          dimensionality of cluster embedding c_n (default 10)
        encoder_dim:    output dim of each input encoder (default 128)
        latent_dim:     dim of each latent variable z, s, v, d (default 64)
        dropout_p:      dropout probability in sigma path (default 0.1)
    """

    def __init__(self, x_dim=14, a_dim=7, b_dim=4, c_dim=10,
                 encoder_dim=128, latent_dim=64, dropout_p=0.1):
        super().__init__()

        self.latent_names = ["z", "s", "v", "d"]

        # Input encoders: one Linear layer per the paper's exact semantics
        # z gets concat(X, A), s gets concat(X, A, B), v gets A, d gets B
        input_dims = {
            "z": x_dim + a_dim,       # concat(X, A) = 14 + 7 = 21
            "s": x_dim + a_dim + b_dim,  # concat(X, A, B) = 14 + 7 + 4 = 25
            "v": a_dim,                # A only = 7
            "d": b_dim,                # B only = 4
        }

        self.input_encoders = nn.ModuleDict({
            name: nn.Sequential(
                nn.Linear(input_dims[name], encoder_dim),
                nn.ReLU(),
            )
            for name in self.latent_names
        })

        # Mu path: concat(e_*, c_n) -> Linear -> BatchNorm -> mu
        head_input_dim = encoder_dim + c_dim

        self.mu_linears = nn.ModuleDict({
            name: nn.Linear(head_input_dim, latent_dim)
            for name in self.latent_names
        })
        self.mu_batchnorms = nn.ModuleDict({
            name: nn.BatchNorm1d(latent_dim)
            for name in self.latent_names
        })

        # Sigma path: concat(e_*, c_n) -> Linear -> PReLU -> Dropout -> softplus -> sigma
        self.sigma_linears = nn.ModuleDict({
            name: nn.Linear(head_input_dim, latent_dim)
            for name in self.latent_names
        })
        self.sigma_prelus = nn.ModuleDict({
            name: nn.PReLU(num_parameters=latent_dim)
            for name in self.latent_names
        })
        self.sigma_dropouts = nn.ModuleDict({
            name: nn.Dropout(p=dropout_p)
            for name in self.latent_names
        })

    def _build_input(self, name, X, A, B):
        """Concatenate the correct input tensors for each latent variable."""
        if name == "z":
            return torch.cat([X, A], dim=1)
        elif name == "s":
            return torch.cat([X, A, B], dim=1)
        elif name == "v":
            return A
        elif name == "d":
            return B
        else:
            raise ValueError(f"Unknown latent name: {name}")

    def forward(self, X, A, B, c_n):
        """
        Args:
            X:   (batch_size, x_dim)
            A:   (batch_size, a_dim)
            B:   (batch_size, b_dim)
            c_n: (batch_size, c_dim) -- cluster embedding

        Returns:
            dict: {name: (mu, sigma)} for name in ['z', 's', 'v', 'd']
                  mu, sigma each have shape (batch_size, latent_dim)
                  sigma is always positive (via softplus)
        """
        result = {}

        for name in self.latent_names:
            # Encode the appropriate input subset
            raw_input = self._build_input(name, X, A, B)
            e = self.input_encoders[name](raw_input)

            # Concatenate with cluster embedding
            h = torch.cat([e, c_n], dim=1)

            # Mu path: Linear -> BatchNorm
            mu = self.mu_batchnorms[name](self.mu_linears[name](h))

            # Sigma path: Linear -> PReLU -> Dropout -> softplus (ensures > 0)
            sigma_raw = self.sigma_linears[name](h)
            sigma_raw = self.sigma_prelus[name](sigma_raw)
            sigma_raw = self.sigma_dropouts[name](sigma_raw)
            sigma = F.softplus(sigma_raw)

            result[name] = (mu, sigma)

        return result
