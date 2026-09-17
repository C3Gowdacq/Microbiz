"""
model.py -- Full ReconstructedVAE model wiring all components together.

Combines:
  - ClusterEmbedding (Part 4a): cluster_label -> c_n
  - PriorNetwork (Part 4b):     A, B, c_n -> prior {z,s,v,d: (mu,sigma)}
  - PosteriorNetwork (Part 4b): X, A, B, c_n -> posterior {z,s,v,d: (mu,sigma)}
  - ReconstructionDecoder:      sampled z,s,v,d -> x_hat, a_hat, b_hat
  - SalesRegressor (Eq. 14):    posterior mu_z, mu_s, mu_v, mu_d -> y_hat

References:
  - Base paper Eq. 4-14, Section 5.3-5.4
  - MicroBizAI_Architecture.md Section 5.3-5.4
"""

import torch
import torch.nn as nn

from dataset import ClusterEmbedding
from encoder import PriorNetwork, PosteriorNetwork, reparameterize
from decoder import ReconstructionDecoder, SalesRegressor


class ReconstructedVAE(nn.Module):
    """
    Full Reconstructed VAE model.

    Wires together clustering embedding, prior/posterior encoders,
    reconstruction decoder, and sales regressor into a single end-to-end model.

    forward() returns all intermediate outputs needed for the ELBO loss
    (Part 4d): prior/posterior distributions, sampled latents, reconstructions,
    and predicted sales.

    Args:
        x_dim:          X tensor dimensionality (default 14)
        a_dim:          A tensor dimensionality (default 7)
        b_dim:          B tensor dimensionality (default 4)
        num_clusters:   K, number of KMeans clusters (default 32)
        cluster_emb_dim: cluster embedding dimensionality (default 10)
        latent_dim:     dim of each latent z, s, v, d (default 64)
        prior_encoder_dim:   enc_A/enc_B output dim in PriorNetwork (default 64)
        prior_hidden_dim:    shared trunk dim in PriorNetwork (default 256)
        post_encoder_dim:    input encoder dim in PosteriorNetwork (default 128)
        decoder_hidden_dim:  hidden dim in each decoder head (default 128)
        regressor_hidden_dim: hidden dim in SalesRegressor (default 128)
        dropout_p:      dropout in PosteriorNetwork sigma path (default 0.1)
    """

    def __init__(
        self,
        x_dim=14,
        a_dim=7,
        b_dim=4,
        num_clusters=32,
        cluster_emb_dim=10,
        latent_dim=64,
        prior_encoder_dim=64,
        prior_hidden_dim=256,
        post_encoder_dim=128,
        decoder_hidden_dim=128,
        regressor_hidden_dim=128,
        dropout_p=0.1,
    ):
        super().__init__()

        # Store config for reference
        self.latent_dim = latent_dim
        self.num_clusters = num_clusters

        # Part 4a: Cluster embedding
        self.cluster_embedding = ClusterEmbedding(
            num_clusters=num_clusters,
            embedding_dim=cluster_emb_dim,
        )

        # Part 4b: Prior and Posterior networks
        self.prior_net = PriorNetwork(
            a_dim=a_dim,
            b_dim=b_dim,
            c_dim=cluster_emb_dim,
            encoder_dim=prior_encoder_dim,
            hidden_dim=prior_hidden_dim,
            latent_dim=latent_dim,
        )

        self.posterior_net = PosteriorNetwork(
            x_dim=x_dim,
            a_dim=a_dim,
            b_dim=b_dim,
            c_dim=cluster_emb_dim,
            encoder_dim=post_encoder_dim,
            latent_dim=latent_dim,
            dropout_p=dropout_p,
        )

        # Part 4c: Decoder and Regressor
        self.decoder = ReconstructionDecoder(
            latent_dim=latent_dim,
            x_dim=x_dim,
            a_dim=a_dim,
            b_dim=b_dim,
            hidden_dim=decoder_hidden_dim,
        )

        self.regressor = SalesRegressor(
            latent_dim=latent_dim,
            hidden_dim=regressor_hidden_dim,
        )

    def forward(self, X, A, B, cluster_label):
        """
        Full forward pass through the Reconstructed VAE.

        Args:
            X:             (batch_size, x_dim) -- temporal/promo features
            A:             (batch_size, a_dim) -- functional store attributes
            B:             (batch_size, b_dim) -- non-functional store attributes
            cluster_label: (batch_size,) LongTensor -- KMeans cluster IDs

        Returns:
            dict with keys:
              'prior':    {z,s,v,d: (mu, sigma)}
              'posterior': {z,s,v,d: (mu, sigma)}
              'sampled':  {z,s,v,d: tensor} -- reparameterized from POSTERIOR
              'x_hat':    (batch_size, x_dim)  -- reconstructed X
              'a_hat':    (batch_size, a_dim)  -- reconstructed A
              'b_hat':    (batch_size, b_dim)  -- reconstructed B
              'y_hat':    (batch_size, 1)      -- predicted sales
        """
        # 1. Cluster embedding: label -> dense vector c_n
        c_n = self.cluster_embedding(cluster_label)

        # 2. Prior: p(z,s,v,d | A, B, c_n)
        prior = self.prior_net(A, B, c_n)

        # 3. Posterior: q(z,s,v,d | X, A, B, c_n)
        posterior = self.posterior_net(X, A, B, c_n)

        # 4. Sample from POSTERIOR via reparameterization trick
        #    (prior is only used as KL divergence target, never sampled during training)
        sampled = {}
        for name in ["z", "s", "v", "d"]:
            mu, sigma = posterior[name]
            sampled[name] = reparameterize(mu, sigma)

        # 5. Reconstruct X, A, B from sampled latents
        x_hat, a_hat, b_hat = self.decoder(
            sampled["z"], sampled["s"], sampled["v"], sampled["d"]
        )

        # 6. Predict sales from POSTERIOR mu values (not sampled values, per Eq.14)
        #    The paper explicitly uses mu for the regressor input
        y_hat = self.regressor(
            posterior["z"][0],  # mu_z
            posterior["s"][0],  # mu_s
            posterior["v"][0],  # mu_v
            posterior["d"][0],  # mu_d
        )

        return {
            "prior": prior,
            "posterior": posterior,
            "sampled": sampled,
            "x_hat": x_hat,
            "a_hat": a_hat,
            "b_hat": b_hat,
            "y_hat": y_hat,
        }

    @torch.no_grad()
    def predict(self, X, A, B, cluster_label):
        """
        Inference-only convenience method. Returns just the predicted sales.

        Sets the model to eval mode, disables gradient computation,
        and returns only y_hat.

        Args:
            X, A, B, cluster_label: same as forward()

        Returns:
            y_hat: (batch_size, 1) -- predicted sales
        """
        was_training = self.training
        self.eval()

        outputs = self.forward(X, A, B, cluster_label)
        y_hat = outputs["y_hat"]

        if was_training:
            self.train()

        return y_hat
