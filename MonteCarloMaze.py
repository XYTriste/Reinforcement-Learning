import numpy as np

state_space = [i for i in range(25)]
action_space = ["n", "e", "s", "w"]

action_to_state = {
    "n": -5,  # 上
    "e": 1,  # 右
    "s": 5,  # 下
    "w": -1  # 左
}
'''
0  1  2  3  4 
5  X  7  8  9
10 11 12 13 14
15 16 X 18 19
20 X 22 23 24
'''
traps = [2, 6, 17, 21]

trajectory = []
states = []
actions = []
rewards = []
gamma = 0.85

V = np.zeros((26, 4))
N = np.zeros((26, 4))

final_V = np.zeros(26)


def initial_env():
    global trajectory
    trajectory = []

    global states
    global actions
    global rewards

    states = []
    actions = []
    rewards = []


def step(state, action):
    s_prime = state
    reward = 0
    if (state < 5 and action == "n") or (state % 5 == 0 and action == "w") \
            or ((state + 1) % 5 == 0 and action == "e") or (state > 19 and action == "s"):
        reward = -5
    else:
        shift_state = action_to_state[action]
        s_prime += shift_state
        if s_prime == 24:
            reward = 10
        elif s_prime in traps:
            reward = -5
        else:
            reward = -1
    done = True if s_prime == 24 else False
    return s_prime, reward, done


def R(state, action):
    _, reward, _ = step(state, action)
    return reward


def random_policy():
    return np.random.choice(action_space)


def monte_carlo():
    rounds = 300
    for i in range(rounds):
        initial_env()

        state = 0
        done = False
        while not done:
            action = random_policy()

            newstate, reward, done = step(state, action)
            states.append(newstate)
            actions.append(action)
            rewards.append(reward)
            trajectory.append(newstate)
            state = newstate

        print('Round {} over, the states is: {}.\nAnd the reward is:{}\n'.format(i + 1, states, rewards))

        G = 0
        for t in range(len(trajectory) - 1, -1, -1):
            G = rewards[t] + gamma * G
            state = states[t]
            action_index = action_space.index(actions[t])
            N[state, action_index] += 1
            alpha = 1.0 / N[state, action_index]
            V[state, action_index] += alpha * (G - V[state, action_index])


def print_state_value():
    count = 0
    for i in final_V[:-1]:
        print("{:<25}".format(i), end="  ")
        count += 1
        if count == 5:
            print()
            count = 0


def find_max_weight_path(map):
    n = len(map)
    dp = [[0] * n for _ in range(n)]

    for j in range(1, n):
        dp[0][j] = dp[0][j - 1] + map[0][j]
    for i in range(1, n):
        dp[i][0] = dp[i - 1][0] + map[i][0]

    for i in range(1, n):
        for j in range(1, n):
            dp[i][j] = max(dp[i - 1][j], dp[i][j - 1]) + map[i][j]

    path = []
    i, j = n - 1, n - 1
    while i > 0 or j > 0:
        if j == 0:
            path.append((i - 1, j))
            i -= 1
        elif i == 0:
            path.append((i, j - 1))
            j -= 1
        else:
            if dp[i - 1][j] > dp[i][j - 1]:
                path.append((i - 1, j))
                i -= 1
            else:
                path.append((i, j - 1))
                j -= 1
    path.reverse()
    path.append((n - 1, n - 1))

    print("Path:", path)

    return dp[n - 1][n - 1], path


if __name__ == '__main__':
    monte_carlo()
    # for s in range(26):
    #     for a in range(4):
    #         print("在状态{}采取动作{}的价值为:{}".format(s, action_space[a], V[s, a]))
    #         final_V[s] += V[s, a]
    #     final_V /= 4.0
    print_state_value()

    final_V = final_V[1:]
    weight_map = np.array(final_V).reshape(-1, 5)

    _, path = find_max_weight_path(weight_map)
    for i, j in path:
        print("reward:", final_V[i * 5 + j])
