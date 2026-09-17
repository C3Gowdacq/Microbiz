"""
loss.py -- ELBO loss components for the Reconstructed VAE.

Implements:
  reconstruction_loss:  MSE across X, A, B reconstructions
  regression_loss:      MSE between predicted and actual sales
  kl_divergence:        Closed-form KL between two diagonal Gaussians
  total_kl_loss:        KL summed across all four latents (z, s, v, d)
  vae_loss:             Full negative ELBO combining all components

References:
  - Base paper Eq. 3, 15-16
  - MicroBizAI_Architecture.md Section 5.4
"""

import torch
import torch.nn.functional as F

# Small epsilon to prevent log(0) and division-by-zero in KL computation
EPS = 1e-6


def reconstruction_loss(x_hat, x, a_hat, a, b_hat, b):
    """
    MSE reconstruction loss summed across the three reconstruction targets.

    Each component uses reduction='mean' (averaged over batch and feature dims),
    then the three component losses are summed. This gives equal weight to each
    reconstruction target regardless of their different dimensionalities (14/7/4).
    Without this, X would dominate simply because it has more dimensions.

    Args:
        x_hat, x: (batch_size, x_dim) predicted and actual X
        a_hat, a: (batch_size, a_dim) predicted and actual A
        b_hat, b: (batch_size, b_dim) predicted and actual B

    Returns:
        Scalar tensor: sum of three mean-MSE losses
    """
    loss_x = F.mse_loss(x_hat, x, reduction="mean")
    loss_a = F.mse_loss(a_hat, a, reduction="mean")
    loss_b = F.mse_loss(b_hat, b, reduction="mean")
    return loss_x + loss_a + loss_b


def regression_loss(y_hat, y):
    """
    MSE loss between predicted and actual (possibly calibrated) sales.

    Args:
        y_hat: (batch_size, 1) model prediction
        y:     (batch_size, 1) target (raw or calibrated)

    Returns:
        Scalar tensor: mean squared error
    """
    return F.mse_loss(y_hat, y, reduction="mean")


def kl_divergence(mu_post, sigma_post, mu_prior, sigma_prior):
    """
    Closed-form KL divergence between two diagonal Gaussians:

      KL(q || p) = KL(N(mu_post, sigma_post^2) || N(mu_prior, sigma_prior^2))
                 = log(sigma_prior / sigma_post)
                   + (sigma_post^2 + (mu_post - mu_prior)^2) / (2 * sigma_prior^2)
                   - 0.5

    Summed over the latent dimension, averaged over the batch.

    Args:
        mu_post:    (batch_size, latent_dim)
        sigma_post: (batch_size, latent_dim), must be > 0
        mu_prior:   (batch_size, latent_dim)
        sigma_prior:(batch_size, latent_dim), must be > 0

    Returns:
        Scalar tensor: mean KL divergence over the batch
    """
    # Add epsilon for numerical stability
    sigma_post = sigma_post + EPS
    sigma_prior = sigma_prior + EPS

    kl = (
        torch.log(sigma_prior / sigma_post)
        + (sigma_post ** 2 + (mu_post - mu_prior) ** 2) / (2 * sigma_prior ** 2)
        - 0.5
    )

    # Sum over latent dimensions, mean over batch
    return kl.sum(dim=1).mean()


def total_kl_loss(posterior_dict, prior_dict):
    """
    Sum KL divergence across all four latent variables (z, s, v, d).

    Args:
        posterior_dict: {name: (mu, sigma)} from PosteriorNetwork
        prior_dict:     {name: (mu, sigma)} from PriorNetwork

    Returns:
        Scalar tensor: total KL loss (sum of four KL terms)
    """
    total = torch.tensor(0.0, device=next(iter(posterior_dict.values()))[0].device)

    for name in ["z", "s", "v", "d"]:
        mu_post, sigma_post = posterior_dict[name]
        mu_prior, sigma_prior = prior_dict[name]
        total = total + kl_divergence(mu_post, sigma_post, mu_prior, sigma_prior)

    return total


def vae_loss(model_output, X, A, B, y, tau=0.1):
    """
    Full negative ELBO loss for the Reconstructed VAE.

    Combines reconstruction, regression, and KL divergence losses:
        loss = reconstruction_loss + regression_loss + tau * total_kl_loss

    NOTE: This is the NEGATIVE ELBO (we ADD the KL term, weighted by tau,
    to the loss terms we're minimizing). The paper's Eq.3/Eq.15 displays
    the ELBO as a maximization objective with a MINUS KL sign; here the
    sign is flipped because PyTorch optimizers MINIMIZE.

    Args:
        model_output: dict from ReconstructedVAE.forward()
        X: (batch_size, x_dim) original X tensor
        A: (batch_size, a_dim) original A tensor
        B: (batch_size, b_dim) original B tensor
        y: (batch_size, 1) target sales (raw or calibrated)
        tau: KL weight (default 0.1, controls recon-KL balance)

    Returns:
        dict with keys:
          'total':      total loss (scalar)
          'recon_loss': reconstruction component (scalar)
          'reg_loss':   regression component (scalar)
          'kl_loss':    KL divergence component before tau weighting (scalar)
    """
    recon = reconstruction_loss(
        model_output["x_hat"], X,
        model_output["a_hat"], A,
        model_output["b_hat"], B,
    )

    reg = regression_loss(model_output["y_hat"], y)

    kl = total_kl_loss(model_output["posterior"], model_output["prior"])

    total = recon + reg + tau * kl

    return {
        "total": total,
        "recon_loss": recon,
        "reg_loss": reg,
        "kl_loss": kl,
    }
