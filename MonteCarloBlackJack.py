import random

import gym
import numpy as np

env = gym.make('Blackjack-v1', render_mode="rgb_array")

V = np.zeros(32)  # 状态价值
N = np.zeros(32)  # 状态出现次数
# Q = np.zeros((32, 2, 2))  # 行为价值
Q = np.random.rand(32, 2, 2) * 1E-5
Q_N = np.zeros((32, 2, 2))  # 行为出现次数
gamma = 0.95
epsilon = 1

record = {}


def process_bar(rounds, i):
    print("Training {:.4f}%".format((i / rounds) * 100))


def print_winning_probability(rounds, trained_rounds, player_win, dealer_win, draw):
    player_winning_rate = (player_win / rounds) * 100
    dealer_winning_rate = (dealer_win / rounds) * 100
    not_lose_rate = (player_win + draw) / rounds * 100
    print("After trained {} rounds. Player win:{}   Dealer win:{}.".format(trained_rounds, player_win, dealer_win))
    print("Player win rate:{:.2f}%.  not lose rate:{:.2f}%.  Dealer win rate:{:.2f}%".format(player_winning_rate,
                                                                                             not_lose_rate,
                                                                                             dealer_winning_rate))
    record_winning_rate(trained_rounds, player_winning_rate, dealer_winning_rate, not_lose_rate)


def process_bar(rounds, i):
    print("Training {:.4f}%".format((i / rounds) * 100))


def epsilon_greedy_policy(player_state, usable_ace, epsilon=0.1):
    if random.uniform(0, 1) < epsilon:
        return env.action_space.sample()
    else:
        return np.argmax(V[player_state])


def monte_carlo():
    rounds = 10000
    for i in range(rounds):
        obs, _ = env.reset()
        player_state, dealer_state, _ = obs

        trajectory = []
        states = []
        rewards = []
        actions = []

        done = False  # 游戏终止状态
        while not done:
            action = epsilon_greedy_policy(player_state, dealer_state)
            observation, reward, done, _, _ = env.step(action)

            trajectory.append((player_state, dealer_state, action))
            states.append(player_state)
            actions.append(action)
            rewards.append(reward)

            player_state = observation[0]
            dealer_state = observation[1]
            # env.render()
        if epsilon > 0.1:
            epsilon *= 0.99

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

        visited_set = set()
        index = 0
        for p_state, d_state, action in trajectory:
            if (p_state, d_state, action) not in visited_set:
                visited_set.add((p_state, d_state, action))
                N[p_state] += 1
                alpha = 1.0 / N[p_state]
                V[p_state] += alpha * (returns[index] - V[p_state])
                # 使用当前状态对应的return 减去 当前的状态价值的差，乘以alpha，把它加到当前状态的状态价值中去。其实就是累进更新平均值的方式。

                Q_N[p_state, action] += 1
                alpha = 1.0 / Q_N[p_state, action]
                Q[p_state, action] += alpha * (returns[index] - Q[p_state, action])
            index += 1


def show_value():
    for i in range(4, 22):
        print("状态 {} 时状态价值为: {}".format(i, V[i]))
        max_action = Q[i, 0, 0]
        usable_ace = 0
        choice_action = 0
        for j in range(2):
            for k in range(2):
                print("该状态下，Ace {} 时，动作 {} 的价值为: {}".format("不可用" if k == 0 else "可用",
                                                                       "stick" if j == 0 else "hit", Q[i, k, j]))
                if Q[i, k, j] > max_action:
                    max_action = Q[i, k, j]
                    usable_ace = k
                    choice_action = j
            print("综上所述， 状态 {} 在 Ace {} 时， {} 动作的价值最大".format(i, "不可用" if usable_ace == 0 else "可用",
                                                                             "不抽牌" if choice_action == 0 else "抽牌"))
            print()


if __name__ == '__main__':
    monte_carlo()
    show_value()
