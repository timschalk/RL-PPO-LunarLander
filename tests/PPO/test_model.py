import sys
from pathlib import Path
import numpy as np
import gym
import torch

module_path = Path(sys.path[0]).parent.parent
sys.path.append(str(module_path))

from PPO.model import PolicyNetwork, ValueNetwork, device
from PPO.replay import Episode, History


def test_model_1():

    env = gym.make("LunarLander-v2")

    observation = env.reset()

    n_actions = env.action_space.n
    feature_dim = observation.size

    policy_model = PolicyNetwork(n=n_actions, in_dim=feature_dim)

    policy_model.to(device)

    action = policy_model.sample_action(observation)

    assert action in list(range(n_actions))


def test_model_2():

    env = gym.make("LunarLander-v2")

    observation = env.reset()

    n_actions = env.action_space.n
    feature_dim = observation.size

    policy_model = PolicyNetwork(n=n_actions, in_dim=feature_dim)
    policy_model.to(device)

    observations = [observation / i for i in range(1, 11)]

    observations = torch.from_numpy(np.array(observations)).to(device)

    probs = policy_model(observations)

    assert list(probs.size()) == [10, n_actions]

    assert probs[0, :].sum().item() == 1


def test_model_3():

    env = gym.make("LunarLander-v2")

    observation = env.reset()

    n_actions = env.action_space.n
    feature_dim = observation.size

    policy_model = PolicyNetwork(n=n_actions, in_dim=feature_dim)
    policy_model.to(device)

    observations = [observation / i for i in range(1, 11)]

    actions = [i % 4 for i in range(1, 11)]

    observations = torch.from_numpy(np.array(observations)).to(device)
    actions = torch.IntTensor(actions).to(device)

    log_probabilities, entropy = policy_model.evaluate_actions(observations, actions)

    assert list(log_probabilities.size()) == [10]
    assert list(entropy.size()) == [10]


def test_history_episode_model():

    env = gym.make("LunarLander-v2")
    observation = env.reset()

    n_actions = env.action_space.n
    feature_dim = observation.size

    policy_model = PolicyNetwork(n=n_actions, in_dim=feature_dim).to(device)
    value_model = ValueNetwork(in_dim=feature_dim).to(device)

    max_episodes = 10
    max_timesteps = 100

    reward_sum = 0
    ite = 0

    history = History()

    for episode_i in range(max_episodes):

        observation = env.reset()
        episode = Episode()

        for timestep in range(max_timesteps):

            action, log_probability = policy_model.sample_action(observation)
            value = value_model.state_value(observation)

            new_observation, reward, done, info = env.step(action)

            episode.append(
                observation=observation,
                action=action,
                reward=reward,
                value=value,
                log_probability=log_probability,
            )

            observation = new_observation

            reward_sum += reward
            ite += 1

            if done:
                episode.end_episode(last_value=np.random.uniform())
                break

            if timestep == max_timesteps - 1:
                episode.end_episode(last_value=0)

        history.add_episode(episode)

    history.build_dataset()

    assert abs(np.sum(history.rewards) - reward_sum) < 1e-5

    assert len(history.rewards) == ite

    assert abs(np.mean(history.advantages)) <= 1e-10

    assert abs(np.std(history.advantages) - 1) <= 1e-3


test_history_episode_model()
