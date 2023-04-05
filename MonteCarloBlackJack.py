import random

import gym
import numpy as np

env = gym.make('Blackjack-v1', render_mode="human")

V = np.zeros(32)
N = np.zeros(32)
Q = np.zeros((32, 2))
Q_N = np.zeros((32, 2))
gamma = 0.95


def epsilon_greedy_policy(player_state, dealer_state, epsilon=0.1):
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

        done = False
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

        G = 0
        returns = []
        for t in range(len(trajectory) - 1, -1, -1):
            G = rewards[t] + gamma * G
            returns = [G] + returns

        print("Trajectory:", trajectory)
        if rewards[-1] > 0:
            print("Player win.")
        elif rewards[-1] == 0:
            print("Draw.")
        else:
            print("dealer win.")

        visited_set = set()
        index = 0
        for p_state, d_state, action in trajectory:
            if (p_state, d_state, action) not in visited_set:
                visited_set.add((p_state, d_state, action))
                N[p_state] += 1
                alpha = 1.0 / N[p_state]
                V[p_state] += alpha * (returns[index] - V[p_state])

                Q_N[p_state, action] += 1
                alpha = 1.0 / Q_N[p_state, action]
                Q[p_state, action] += alpha * (returns[index] - Q[p_state, action])
            index += 1


def show_value():
    for i in range(4, 22):
        print("状态 {} 时状态价值为: {}".format(i, V[i]))
        for j in range(2):
            print("该状态下，动作 {} 的价值为: {}".format("stick" if j == 0 else "hit", Q[i, j]))
        print()


if __name__ == '__main__':
    monte_carlo()
    show_value()
