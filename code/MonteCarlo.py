import gym
import numpy as np

env = gym.make('Blackjack-v1')

# 初始化状态价值表为0
V = np.zeros((32, 11, 2))

# 统计每个状态被访问的次数
N = np.zeros((32, 11, 2))
states = []
actions = []
rewards = []


def init_info():
    global states
    global actions
    global rewards

    states = []
    actions = []
    rewards = []


# 进行10000次回合
for i in range(10000):
    # 初始化这一回合的状态、行动和回报

    init_info()
    state, _ = env.reset()
    done = False

    # 玩家的牌面小于12时一定要继续叫牌
    while state[0] < 12:
        state, reward, done, _, _ = env.step(1)
        states.append((state[0], state[1], state[2]))
        actions.append(1)
        rewards.append(reward)

    # 当玩家的牌面大于等于12时，使用蒙特卡洛方法进行策略评估
    while not done:
        # 以50%的概率继续叫牌，以50%的概率停牌
        action = np.random.choice([0, 1])
        state, reward, done, _, _ = env.step(action)
        states.append((state[0], state[1], state[2]))
        actions.append(action)
        rewards.append(reward)

    # 回合结束，根据蒙特卡洛方法更新状态价值表
    G = 0
    for t in range(len(states) - 1, -1, -1):
        G = rewards[t] + 0.95 * G
        state = states[t]
        action = actions[t]
        N[state[0], state[1], action] += 1
        alpha = 1.0 / N[state[0], state[1], action]
        V[state[0], state[1], action] += alpha * (G - V[state[0], state[1], action])

# 输出状态价值表
# print(V)
for i in range(12, 22):
    for j in range(1, 11):
        if V[i, j, 0] >= V[i, j, 1]:
            print('在状态 ({}, {}): 停牌价值更高'.format(i, j))
        else:
            print('在状态 ({}, {}): 叫牌价值更高'.format(i, j))
