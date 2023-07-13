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



## 7.12

目前的想法是，新建一个神经网络（暂时称为A）。该网络包含三个部分，第一个称为recorder，第二个称为target，第三个称为initial。思路是通过A来记录一段时间（例如一个回合内）相同或相似的状态动作对出现的次数，如果相同或相似的状态动作对出现的次数太多（出现的次数多可能来自于RND的内在奖励），则降低这一步的内在奖励权重（思路是如果相同的状态动作对能够获得环境奖励的话，那么即使降低内在奖励权重，也不会过多影响智能体下次继续探索该状态）。如何衡量相同或相似的状态动作对出现的次数？只需要通过recorder和target的误差即可。

在创建该网络时，recorder进行随机初始化，target和initial都是固定不动的网络。initial复制recorder的网络参数。当训练过程中与环境交互得到新的观测时，将当前状态($state$而不是$s{\_}prime$)和动作$action$拼接在一起传递给A网络。通过recorder和target的误差来更新recorder网络，并通过initial网络得到当前状态动作下的起始误差，也即误差上界。通过以下公式将recorder和target的误差归一化到[0,1]范围内:
$$
x_{norm} = \frac{x-0}{b-0}=\frac{x}{b}
$$
其中，$x$为当前recorder和target的误差，$b$为误差上界(即initial网络的输出)。$x$的值越小，则说明误差越小，说明该状态动作对出现的次数越多。

至于recorder和target网络究竟是每回合重置，还是究竟怎么重置，需要实验探究。

A网络如何进行更新？

我们希望做的是使得recorder和target网络的预测接近，因此应该使用它们的误差作为网络更新的参数。

首先，我们得到initial网络的输出，即初始误差。我们已经得到了当前输出和目标输出，已知当前误差。

1. 网络最初的输出为$X$，即起始误差，也是误差上界。

2. 当前recorder输出为$Y$，target输出为$Z$。当前误差为$f(Y-Z)$(  误差使用均方误差损失函数)

3. 那么，当前状态动作对出现的频率为:
   $$
   \frac{f(Y-Z)-0}{X}=
   $$

## 7.13

最初使用的方式为:

```
 s_prime, extrinsic_reward, done, _, _, = env.step(action)
action_numpy = np.full((2,), action)
state_action = np.vstack((state, action_numpy))
state_action = torch.from_numpy(state_action).float().unsqueeze(0)
state_action = state_action.reshape(-1)
record, target = net(state_action)
coff = net.learn(state_action, record, target)

reward_weight = 0.01 + coff * (0.1 - 0.01)
```

但是效果非常差，考虑到环境。
