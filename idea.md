# 创新点的一些简单想法

## 7.8

目前的想法是，使用注意力机制让智能体尽量避免在探索过程中做出这些动作:


- 采取动作后，智能体的状态没有改变
- 采取动作后，直接导致游戏结束（怎么判断是不是该动作导致游戏结束可能有点难）

计划是采用注意力机制来使得智能体更多关注自身附近的信息，如果智能体采取某个动作后，状态没有发生改变（或者变化非常小，因为智能体可能会做出该动作的帧但是对位置没有改变），那么需要使用注意力机制来降低这个操作的得分。

但是目前使用DQN+RND算法在Montezuma revenge环境中暂时还没有训练出效果，如果有可能还得换baseline。
CHATGPT给出的参考示例:
在Breakout环境中，我们可以使用注意力机制来关注无效的动作。以下是一个简单的示例，使用了PyTorch框架和OpenAI Gym库：

```python
import gym
import torch
import torch.nn as nn
import torch.nn.functional as F

class ActionPredictor(nn.Module):
    def __init__(self):
        super(ActionPredictor, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=8, stride=4)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=4, stride=2)
        self.conv3 = nn.Conv2d(64, 64, kernel_size=3, stride=1)
        self.fc1 = nn.Linear(7*7*64, 512)
        self.fc2 = nn.Linear(512, 4)  # 4 actions in Breakout

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = x.view(x.size(0), -1)  # flatten
        x = F.relu(self.fc1(x))

        return self.fc2(x)

env = gym.make('Breakout-v0')
model = ActionPredictor()

state = env.reset()
state = torch.from_numpy(state).permute(2, 0, 1).unsqueeze(0).float()  # reshape and normalize to [0, 1]

action_values = model(state)
action = action_values.max(1)[1].item()  # choose action with highest value

next_state, reward, done, _ = env.step(action)

# calculate state change
state_change = torch.norm(state - torch.from_numpy(next_state).permute(2, 0, 1).unsqueeze(0).float())

# if state change is small and game is over, consider this action as invalid
if state_change < 0.1 and done:
    action_values[0, action] = -float('inf')  # set value to negative infinity

# apply attention mechanism
attention_weights = F.softmax(action_values, dim=1)
action_values = action_values * attention_weights

# choose action with highest value
action = action_values.max(1)[1].item()

next_state, reward, done, _ = env.step(action)
```

在这个示例中，我们首先使用一个神经网络模型来预测每个动作的价值。然后，我们计算状态的改变，如果一个动作导致的状态改变小于一个阈值，并且游戏结束，那么我们认为这个动作是无效的，将其价值设置为负无穷。

然后，我们应用一个注意力机制，这个机制会关注无效的动作。我们使用softmax函数来计算每个动作的注意力权重，然后将这些权重应用到动作的价值上。

最后，我们选择价值最高的动作，并在环境中执行这个动作。
