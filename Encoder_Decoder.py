{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "name": "Encoder_Decoder.py",
      "version": "0.3.2",
      "provenance": [],
      "collapsed_sections": [],
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/ArghyaPal/Zero-shot-task-transfer/blob/master/Encoder_Decoder.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "metadata": {
        "id": "KzA8zOxF6COe",
        "colab_type": "code",
        "colab": {}
      },
      "source": [
        "'''\n",
        "A slight change from our paper description. In the paper we used ResNet-50 as Encoder.\n",
        "However, we later changed it to UNet as we find it more concise\n",
        "\n",
        "'''\n",
        "\n",
        "import torch\n",
        "from torch.autograd import Variable\n",
        "import torchvision\n",
        "import torch.nn as nn\n",
        "import torch.nn.functional as F\n",
        "from torchvision import datasets, models,transforms\n",
        "import torch.optim as optim\n",
        "from torch.optim import lr_scheduler\n",
        "import numpy as np\n",
        "import os\n",
        "from torch.autograd import Function\n",
        "from torch.autograd import Variable\n",
        "from collections import OrderedDict\n",
        "import math\n",
        "import torchvision.models as models\n",
        "import random\n",
        "from resnet import *\n",
        "\n",
        "zsize = 100\n",
        "batch_size = 50\n",
        "iterations =  100\n",
        "learningRate= 0.001\n",
        "\n",
        "\n",
        "def weights_init_normal(m):\n",
        "    classname = m.__class__.__name__\n",
        "    if classname.find(\"Conv\") != -1:\n",
        "        torch.nn.init.normal_(m.weight.data, 0.0, 0.02)\n",
        "    elif classname.find(\"BatchNorm2d\") != -1:\n",
        "        torch.nn.init.normal_(m.weight.data, 1.0, 0.02)\n",
        "        torch.nn.init.constant_(m.bias.data, 0.0)\n",
        "\n",
        "##############################\n",
        "#           U-NET\n",
        "##############################\n",
        "class UNetUp(nn.Module):\n",
        "    def __init__(self, in_size, out_size, dropout=0.0):\n",
        "        super(UNetUp, self).__init__()\n",
        "        layers = [\n",
        "            nn.ConvTranspose2d(in_size, out_size, 3, 1, 1, bias=False),\n",
        "            nn.InstanceNorm2d(out_size),\n",
        "            nn.ReLU(inplace=True),\n",
        "        ]\n",
        "        if dropout:\n",
        "            layers.append(nn.Dropout(dropout))\n",
        "\n",
        "        self.model = nn.Sequential(*layers)\n",
        "\n",
        "    def forward(self, x, skip_input):\n",
        "        x = self.model(x)\n",
        "        #print(x.size())\n",
        "        #print(skip_input.size())\n",
        "        x = torch.cat((x, skip_input), 1)\n",
        "\n",
        "        return x\n",
        "        \n",
        "class Encoder(nn.Module):\n",
        "\n",
        "    def __init__(self, block, layers, num_classes=23):\n",
        "        self.inplanes = 64\n",
        "        super(Encoder, self).__init__()\n",
        "        self.down1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3,bias=False)\n",
        "        self.bn1 = nn.BatchNorm2d(64)\n",
        "        self.relu = nn.ReLU(inplace=True)\n",
        "        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)\n",
        "        self.down2 = self._make_layer(block, 64, layers[0])\n",
        "        self.down3 = self._make_layer(block, 128, layers[1], stride=2)\n",
        "        self.down4 = self._make_layer(block, 256, layers[2], stride=2)\n",
        "        self.down5 = self._make_layer(block, 512, layers[3], stride=2)\n",
        "      \n",
        "        for m in self.modules():\n",
        "            if isinstance(m, nn.Conv2d):\n",
        "                n = m.kernel_size[0] * m.kernel_size[1] * m.out_channels\n",
        "                m.weight.data.normal_(0, math.sqrt(2. / n))\n",
        "            elif isinstance(m, nn.BatchNorm2d):\n",
        "                m.weight.data.fill_(1)\n",
        "                m.bias.data.zero_()\n",
        "\n",
        "    def _make_layer(self, block, planes, blocks, stride=1):\n",
        "        downsample = None\n",
        "        if stride != 1 or self.inplanes != planes * block.expansion:\n",
        "            downsample = nn.Sequential(\n",
        "                nn.Conv2d(self.inplanes, planes * block.expansion,\n",
        "                          kernel_size=1, stride=stride, bias=False),\n",
        "                nn.BatchNorm2d(planes * block.expansion),\n",
        "            )\n",
        "\n",
        "        layers = []\n",
        "        layers.append(block(self.inplanes, planes, stride, downsample))\n",
        "        self.inplanes = planes * block.expansion\n",
        "        for i in range(1, blocks):\n",
        "            layers.append(block(self.inplanes, planes))\n",
        "\n",
        "        return nn.Sequential(*layers)\n",
        "\n",
        "    def forward(self, x):\n",
        "    \td1 = self.down1(x)\n",
        "    \td2 = self.down2(d1)\n",
        "    \td3 = self.down3(d2)\n",
        "    \td4 = self.down4(d3) \n",
        "    \td5 = self.down5(d4)\n",
        "    \treturn d1,d2,d3,d4,d5\n",
        "\n",
        "encoder = Encoder(Bottleneck, [3, 4, 6, 3])\n",
        "\n",
        "\n",
        "class Decoder(nn.Module):\n",
        "        def __init__(self):\n",
        "                super(Decoder, self).__init__()\n",
        "                self.up1 = nn.ConvTranspose2d(2048, 512, 3, 1, 1, bias=False)\n",
        "                self.up2 = UNetUp(512, 512, dropout=0.5)\n",
        "                self.up3 = nn.ConvTranspose2d(2560, 256, 3, 2, 1, bias=False)\n",
        "                self.up4 = UNetUp(256, 256, dropout=0.5)\n",
        "                self.up5 = nn.ConvTranspose2d(1280, 128, 3, 2, 1, bias=False)\n",
        "                self.up6 = UNetUp(128, 128, dropout=0.5)\n",
        "                self.up7 = nn.ConvTranspose2d(640, 64, 4, 2, 1, bias=False)\n",
        "                self.up8 = UNetUp(64, 64, dropout=0.5)\n",
        "                self.up9 = UNetUp(320, 3, dropout=0.5)\n",
        "                self.up10 = nn.ConvTranspose2d(67, 3, 4, 2, 1, bias=False)\n",
        "                self.up11 = UNetUp(3, 3, dropout=0.5)\n",
        "                self.up12 = nn.ConvTranspose2d(6, 1, 1, bias=False) \n",
        "                # pleae change the number of output channels according to your task\n",
        "                \n",
        "        def forward(self, d1, d2, d3, d4, d5):\n",
        "                u1 = self.up1(d5)    \n",
        "                u2 = self.up2(u1,d5)\n",
        "                u3 = self.up3(u2)\n",
        "                u4 = self.up4(u3, d4)\n",
        "                u5 = self.up5(u4)\n",
        "                u6 = self.up6(u5, d3)\n",
        "                u7 = self.up7(u6)\n",
        "                u8 = self.up8(u7, d2)\n",
        "                u9 = self.up9(u8, d1)\n",
        "                u10 = self.up10(u9)\n",
        "                return u10\n",
        "\n",
        "decoder = Decoder()\n",
        "\n",
        "\n",
        "#########################################################\n",
        "class Autoencoder(nn.Module):\n",
        "    def __init__(self):\n",
        "        super(Autoencoder,self).__init__()\n",
        "        self.encoder = encoder\n",
        "        self.decoder = decoder\n",
        "        \n",
        "    def forward(self,x):\n",
        "        d1, d2, d3, d4, d5 = self.encoder(x)\n",
        "        x = self.decoder(d1, d2, d3, d4, d5)\n",
        "        return x"
      ],
      "execution_count": 0,
      "outputs": []
    }
  ]
}