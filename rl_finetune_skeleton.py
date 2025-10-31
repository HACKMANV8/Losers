
import torch
import torch.optim as optim
from torch.distributions import Categorical
import numpy as np

from neuropt import PassFormer, load_model

# --- 1. Environment ---

class CompilerGym:
    """A mock environment that simulates the compiler optimization process."""
    def __init__(self, program_features):
        self.program_features = program_features
        self.state = [] # The current sequence of passes

    def step(self, action):
        """
        Apply a pass (action) and get the new state and reward.
        In a real scenario, this would involve compiling the program and measuring performance.
        """
        self.state.append(action)
        
        # Mock reward: shorter sequences get a small positive reward
        # In a real scenario, reward would be based on runtime or binary size improvement
        reward = -0.1 * len(self.state)
        
        # In this simple mock env, we are done after a fixed number of steps
        done = len(self.state) >= 10
        
        return self.state, reward, done

    def reset(self):
        """Resets the environment to its initial state."""
        self.state = []
        return self.state

# --- 2. Policy ---

class Policy(nn.Module):
    """Wraps the PassFormer model to act as a policy network."""
    def __init__(self, model):
        super().__init__()
        self.model = model

    def forward(self, features, sequence_so_far):
        """
        Given program features and the sequence generated so far,
        predict the probability distribution over the next pass.
        """
        # The model expects a batch, so we unsqueeze
        features = features.unsqueeze(0)
        sequence_so_far = sequence_so_far.unsqueeze(0)
        
        logits = self.model(features, sequence_so_far)
        
        # Return the probability distribution for the last token
        return Categorical(logits=logits[:, -1, :])

# --- 3. REINFORCE Agent ---

class ReinforceAgent:
    """Implements the REINFORCE algorithm."""
    def __init__(self, policy, optimizer):
        self.policy = policy
        self.optimizer = optimizer
        self.rewards = []
        self.log_probs = []

    def select_action(self, features, sequence_so_far):
        """
        Selects an action (a compiler pass) from the policy's output distribution.
        """
        dist = self.policy(features, sequence_so_far)
        action = dist.sample()
        
        self.log_probs.append(dist.log_prob(action))
        return action.item()

    def update_policy(self):
        """
        Performs a policy gradient update using the collected rewards.
        """
        R = 0
        policy_loss = []
        returns = []
        
        # Calculate discounted rewards
        for r in self.rewards[::-1]:
            R = r + 0.99 * R # gamma = 0.99
            returns.insert(0, R)
        
        returns = torch.tensor(returns)
        returns = (returns - returns.mean()) / (returns.std() + 1e-6) # Normalize

        for log_prob, R in zip(self.log_probs, returns):
            policy_loss.append(-log_prob * R)

        self.optimizer.zero_grad()
        policy_loss = torch.cat(policy_loss).sum()
        policy_loss.backward()
        self.optimizer.step()
        
        # Clear buffers
        self.rewards = []
        self.log_probs = []

# --- 4. Main Fine-tuning Loop (Skeleton) ---

def main():
    # --- Setup ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load the pre-trained PassFormer model
    model_path = 'passformer_runtime.pth' # or binary_size
    pretrained_model, vocab, feature_keys, feature_scaler = load_model(model_path, device)
    
    # Create the policy network
    policy = Policy(pretrained_model).to(device)
    optimizer = optim.Adam(policy.parameters(), lr=1e-4)
    
    agent = ReinforceAgent(policy, optimizer)

    # --- Training ---
    num_episodes = 1000
    for i_episode in range(num_episodes):
        # Get a program from the dataset (mock)
        # In a real scenario, you would iterate through your dataset
        mock_program_features = torch.randn(len(feature_keys)).to(device)
        
        env = CompilerGym(mock_program_features)
        state = env.reset()
        
        # --- Run one episode ---
        for t in range(10): # Max steps per episode
            state_tensor = torch.tensor(state, dtype=torch.long).to(device)
            action = agent.select_action(mock_program_features, state_tensor)
            state, reward, done = env.step(action)
            
            agent.rewards.append(reward)
            if done:
                break
        
        # --- Update policy ---
        agent.update_policy()
        
        if i_episode % 10 == 0:
            print(f'Episode {i_episode}\tLast reward: {reward:.2f}')

if __name__ == '__main__':
    print("This is a skeleton script for RL fine-tuning. It is not meant to be run directly.")
    # main() # Uncomment to run the skeleton
