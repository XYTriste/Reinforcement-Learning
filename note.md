# It's a RL note created by YuXia.
## Basic concept
name|description|Supplement
--:|:--:|:--
$state$|代理相对于环境的状态|无
$action$|代理在每个状态下的动作|每个状态下的所有动作构成动作空间
$state transition$|代理在某个状态下采取某个动作|通常描述为状态->动作->新的状态。也可以用$p(s_{n+1} \mid s_n,a_n) = probability$来表示一个状态经过某个动作转移到另一个状态的条件概率
$policy$|策略表示的是一个从状态到动作的映射,对于每个可能的状态,策略会选择一个相应的行动|策略同样可以用条件概率表示，表示为$\pi (a_n\mid s_n) = probability$.
$reward$|采取某策略后的奖励称为$reward$|$reward$可以表示为$r_{state} = number$.由于代理在一个状态有多个策略,不同策略发生的概率不同。获得的奖励也不同,所以可以用$p(r \mid s,a)$表示代理在状态$s$时采取行动$a$获得奖励的数量.
$Trajectory$|由一系列的$state-action-reward$构成了一条$Trajectory$|每个$state$的策略有多个,所以即使一个$state$也对应着多条$Trajectory$.
$return$|$return$指的是某个$Trajectory$获得的所有$reward$之和|显然如果$Trajectory$不同,获得的$return$也不同.$return$又区分为$immediate\_ reward$和$delay \_ reward$
$discounted\_return$|贴现率|用来控制$delay \_ reward$.

---

## Return与状态值
return的作用是衡量一个策略的良好程度，因此return十分重要。
return也可以定义为沿着轨迹的含贴现率的reward总和。
name|description|Supplement
--:|:--:|:--
$state\_value$|从某个状态开始的所有可能$return$的平均值定义为$state\_value$|所有可能的$return$指的不仅是状态采取某个行动时获得的$immediate\_ reward$,还包括了后面可能获得的$delay \_ reward$

---
考虑一个时间序列$t = 0,1,2,...$，假设在时间$t$，代理处于状态$S_t$且采取的行动是$A_t$,下一步的状态是$S_{t+1}$，获得的奖励记作$R_{t+1}$.那么后续构成的轨迹可以看作是:
$$
{S_t}\stackrel{{A_t}}{\longrightarrow}{S_{t+1}},R_{t+1}\stackrel{{A_t}}{\longrightarrow}{S_{t+2}},R_{t+2}\stackrel{{A_t}}{\longrightarrow}{S_{t+3}},R_{t+3}...
$$
注意到这里的每一步的$S_t$、$A_t$、$S_{t+1}$、$R_{t+1}$都不是固定的，根据策略的不同它们会不同。如果把轨迹的含贴现率的总$return$记作$G_t$。那么就有
$$
G_t=R_{t+1} + \gamma R_{t+2} + \gamma^{2}R_{t+3}+...
$$
其中$\gamma \in (0,1)$.注意到$G_t$也是一个非固定值，根据策略的不同它会不同。

这里需要引入一个新的概念，以$S_t$为起点的一条轨迹，称作一条**状态序列(episode)**，显然对于任意的一个状态$S_t$，它可能拥有一条或多条状态序列。每条状态序列获得的总回报$(return)$就是我们的一个$G_t$.

那么我们可以把状态$s$的状态值定义为:
$$
V_\pi(s) = \Bbb E[G_t\mid S_t=s]
$$
这个公式的含义为,对所有以状态$s$为起点的所有可能的轨迹的总回报(也就是所有的$G_t$)求数学期望，即求它们的带权平均值。

> 再举一个例子说明什么是$V_\pi(s)$.
>
> 考虑一个$2×2$的网格世界.每个网格分别被记作状态$S_i(i \in [1, 4])$.
>
> 网格世界如下所示:
>
$S_1$|$S_2$
--:|:--
$S_3$|$S_4$
> 假设以$S_1$为起始状态，$S_4$为结束状态。把到达各个状态的奖励分别设置为$R_1、R_2、R_3、R_4$。
>
>那么$S_1$的状态序列就有两条，分别是:
>
>$$S_1 \rightarrow S_2  \rightarrow S_4$$
>
>$$S_1 \rightarrow S_3 \rightarrow S_4$$
>对于每条状态序列,获得的奖励分别是
>
>$$G_{t1}= R_2 + \gamma R_4$$
>
>$$G_{t2}= R_3 + \gamma R_4$$
>
>那么$S_1$的状态值$V_\pi(s) = \Bbb E[G_t\mid S_t=s]$就是这二者的数学期望，也就是对它们乘以各自发生的概率求和。
>
>需要注意的是，在实际应用中，我们通常**无法事先确定**每个状态序列出现的准确概率，因此需要使用一些估计方法来得到这些概率。例如，在蒙特卡罗方法中，我们可以通过采样多条状态序列，并统计它们的出现次数来估计每个状态序列的概率。

