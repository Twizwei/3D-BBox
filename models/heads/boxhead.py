import torch
from torch import nn

__all__ = [
    'BoxHead'
]

def fbr_layer(in_size, out_size, bias=False):
    return nn.Sequential(
        nn.Linear(in_size, out_size, bias=bias),
        nn.BatchNorm1d(out_size),
        nn.ReLU(inplace=True)
    )

class BoxHead(nn.Module):

    def __init__(
            self,
            in_size=512*7*7,
            num_bins=2,
            d_hidden_sizes=[512],
            a_hidden_sizes=[256],
            c_hidden_sizes=[256],
            init_weights=True
        ):
        super(BoxHead, self).__init__()

        self.in_size = in_size
        self.num_bins = num_bins

        self.d_layers = self._make_fc_layers(d_hidden_sizes, 3)
        self.a_layers = self._make_fc_layers(a_hidden_sizes, num_bins*2)
        self.c_layers = self._make_fc_layers(c_hidden_sizes, num_bins)

        if init_weights:
            self.init_weights()
    
    def _make_fc_layers(self, hidden_sizes, out_size):
        fc_layers = []
        pre_size = self.in_size
        for hidden_size in hidden_sizes:
            fc_layers.append(fbr_layer(pre_size, hidden_size))
            pre_size = hidden_size
        fc_layers.append(nn.Linear(pre_size, out_size))
        return nn.Sequential(*fc_layers)
    
    def init_weights(self):
        for m in self.modules():
            if isinstance(m, nn.BatchNorm1d):
                nn.init.constant_(m.weight, 1)
                nn.init.constant_(m.bias, 0)
            elif isinstance(m, nn.Linear):
                nn.init.normal_(m.weight, 0, 0.01)
                if m.bias is not None:
                    nn.init.constant_(m.bias, 0)
    
    def forward(self, x):
        """
        Input:
            x: Tensor(N, self.in_size)

        Return:
            dimensions: Tensor(N, 3)
            delta_theta_l: Tensor(N, num_bins)
            confidences: Tensor(N, num_bins)
        """

        # forward to fc layers
        dimensions = self.d_layers(x)
        delta_theta_l = self.a_layers(x)
        confidences = self.c_layers(x)

        # reshape and normalize for theta_l
        delta_theta_l = delta_theta_l.view(-1, self.num_bins, 2)
        delta_theta_l = torch.atan2(delta_theta_l[:, :, 1], delta_theta_l[:, :, 0])

        return dimensions, delta_theta_l, confidences


# debug
if __name__ == '__main__':
    head = BoxHead(in_size=512)
    fake_input = torch.randn(8, 512)
    d, t, c = head(fake_input)
    print(d.size())
    print(t.size())
    print(c.size())