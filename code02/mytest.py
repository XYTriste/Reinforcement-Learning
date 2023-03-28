import numpy as np

# 生成迷宫
maze = [[0, 0, 1, 0],
        [0, 0, 1, 0],
        [0, 0, 0, 0],
        [1, 1, 0, 0]]

# 各个状态的奖励
rewards = [[-2, -2, -7, -2],
           [-2, -2, -7, -2],
           [-2, -2, -2, -2],
           [-7, -7, -2, 10]]

# 定义起点和终点
start_state = (0, 0)
end_state = (3, 3)

# 定义状态到下标的映射和下标到状态的映射
state_index_map = {}
index_state_map = {}
chains = [[(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (2, 3), (3, 3)],  # 三条从起点到终点的状态序列
          [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (2, 3), (3, 3)],
          [(0, 0), (0, 1), (1, 1), (2, 1), (2, 2), (3, 2), (3, 3)]]
n_states = len(maze) * len(maze[0])  # 迷宫中的状态数（包括障碍物和终点）
P = np.zeros((n_states, n_states))

map = np.array([
    [0, 1, 2, 3],
    [4, 5, 6, 7],
    [8, 9, 10, 11],
    [12, 13, 14, 15]
])


def init_state_with_index():
    index = 0
    for i in range(len(maze)):
        for j in range(len(maze[0])):
            if maze[i][j] != 1:  # 不是障碍物
                state_index_map[(i, j)] = index
                index_state_map[index] = (i, j)
                index += 1


def init_state_transition_probability():
    '''

    [
[0, 1, 2, 3],
[4, 5, 6, 7],
[8, 9, 10, 11],
[12, 13, 14, 15]
]
    :return:
    '''
    global P
    for i in range(n_states):
        row = i // 4
        col = i % 4
        neighbors = []

        # 找到当前格子周围的且可以到达的格子
        if row > 0:
            neighbors.append(map[row - 1][col])
        if row < 3:
            neighbors.append(map[row + 1][col])
        if col > 0:
            neighbors.append(map[row][col - 1])
        if col < 3:
            neighbors.append(map[row][col + 1])

        # 计算从当前状态到下一状态的概率
        for j in neighbors:
            P[i, j] = 1 / len(neighbors)


def compute_return(start_index=0, chain=None, gamma=0.5):
    all_return, power, gamma = 0.0, 0, gamma
    for i in range(start_index, len(chain)):
        x, y = chain[i]
        all_return += np.power(gamma, power) * rewards[x][y]
        power += 1
    return all_return


def compute_state_value(Pss, reward, gamma=0.05):
    reward = np.array(reward).reshape((-1, 1))
    value = np.dot(np.linalg.inv(np.eye(len(Pss), len(Pss)) - gamma * Pss), reward)

    return value


if __name__ == '__main__':
    init_state_with_index()
    init_state_transition_probability()
    print(compute_state_value(P, rewards, 0.5))