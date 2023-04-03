import random

# 定义21点游戏的状态和行动空间
state_space = [i for i in range(0, 32)]  # 玩家的点数，不包括A牌
action_space = ["take", "stop"]  # 行动：要牌 / 停牌

poker_pile = []

# 初始化状态值函数和行动价值函数
v_table = {}
q_table = {}

# 定义蒙特卡洛强化学习参数
num_episodes = 1000  # 轨迹数量
epsilon = 0.2  # epsilon-greedy策略中的epsilon

player_win = 0
dealer_win = 0
initial_state = [0] * 22


def initial_poker_pile():
    global poker_pile
    for i in range(1, 11):
        poker_pile += ([i] * 4)
        if i == 10:
            poker_pile += ([i] * 12)


def initial_something():
    global v_table
    global q_table
    for state in state_space:  # 将所有的状态价值和对应状态下的行为价值设置为0
        v_table[state] = 0.0
        q_table[state] = {"take": -float('inf'), "stop": -float('inf')}
    initial_poker_pile()


# 定义状态转移函数
def get_next_state(state, action):
    """
    :param state: 当前的状态
    :param action: 采取的行为
    :return: 如果状态合法则返回对应状态否则触碰到边界返回边界状态
    """
    next_state = state
    if action == "take":
        if len(poker_pile) != 0:
            choice_poker = random.choice(poker_pile)
            next_state += choice_poker
            poker_pile.remove(choice_poker)

            # print('take poker:', choice_poker)
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


def human_policy(state, prob=0.2):
    if state <= 10:
        return "take"
    elif state <= 15:
        return random.choice(action_space)
    elif state == 21:
        return "stop"
    else:
        rval = random.uniform(0, 1)
        if rval < prob:
            return "take"
        else:
            return "stop"


def show_value(value):
    count = 0
    for k, v in value.items():
        print(value[k], end=" ")
        count += 1
        if count % 4 == 0:
            print()
            count = 0
    print()


def monte_carlo():
    global player_win
    global dealer_win

    # 运行蒙特卡洛强化学习算法
    for i in range(num_episodes):
        # 初始化游戏状态和轨迹
        player_state = 0  # random.randint(4, 21)  # 玩家随机抽两张牌
        initial_state[player_state] += 1
        trajectory = []  # 轨迹

        # 执行当前策略并记录轨迹
        while True:
            action = epsilon_greedy_policy(player_state, epsilon)  # 遵循epsilon greedy策略获取一个动作

            trajectory.append((player_state, action))  # 在轨迹中加上对应的状态-行动对

            next_player_state = get_next_state(player_state, action)  # 获得状态采取行动后的下一个状态
            if next_player_state > 21:  # 如果下一个状态超出了21点
                reward = -1.0  # 获得 -1 的奖励
                break
            elif action == "stop":  # 如果采取的行动是不抽牌
                dealer_total = 0
                while dealer_total < 17:
                    dealer_total += get_next_state(dealer_total, "take")
                if dealer_total > 21 or dealer_total < next_player_state:
                    player_win += 1
                    reward = 1.0
                elif dealer_total > next_player_state:
                    dealer_win += 1
                    reward = -1.0
                else:
                    reward = 0.0
                break

            player_state = next_player_state

        # print("trajectory:", trajectory)
        # 更新状态值函数和行动价值函数
        visited_states = set()
        allReturns = reward
        trajectory.append((next_player_state, "stop"))
        for state, action in trajectory:
            allReturns += 1
            if (state, action) not in visited_states:
                visited_states.add((state, action))
                old_v = v_table[state]
                returns = reward
                for j in range(len(trajectory) - 1, -1, -1):
                    if trajectory[j][0] == state:
                        pass
                        # returns += 1
                    else:
                        break

                new_v = old_v + (1.0 / len(visited_states)) * (returns - old_v)
                v_table[state] = new_v
                q_table[state][action] = new_v
        # print("The trajectory all returns:", allReturns)
        initial_poker_pile()


if __name__ == '__main__':
    initial_something()
    print(poker_pile)

    monte_carlo()

    # 打印最终的状态值函数和策略
    show_value(v_table)
    for state in state_space:
        print(state, "take value:", q_table[state]["take"], "  stop value:", q_table[state]["stop"])
    print('player win:', player_win)
    print("dealer win:", dealer_win)
    print('player initial state count:', initial_state)