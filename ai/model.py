import torch
import torch.nn as nn
import torch.nn.functional as F

class XiangqiNet(nn.Module):
    def __init__(self):
        super(XiangqiNet, self).__init__()
        # Input: 14 channel (quân cờ)
        self.conv1 = nn.Conv2d(14, 64, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(64)
        
        self.conv2 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(128)
        
        self.conv3 = nn.Conv2d(128, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        
        # Flatten: 128 channel * 10 row * 9 col
        self.fc1 = nn.Linear(128 * 10 * 9, 512)
        self.dropout = nn.Dropout(0.3)
        self.fc2 = nn.Linear(512, 1) # 1 giá trị output

    def forward(self, x):
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = F.relu(self.bn3(self.conv3(x)))
        
        x = x.view(-1, 128 * 10 * 9) # Duỗi thẳng
        x = F.relu(self.fc1(x))
        x = self.dropout(x)
        x = torch.tanh(self.fc2(x)) # Output range [-1, 1]
        return x