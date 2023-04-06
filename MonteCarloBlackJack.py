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


def epsilon_greedy_policy(player_state, usable_ace, epsilon=0.1):
    if random.uniform(0, 1) < epsilon:
        return env.action_space.sample()
    else:
        return np.argmax(Q[player_state, usable_ace])


def record_winning_rate(trained_rounds, player_winning_rate, dealer_winning_rate, not_lose_rate):
    global record
    record[trained_rounds] = (player_winning_rate, dealer_winning_rate, not_lose_rate)


def initialization_training_data():
    global V
    global N
    global Q
    global Q_N
    global epsilon

    V = np.zeros(32)  # 状态价值
    N = np.zeros(32)  # 状态出现次数
    Q = np.random.rand(32, 2, 2) * 1E-5  # 行为价值
    Q_N = np.zeros((32, 2, 2))  # 行为出现次数
    epsilon = 1


def monte_carlo():
    initialization_training_data()
    global epsilon

    rounds = 1000000  # 迭代次数为10000
    for i in range(rounds):  # 循环迭代
        percent = rounds / 20
        if i > 0 and i % percent == 0:
            process_bar(rounds, i)
            play_with_dealer(10000, i)

        obs, _ = env.reset()  # 初始化环境，得到最初的观测空间，包含玩家手牌点数，庄家明牌点数
        player_state, dealer_state, usable_ace = obs
        usable_ace = 1 if usable_ace else 0

        trajectory = []
        states = []
        rewards = []
        actions = []

        done = False  # 游戏终止状态
        while not done:
            action = epsilon_greedy_policy(player_state, usable_ace, epsilon)  # 使用epsilon策略获得一个动作
            observation, reward, done, _, _ = env.step(action)  # 得到观测空间， 动作转移到某状态获得的即时奖励 游戏是否结束

            trajectory.append((player_state, dealer_state, action, usable_ace))  # 在轨迹中加入当前的状态-行动对
            states.append(player_state)  # 将当前状态加入到一个状态列表中
            actions.append(action)  # 将当前状态采取的动作加入到一个动作列表中
            rewards.append(reward)  # 将当前状态采取动作获得的即时奖励加入一个奖励列表中

            player_state = observation[0]  # 从得到的观测空间中，得到玩家新的手牌点数
            dealer_state = observation[1]  # 从得到的观测空间中，得到庄家新的手牌点数
            usable_ace = 1 if usable_ace else 0
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

        visited_set = set()  # 我们采用首次访问的方式，所以使用一个集合来记录出现过的状态-行动对
        index = 0  # 记录我们当前在访问trajectory中的第几个状态-行动对
        for p_state, d_state, action, usable_ace in trajectory:  # 遍历当前的trajectory
            if (p_state, d_state, action, usable_ace) not in visited_set:  # 如果当前的状态-行动对没有出现过
                visited_set.add((p_state, d_state, action, usable_ace))  # 把这个状态-行动对加入到集合中
                N[p_state] += 1  # 记录状态出现的次数，将该状态出现的次数加一
                alpha = 1.0 / N[p_state]  # alpha其实就是 状态出现的次数的倒数
                V[p_state] += alpha * (returns[index] - V[p_state])
                # 使用当前状态对应的return 减去 当前的状态价值的差，乘以alpha，把它加到当前状态的状态价值中去。其实就是累进更新平均值的方式。

                Q_N[p_state, usable_ace, action] += 1  # 记录当前状态-行为对出现的次数
                alpha = 1.0 / Q_N[p_state, usable_ace, action]  # 同样是累进更新平均值
                Q[p_state, usable_ace, action] += alpha * (
                        returns[index] - Q[p_state, usable_ace, action])  # 使用这种方式更新 状态采取某行为的价值。
            index += 1  # 访问完了一个状态-行动对，将index + 1


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


def play_with_dealer(rounds, trained_rounds):
    """
    以下是玩家与庄家对抗时的信息
    """
    player_win = 0
    dealer_win = 0
    draw = 0
    for i in range(rounds):
        done = False

        obs, _ = env.reset()
        player_state, dealer_state, usable_ace = obs
        usable_ace = 1 if usable_ace else 0
        while not done:
            action = epsilon_greedy_policy(player_state, usable_ace, 0)
            observation, reward, done, _, _ = env.step(action)

            _, _, usable_ace = observation
            usable_ace = 1 if usable_ace else 0

        if reward > 0:
            player_win += 1
        elif reward == 0:
            draw += 1
        else:
            dealer_win += 1
    print_winning_probability(rounds, trained_rounds, player_win, dealer_win, draw)


if __name__ == '__main__':
    monte_carlo()
    # show_value()

    # play_with_dealer(10000, 10000)
    maxRate = 0
    maxRecord_round = 0
    maxRecord = ()
    for key, value in record.items():
        if record[key][0] > maxRate:
            maxRate = record[key][0]
            maxRecord_round = key
            maxRecord = record[key]

    print("当迭代次数为 {} 时效果最好，此时玩家胜率为: {:.2f}%  庄家胜率为: {:.2f}%  玩家不败的概率为: {:.2f}%".format(maxRecord_round, maxRecord[0], maxRecord[1], maxRecord[2]))
