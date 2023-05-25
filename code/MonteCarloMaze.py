import numpy as np

state_space = [i for i in range(25)]  # 5*5的网格世界，需要25个状态表示
action_space = ['n', 'e', 's', 'w']

# 每采取一个动作状态的改变
action_to_state = {
    'n': -5,
    'e': 1,
    's': 5,
    'w': -1
    # 上 右 下 左
}
'''
1  X  3  4  5
6  7  8  9  10
11 12 13 14 15
16 X  18 19 20
X  22 23 24 25
'''
traps = [2, 17, 21]
trajectory = []
states = []
actions = []
rewards = []
gamma = 0.85

V = np.zeros((26, 4))  # 状态动作对的行为价值
N = np.zeros((26, 4))  # 记录状态动作对的数量
final_V = np.zeros(26)  # 最终的行为价值，先初始化为0


def initial_env():
    global trajectory
    global states
    global actions
    global rewards

    trajectory = []
    states = []
    actions = []
    rewards = []


def step(state, action):
    s_prime = state
    reward = 0
    if (state < 5 and action == 'n') or (state % 5 == 0 and action == 'w') \
            or ((state + 1) % 5 == 0 and action == 'e') or (state > 19 and action == 's'):  # 撞墙的情况
        reward = -2
    else:
        shift_state = action_to_state[action]
        s_prime += shift_state
        if s_prime == 24:
            reward = 1
        elif s_prime in traps:
            reward = -20
        else:
            reward = -1
    done = True if s_prime == 24 else False
    return s_prime, reward, done


def R(state, action):
    _, reward, _ = step(state, action)
    return reward


def random_policy():  # 采用均匀策略
    return np.random.choice(action_space)


def epsilon_greedy(epsilon, state):
    if np.random.uniform(0, 1) < epsilon:
        return np.random.choice(action_space)
    else:
        return action_space[np.argmax(V[state])]


def monte_carlo():
    rounds = 300000
    epsilon=0.5
    for i in range(rounds):
        if i % 2000 == 0:
            print("{:<5} %".format(i / rounds * 100) )
        initial_env()
        state = 1
        done = False
        count=0
        flag=False
        while not done:
            action = epsilon_greedy(epsilon,state)
            newstate, reward, done = step(state, action)
            states.append(state)
            actions.append(action)
            rewards.append(reward)
            trajectory.append(state)
            state = newstate
            count+=1
            if count > 300000:
                flag=True
                break
        if flag is True:
            i-= 1
            continue
        if epsilon > 0.1:
            epsilon *= 0.99

        G = []
        r = 0
        for t in range(len(rewards) - 1, -1, -1):
            r = rewards[t] + gamma * r
            G = [r] + G
        
        #print('Round{}over,the states is:{}.\nAnd the reward is:{}\n'.format(i + 1, states, rewards))
        visited = set()
        for t in range(len(trajectory)):
            if states[t] not in visited:
                visited.add(states[t])
                state = states[t]
                action_index = action_space.index(actions[t])
                N[state, action_index] += 1
                alpha = 1.0 / N[state, action_index]
                V[state, action_index] += alpha * (G[t] - V[state, action_index])


def print_state_value():
    count = 0
    for i in V[:-1]:
        print('{:<5}'.format(action_space[np.argmax(i)]), end='')
        count += 1
        if count == 5:
            print()
            count = 0


if __name__ == '__main__':
    monte_carlo()
    print_state_value()
