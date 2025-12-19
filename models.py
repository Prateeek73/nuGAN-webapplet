from libraries import *
from utils import *


#---GENERATORS
class G_rodriguez_p311(nn.Module):

    def main_module(self, inchn):
        return nn.Sequential(
            nn.ConvTranspose2d(inchn, 256, 5, 2, 2, output_padding=1, bias=False), #---256,4,4
            nn.BatchNorm2d(256),
            nn.ReLU(True),

            nn.ConvTranspose2d(256, 128, 5, 2, 2, output_padding=1, bias=False), #---128,8,8
            nn.BatchNorm2d(128),
            nn.ReLU(True),

            nn.ConvTranspose2d(128, 128, 3, 1, 1, output_padding=0, bias=False), #---128,8,8
            nn.BatchNorm2d(128),
            nn.ReLU(True),

            nn.ConvTranspose2d(128, 64, 5, 2, 2, output_padding=1, bias=False), #---64,16,16
            nn.BatchNorm2d(64),
            nn.ReLU(True),

            nn.ConvTranspose2d(64, 64, 3, 1, 1, output_padding=0, bias=False), #---64,16,16
            nn.BatchNorm2d(64),
            nn.ReLU(True),

            nn.ConvTranspose2d(64, 1, 5, 2, 2, output_padding=1, bias=False), #---32,32,32
            nn.Tanh()
            )

    def __init__(self, nz, MCHN):
        super(G_rodriguez_p311, self).__init__()
        self.linear = torch.nn.Linear(MCHN+nz+MCHN, 512*16*16)
        self.deconvs = self.main_module(512)
        
    def forward(self, z, params, MCHN):
        if len(z.shape)!=2:
            z = z.squeeze()
        assert len(z.shape)==2, 'check latent vector dimensions'
        BS = z.shape[0]
        params = params.view(-1,1).repeat(1,MCHN)
        z = torch.cat((params,z,params), dim=1)
        z = self.linear(z)
        z = z.view(BS,512,16,16)
        z = self.deconvs(z)
        return z


#---DISCRIMINATORS
class D_rodriguez_wgan(nn.Module):

    def main_module(self, inchn):
        return nn.Sequential(
            nn.Conv2d(inchn, 64, 5, 2, 2, bias=False), #---128^2
            nn.BatchNorm2d(64),
            nn.LeakyReLU(0.2),

            nn.Conv2d(64,128, 5, 2, 2, bias=False), #---64^2
            nn.BatchNorm2d(128),
            nn.LeakyReLU(0.2),

            nn.Conv2d(128, 256, 5, 2, 2, bias=False), #---32^2
            nn.BatchNorm2d(256),
            nn.LeakyReLU(0.2),

            nn.Conv2d(256, 512, 5, 2, 2, bias=False), #---16^2
            nn.BatchNorm2d(512),
            nn.LeakyReLU(0.2),
            )

    def __init__(self, MCHN):
        super(D_rodriguez_wgan, self).__init__()
        self.convs = self.main_module(1)
        self.linear = torch.nn.Linear(MCHN+512*16*16+MCHN,1)
        
    def forward(self, x, params, MCHN):
        assert len(x.shape)==4, 'check data dimensions'
        BS = x.shape[0]
        x = self.convs(x)
        x = x.view(BS,512*16*16)

        params = params.view(-1,1).repeat(1,MCHN)
        x = torch.cat((params,x,params), dim=1)
        x = self.linear(x)
        #x = torch.nn.Sigmoid()(x) ---No sigmoid in last layer of a WGAN Discriminator
        return x