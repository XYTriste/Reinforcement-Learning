import random

import gym
import numpy as np

env = gym.make('Blackjack-v1', render_mode="rgb_array")

V = np.zeros(32)
N = np.zeros(32)
Q = np.zeros((32, 2))
Q_N = np.zeros((32, 2))
gamma = 0.95


def process_bar(rounds, i):
    print("Training {:.4f}%".format((i / rounds) * 100))


def epsilon_greedy_policy(player_state, dealer_state, epsilon=0.1):
    if random.uniform(0, 1) < epsilon:
        return env.action_space.sample()
    else:
        return np.argmax(Q[player_state])


def monte_carlo():
    rounds = 50000  # 迭代次数为10000
    for i in range(rounds):  # 循环迭代

        if i % 5000 == 0:
            process_bar(rounds, i)

        obs, _ = env.reset()  # 初始化环境，得到最初的观测空间，包含玩家手牌点数，庄家明牌点数
        player_state, dealer_state, _ = obs

        trajectory = []
        states = []
        rewards = []
        actions = []

        done = False  # 游戏终止状态
        while not done:
            action = epsilon_greedy_policy(player_state, dealer_state)  # 使用epsilon策略获得一个动作
            observation, reward, done, _, _ = env.step(action)  # 得到观测空间， 动作转移到某状态获得的即时奖励 游戏是否结束

            trajectory.append((player_state, dealer_state, action))  # 在轨迹中加入当前的状态-行动对
            states.append(player_state)  # 将当前状态加入到一个状态列表中
            actions.append(action)  # 将当前状态采取的动作加入到一个动作列表中
            rewards.append(reward)  # 将当前状态采取动作获得的即时奖励加入一个奖励列表中

            player_state = observation[0]  # 从得到的观测空间中，得到玩家新的手牌点数
            dealer_state = observation[1]  # 从得到的观测空间中，得到庄家新的手牌点数
            # env.render()

        G = 0  # G其实就是以各个状态为起点的return
        returns = []  # 保存一个episode中所有状态的return的列表
        for t in range(len(trajectory) - 1, -1, -1):  # 从最后一个状态开始，计算return
            G = rewards[t] + gamma * G  # 该状态的return = 当前状态的即时奖励 + 后续return * gamma（折现率）
            returns = [G] + returns  # 将当前 状态-行动对的return 插入到 returns 的最前面。因为G是从后向前算的
            # 所以trajectory中第一个状态-行动对的 G 也应该在returns的最前面

        # 一些无关紧要的输出信息
        # print("Trajectory:", trajectory)
        # if rewards[-1] > 0:
        #     print("Player win.")
        # elif rewards[-1] == 0:
        #     print("Draw.")
        # else:
        #     print("dealer win.")

        visited_set = set()  # 我们采用首次访问的方式，所以使用一个集合来记录出现过的状态-行动对
        index = 0  # 记录我们当前在访问trajectory中的第几个状态-行动对
        for p_state, d_state, action in trajectory:  # 遍历当前的trajectory
            if (p_state, d_state, action) not in visited_set:  # 如果当前的状态-行动对没有出现过
                visited_set.add((p_state, d_state, action))  # 把这个状态-行动对加入到集合中
                N[p_state] += 1  # 记录状态出现的次数，将该状态出现的次数加一
                alpha = 1.0 / N[p_state]  # alpha其实就是 状态出现的次数的倒数
                V[p_state] += alpha * (returns[index] - V[p_state])
                # 使用当前状态对应的return 减去 当前的状态价值的差，乘以alpha，把它加到当前状态的状态价值中去。其实就是累进更新平均值的方式。

                Q_N[p_state, action] += 1  # 记录当前状态-行为对出现的次数
                alpha = 1.0 / Q_N[p_state, action]  # 同样是累进更新平均值
                Q[p_state, action] += alpha * (returns[index] - Q[p_state, action])  # 使用这种方式更新 状态采取某行为的价值。
            index += 1  # 访问完了一个状态-行动对，将index + 1


def show_value():
    for i in range(4, 22):
        print("状态 {} 时状态价值为: {}".format(i, V[i]))
        for j in range(2):
            print("该状态下，动作 {} 的价值为: {}".format("stick" if j == 0 else "hit", Q[i, j]))
        print()


def play_with_dealer():
    rounds = 10000
    player_win = 0
    dealer_win = 0
    draw = 0
    for i in range(rounds):
        done = False

        obs, _ = env.reset()
        player_state, dealer_state, _ = obs
        while not done:
            action = epsilon_greedy_policy(player_state, dealer_state, 0)
            observation, reward, done, _, _ = env.step(action)

        if reward > 0:
            player_win += 1
        elif reward == 0:
            draw += 1
        else:
            dealer_win += 1

    print("After {} rounds. Player win:{}   Dealer win:{}.".format(rounds, player_win, dealer_win))
    print("Player win rate:{:.4f}".format(player_win / rounds))


if __name__ == '__main__':
    monte_carlo()
    # show_value()

    play_with_dealer()
