接下来我们来看 $T$ 是否是一个压缩映射。假设 $V$ 和 $W$ 是任意两个状态价值函数，且 $V \geq W$ （即对于所有状态 $s$，$V(s) \geq W(s)$）。考虑到 $T$ 的定义，我们有：
$$
\begin{aligned}
(TV)(s) - (TW)(s) = \\
 \sum_{a} \pi(a|s) \sum_{s'} P(s'|s,a)[R(s,a,s')+\gamma V(s')] - \sum_{a} \pi(a|s) \sum_{s'} P(s'|s,a)[R(s,a,s')+\gamma W(s')] \\
&= \gamma \sum_{a} \pi(a|s) \sum_{s'} P(s'|s,a) [V(s') - W(s')] \\
&\leq \gamma \sum_{a} \pi(a|s) \sum_{s'} P(s'|s,a) [V(s') - W(s')] \\
&\leq \gamma \sum_{s'} P(s'|s) [V(s') - W(s')] \\
&\leq \gamma \lVert V - W \rVert_\infty
\end{aligned}
$$
其中第一个等号是因为 $V \geq W$，第二个等号是由于 Bellman 期望方程的定义，不等式来自于 $V \geq W$，最后一个不等式是因为 $P(s'|s,a)$ 是概率分布。这证明了 $T$ 是一个 $\gamma$-压缩映射，即对于任何两个状态价值函数 $V$ 和 $W$，$T(V)$ 和 $T(W)$ 之间的 $\infty$-范数不超过 $\gamma$ 倍 $V$ 和 $W$ 之间的 $\infty$-范数。

接下来考虑使用压缩映射定理来证明 $T$ 的不动点存在且唯一。我们将定义一个迭代序列 $V_0, V_1, \ldots$，其中 $V_0$ 是任意的状态价值函数，而 $V_{k+1} = TV_k$。由于 $T$ 是一个 $\gamma$-压缩映射，我们知道 $\lVert V_{k+1} - V_k \rVert_\infty \leq \gamma \lVert V_k - V_{k-1} \rVert_\infty \leq \gamma^2 \lVert V_{k-1} - V_{k-2} \rVert_\infty \leq \cdots \leq \gamma^{k+1} \lVert V_0 - V_1 \rVert_\infty$。因此，$V_k$ 的收敛速度是 $\mathcal{O}(\gamma^k)$ 的，而且收敛到唯一的不动点 $V{}$，满足 $V^ = TV^{*}$。这就证明了贝尔曼方程的收敛性。
\
\
\
SARSA($\lambda$)是一种基于TD学习的强化学习算法，它可以用于求解基于动作的马尔可夫决策过程（MDP）问题。SARSA($\lambda$)算法的更新规则如下：

初始化状态值函数 $Q(s,a)$，以及 效用迹 $e(s,a) = 0$。

对于每一个时间步 $t$，执行以下操作：

1. 根据当前状态 $S_t$，使用一个 $\epsilon$-greedy 策略选择动作 $A_t$。

2. 执行动作 $A_t$，得到奖励 $R_{t+1}$ 和新状态 $S_{t+1}$。

3. 根据新状态 $S_{t+1}$，使用一个 $\epsilon$-greedy 策略选择动作 $A_{t+1}$。

4. 计算TD误差 $\delta_t = R_{t+1} + \gamma Q(S_{t+1}, A_{t+1}) - Q(S_t, A_t)$。

5. 将当前状态-动作对 $(S_t, A_t)$ 的 eligibility trace 加1，即 $e(S_t,A_t) \leftarrow e(S_t,A_t) + 1$。

6. 对于所有状态-动作对 $(s,a)$，更新状态值函数和 eligibility traces：

 $$
 \begin{aligned}
 Q(s,a) &\leftarrow Q(s,a) + \alpha \delta_t e(s,a) \\
 e(s,a) &\leftarrow \gamma \lambda e(s,a) \quad \text{(衰减 eligibility traces)}
 \end{aligned}
 $$
 


这里 $\alpha$ 是学习率，$\gamma$ 是折扣因子，$\lambda$ 是一个参数，称为 $\lambda$ 返回（$\lambda$-return）。当 $\lambda = 0$ 时，SARSA($\lambda$) 等价于 SARSA；当 $\lambda = 1$ 时，SARSA($\lambda$) 等价于 TD($\lambda$)。

重复步骤2直到收敛。