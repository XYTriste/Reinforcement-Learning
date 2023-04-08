import random
import numpy as np

# 定义21点游戏的状态和行动空间
state_space = [i for i in range(4, 32)]  # 玩家的点数，不包括A牌
action_space = ["hit", "stick"]  # 行动：要牌 / 停牌

# 初始化状态值函数和行动价值函数
v_table = {}
q_table = {}
N = np.zeros((32, 2))
for state in state_space:
    v_table[state] = 0.0
    q_table[state] = {"hit": 0.0, "stick": 0.0}

# 定义蒙特卡洛强化学习参数
num_episodes = 10000  # 轨迹数量
epsilon = 1  # epsilon-greedy策略中的epsilon

dealer_win = 0
player_win = 0


# 定义状态转移函数
def get_next_state(state, action):
    """
    :param state: 当前的状态
    :param action: 采取的行为
    :return: 如果状态合法则返回对应状态否则触碰到边界返回边界状态
    """
    next_state = state
    if action == "hit":
        next_state += random.randint(1, 10)
    return next_state


# 定义epsilon-greedy策略
def epsilon_greedy_policy(state, epsilon):
    """
    如果生成的随机数小于epsilon则随机挑选一个行为.
    否则从该状态对应的行为空间中挑选一个行为价值更大的行为。
    返回对应的行为
    :param state:
    :param epsilon:
    :return:
    """
    if random.uniform(0, 1) < epsilon:
        return random.choice(action_space)
    else:
        return max(q_table[state], key=q_table[state].get)

if __name__ == '__main__':

    # 运行蒙特卡洛强化学习算法
    for i in range(num_episodes):
        # 初始化游戏状态和轨迹
        player_state = random.randint(4, 21)
        dealer_showing = random.randint(1, 10)
        trajectory = [(player_state, 1)]
        rewards = [0.0]
        returns = []

        # 执行当前策略并记录轨迹
        while True:
            action = epsilon_greedy_policy(player_state, epsilon)
            next_player_state = get_next_state(player_state, action)
            player_state = next_player_state
            trajectory.append((player_state, 1 if action == "hit" else 0))
            if player_state > 21:
                print("玩家爆牌，玩家负")
                rewards += [-1.0]
                dealer_win += 1
                break
            if action == "stick":
                if player_state > 21:
                    print("玩家爆牌，玩家负")
                    dealer_win += 1
                    rewards += [-1.0]
                else:
                    while dealer_showing < 17:
                        dealer_showing += random.randint(1, 10)
                    if dealer_showing > 21:
                        print("庄家爆牌，庄家负")
                        player_win += 1
                        reward = 1
                    elif dealer_showing > player_state:
                        print("玩家点数: {}   庄家点数:{}   玩家负".format(player_state, dealer_showing))
                        dealer_win += 1
                        reward = -1.0
                    elif player_state > dealer_showing:
                        player_win += 1
                        reward = 1.0
                    else:
                        print("玩家点数: {}   庄家点数:{}   和局".format(player_state, dealer_showing))
                        reward = 0.0
                    rewards += [reward]
                    break
            else:
                rewards += [0.0]
        
        if epsilon > 0.1:
            epsilon *= 0.99
        
        print("trajectory:", trajectory)
        
        G = 0
        for t in range(len(trajectory) - 1, -1, -1):
            G = rewards[t] + 0.95 * G
            returns = [G] + returns
        print("returns:", returns)
        # 更新状态值函数和行动价值函数
        visited_states = set()
        index = 0
        for state, action in trajectory:
            if (state, action) not in visited_states:
                visited_states.add((state, action))
                old_v = q_table[state]["hit" if action == 1 else "stick"]
                # returns = reward
                # for j in range(len(trajectory) - 1, -1, -1):
                #     if trajectory[j][0] == state:
                #         returns += 1.0
                #     else:
                #         break
                N[state, action] += 1
                q_table[state]["hit" if action == 1 else "stick"] +=  (1.0 / N[state, action]) * (returns[index] - old_v)
                #print("update:", q_table[state]["hit" if action == 1 else "stick"])
                # print("New:", new_v)
                # q_table[state][action] = new_v
                # v_table[state] = new_v
            index += 1

    # 打印最终的状态值函数和策略
    print(v_table)
    for state in state_space[:-10]:
        print("状态{}下:".format(state))
        for action in action_space:
            print("动作 {} 的价值是: {}".format(action, q_table[state][action]))
        print("更有价值的动作是: {}".format("hit" if q_table[state]["hit"] >= q_table[state]["stick"] else "stick"))
    print("玩家赢了 {} 回合, 庄家赢了 {} 回合".format(player_win, dealer_win))
    print("玩家的胜率是: {:.2f}%   庄家的胜率是:{:.2f}%   玩家不败的概率是:{:.2f}%".format(player_win / 100, dealer_win / 100, (10000 - dealer_win) / 100))