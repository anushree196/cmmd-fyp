"""Stage 1 model: one shared image encoder for both views, View Attention, age, and a 2-class head.

    CC  image --\                         /-- weight w_cc --\
                 >-- EfficientNet-B3 --<                     >-- weighted sum (1536) --\
    MLO image --/   (same weights)        \-- weight w_mlo -/                           >-- concat -> head -> 2 logits
    age ---------------------------------------- small MLP (32) -----------------------/

View Attention: the model scores each view's features and turns the two scores into weights that add up to 1
(softmax), so for every breast it decides how much to rely on the CC and how much on the MLO.
"""
import timm
import torch
from torch import nn

# Images arrive as 0..1 greyscale. ImageNet-trained encoders expect roughly zero-mean input; these are the
# averages of the ImageNet red/green/blue means and standard deviations.
GREY_MEAN, GREY_STD = 0.449, 0.226


class DualViewNet(nn.Module):
    def __init__(self, backbone="efficientnet_b3", pretrained=True, n_classes=2, n_clinical=1, dropout=0.3):
        super().__init__()
        # in_chans=1: timm adapts the ImageNet weights of the first layer to a single grey channel
        self.encoder = timm.create_model(backbone, pretrained=pretrained, num_classes=0, in_chans=1)
        d = self.encoder.num_features                      # 1536 for EfficientNet-B3
        self.view_score = nn.Linear(d, 1)                   # one score per view
        self.clinical = nn.Sequential(nn.Linear(n_clinical, 32), nn.ReLU())
        self.head = nn.Sequential(nn.Dropout(dropout), nn.Linear(d + 32, n_classes))

    def forward(self, cc, mlo, clin):
        b = cc.shape[0]
        x = (torch.cat([cc, mlo]) - GREY_MEAN) / GREY_STD  # both views through the encoder in one pass
        feats = self.encoder(x)
        views = torch.stack([feats[:b], feats[b:]], dim=1)            # (batch, 2 views, d)
        weights = torch.softmax(self.view_score(views).squeeze(-1), dim=1)  # (batch, 2), rows sum to 1
        fused = (weights.unsqueeze(-1) * views).sum(dim=1)             # (batch, d)
        logits = self.head(torch.cat([fused, self.clinical(clin)], dim=1))
        return logits, weights
