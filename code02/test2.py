import random

# 定义21点游戏的状态和行动空间
state_space = [i for i in range(4, 22)]  # 玩家的点数，不包括A牌
action_space = ["take", "stop"]  # 行动：要牌 / 停牌

# 初始化状态值函数和行动价值函数
v_table = {}
q_table = {}
for state in state_space:
    v_table[state] = 0.0
    q_table[state] = {"take": 0.0, "stop": 0.0}

# 定义蒙特卡洛强化学习参数
num_episodes = 10000  # 轨迹数量
epsilon = 0.1  # epsilon-greedy策略中的epsilon


# 定义状态转移函数
def get_next_state(state, action):
    """
    :param state: 当前的状态
    :param action: 采取的行为
    :return: 如果状态合法则返回对应状态否则触碰到边界返回边界状态
    """
    next_state = state
    if action == "take":
        next_state += random.randint(1, 10)
    return next_state


# 定义epsilon-greedy策略
def epsilon_greedy_policy(state, epsilon):
    """
    epsilon-greedy策略
    以epsilon的概率随机挑选一个行为，并以(1 - epsilon)的概率挑选行为价值最大的行为
    :param state:
    :param epsilon:
    :return:
    """
    if random.uniform(0, 1) < epsilon:
        return random.choice(action_space)
    else:
        return max(q_table[state], key=q_table[state].get)


# 运行蒙特卡洛强化学习算法
for i in range(num_episodes):
    # 初始化游戏状态和轨迹
    player_state = random.randint(4, 21)    # 玩家随机抽两张牌
    dealer_showing = random.randint(1, 10)  # 庄家目前手上的牌
    trajectory = [] # 轨迹

    # 执行当前策略并记录轨迹
    while True:
        action = epsilon_greedy_policy(player_state, epsilon)
        trajectory.append((player_state, action))

        next_player_state = get_next_state(player_state, action)
        if next_player_state > 21:
            reward = -1.0
            break
        elif action == "stop":
            dealer_total = dealer_showing + random.randint(1, 10)
            while dealer_total < 17:
                dealer_total += random.randint(1, 10)
            if dealer_total > 21 or dealer_total < next_player_state:
                reward = 1.0
            elif dealer_total > next_player_state:
                reward = -1.0
            else:
                reward = 0.0
            break

        player_state = next_player_state

    # 更新状态值函数和行动价值函数
    visited_states = set()
    for state, action in trajectory:
        if (state, action) not in visited_states:
            visited_states.add((state, action))
            old_v = v_table[state]
            returns = reward
            for j in range(len(trajectory) - 1, -1, -1):
                if trajectory[j][0] == state:
                    returns += 1.0
                else:
                    break
            new_v = old_v + (1.0 / len(visited_states)) * (returns - old_v)
            v_table[state] = new_v
            q_table[state][action] = new_v

# 打印最终的状态值函数和策略
print(v_table)
for state in state_space:
    print(state, max(q_table[state], key=q_table[state].get))
