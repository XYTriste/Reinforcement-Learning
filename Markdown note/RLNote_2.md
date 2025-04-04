---
title: "Reinforcement Learning note"
author: Yu Xia
date: May 13, 2023
output: pdf_document
---
# 强化学习的内在奖励
## 什么是内在奖励？
强化学习中的内在奖励，指的是智能体在与环境交互的过程中，由于感受到了“成长”而获得的自我奖励。区别于外部奖励，外部奖励是智能体通过与环境交互得到反馈的奖励信号。我们可以从这样的一个例子中理解什么是外部奖励，什么是内在奖励:
>当涉及到内在奖励和外部奖励的例子时，我们可以考虑一个小孩学习的情景。
外部奖励：
假设一个小孩正在学习画画。当他完成一幅漂亮的画作时，他的家长给予他一个糖果作为奖励。在这个例子中，糖果就是外部奖励，它来自于小孩与外部环境（家长）的交互，作为对小孩绘画成果的正面反馈。
内在奖励：
在画画的过程中，小孩可能会产生一些内在的奖励信号。比如，当他成功地完成一个难度较高的绘画技巧时，他可能会感到内心的满足和喜悦，这种满足感和喜悦就是内在奖励。它并不是来自于外部的奖励，而是来自于小孩自身对自己的成长和进步的认知和体验。
在这个例子中，外部奖励是糖果作为一种物质奖励，提供给小孩作为对他绘画成果的外在正面反馈。而内在奖励是小孩在绘画过程中产生的满足感和喜悦，它们是基于小孩的内在体验和成就感而产生的，不依赖于外部的物质奖励。
需要注意的是，内在奖励和外部奖励通常是相互影响的。外部奖励可以激励小孩继续学习和努力画画，而内在奖励则增强了他对绘画过程中的乐趣和成就感的体验。这种内外奖励的结合有助于提高学习的动机和享受学习过程。

## 为什么要引入内在奖励？
在很多现实环境中，奖励信号是稀疏的，所以我们需要引导智能体高效的探索状态空间和动作空间。进而找到最优策略来完成任务。

为此，我们引入了内在奖励机制。我们希望通过内在奖励来:
1. 激励智能体探索更多的新状态(novel state)
2. 激励智能体执行有利于减少环境不确定性的动作

看上去这两个目的的想法似乎是一致的，探索到了更多的新状态的结果就是减少了环境的不确定性。但是值得注意的是，第一个目的更加的注重于状态的“新颖性”，而第二个目的则是更加注重状态行为对的“新颖性”。
> 新颖性指的是一个状态或者一个状态行为对对于智能体来说有多“新”。一个状态或者状态行为对越“新颖”，说明智能体对于它的认知越不充分。需要在之后与环境交互时达到更多该状态或者执行相似的行为，访问对应的状态。在探索模块赋予其更大的内在奖励。

### 如何度量“新颖性”？
1. 通过计数度量新颖性
对于每个$(s,a)$对应一个访问计数$N(s,a)$，当$N$越大时，说明之前访问的次数越多。或者说对应的$(s,a)$被充分探索，越“不新颖”。探索模块给出一个与计数成反比的内在奖励:
$$
intrinsic\ reward = \frac{1}{N(s,a)}
$$
但是这样的方法度量新颖性存在一个显然的局限性，就是应对连续状态或行为空间时，计数方式有如表格式的价值函数一般，难以存储。而且换一个角度来说，访问计数并不能够准确的度量智能体对$(s,a)$的了解程度，就好比我天天看书不代表我就一定懂得所有知识一样。
<br>
2. 通过预测误差度量新颖性
我们可以通过利用智能体对于环境的预测问题来度量新颖性，例如可以使用神经网络建模一个预测函数:
$$
S_{t+1} = f(s_t,a_t)
$$
使用该预测函数来得到智能体对下一个状态的预测或者所有可能的下一状态的概率分布，通过输出和实际执行行为后达到的状态，以某种指标衡量它们之间的误差，进而得出内在奖励。
基于预测的探索机制的局限性在于，如果问题的规模非常大，由于神经网络容量和拟合误差的限制，即使状态行为空间的某个区域的访问次数非常大，预测的误差可能仍然很大。

### observation和action 包含了哪些信息？
一般来说，环境观测/状态(observation/state)的信息来源大概分为三部分:
1. 智能体行为直接控制的部分（智能体的移动造成状态转移）
2. 不受智能体行为控制但是对智能体决策造成影响的部分（环境中包含的陷阱等等）
3. 不受智能体行为控制，且对智能体的决策好坏没有影响的部分（例如我要去食堂吃饭，食堂里面有没有人对我来说没有影响，但是又是环境的一部分）

基于上述内容，智能体真正关注的是第一和第二部分的信息。这两种信息本质上影响智能体的决策。在基于预测误差的探索机制中，环境状态的特征空间在编码状态中第一和第二部分信息的同时，应该避免第三部分信息的干扰。