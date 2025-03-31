import torch
import random
import numpy as np
from collections import deque
import tkinter as tk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from game import SnakeGameAI, Direction, Point
from model import Linear_QNet, QTrainer
from helper import plot
import matplotlib
import matplotlib.colors as mcolors
matplotlib.use("TkAgg")  # Force Matplotlib to use Tkinter backend
from game import BLOCK_SIZE  # Import the constant directly
MAX_MEMORY = 100_000
BATCH_SIZE = 1000
LR = 0.001

class Agent:
    def __init__(self):
        self.n_games = 0
        self.epsilon = 0  # randomness
        self.gamma = 0.9  # discount rate
        self.memory = deque(maxlen=MAX_MEMORY)  # popleft()
        self.model = Linear_QNet(11, 256, 3)
        self.trainer = QTrainer(self.model, lr=LR, gamma=self.gamma)
        self.action_counts = [0, 0, 0]  # Tracks left, right, straight actions
        self.q_values = []  # Stores Q-values
        self.rewards = []  # Stores rewards
        self.losses = []  # Tracks model loss
        self.heatmap = np.zeros((24, 32))  # 480/20=24 rows, 640/20=32 columns

    def get_state(self, game):
        head = game.snake[0]
        # Convert pixel position to grid coordinates
        x_idx = min(max(0, int(head.x // BLOCK_SIZE)), self.heatmap.shape[1] - 1)
        y_idx = min(max(0, int(head.y // BLOCK_SIZE)), self.heatmap.shape[0] - 1)
        
        # Flip y-axis since tkinter has (0,0) at top-left
        y_idx = self.heatmap.shape[0] - 1 - y_idx
        
        self.heatmap[y_idx, x_idx] += 1

        point_l = Point(head.x - 20, head.y)
        point_r = Point(head.x + 20, head.y)
        point_u = Point(head.x, head.y - 20)
        point_d = Point(head.x, head.y + 20)
        
        dir_l = game.direction == Direction.LEFT
        dir_r = game.direction == Direction.RIGHT
        dir_u = game.direction == Direction.UP
        dir_d = game.direction == Direction.DOWN

        state = [
            (dir_r and game.is_collision(point_r)) or 
            (dir_l and game.is_collision(point_l)) or 
            (dir_u and game.is_collision(point_u)) or 
            (dir_d and game.is_collision(point_d)),
            (dir_u and game.is_collision(point_r)) or 
            (dir_d and game.is_collision(point_l)) or 
            (dir_l and game.is_collision(point_u)) or 
            (dir_r and game.is_collision(point_d)),
            (dir_d and game.is_collision(point_r)) or 
            (dir_u and game.is_collision(point_l)) or 
            (dir_r and game.is_collision(point_u)) or 
            (dir_l and game.is_collision(point_d)),
            dir_l, dir_r, dir_u, dir_d,
            game.food.x < game.head.x,
            game.food.x > game.head.x,
            game.food.y < game.head.y,
            game.food.y > game.head.y
        ]
        return np.array(state, dtype=int)

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def train_long_memory(self):
        if len(self.memory) > BATCH_SIZE:
            mini_sample = random.sample(self.memory, BATCH_SIZE)
        else:
            mini_sample = self.memory

        states, actions, rewards, next_states, dones = zip(*mini_sample)
        self.trainer.train_step(states, actions, rewards, next_states, dones)

    def train_short_memory(self, state, action, reward, next_state, done):
        self.trainer.train_step(state, action, reward, next_state, done)

    def get_action(self, state):
        self.epsilon = 80 - self.n_games
        final_move = [0, 0, 0]
        if random.randint(0, 200) < self.epsilon:
            move = random.randint(0, 2)
            final_move[move] = 1
        else:
            state0 = torch.tensor(state, dtype=torch.float)
            prediction = self.model(state0)
            move = torch.argmax(prediction).item()
            final_move[move] = 1
            self.q_values.append(prediction.tolist())
        self.action_counts[move] += 1
        return final_move

def train():
    agent = Agent()
    game = SnakeGameAI()
    record = 0
    # Main Window for Monitoring
    root = tk.Tk()
    root.title("Snake AI Monitoring")

    # UI Elements
    frame = tk.Frame(root)
    frame.pack()
    score_label = tk.Label(frame, text="Score: 0", font=("Arial", 14))
    score_label.pack()
    epsilon_label = tk.Label(frame, text="Epsilon: 0", font=("Arial", 14))
    epsilon_label.pack()

    # ✅ Use `plt.Figure()` to avoid extra pop-up figures
    fig = plt.Figure(figsize=(8, 8))  
    axs = fig.subplots(2, 2)
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.get_tk_widget().pack()

    # ✅ Create a dedicated Score Tracking window
    score_window = tk.Toplevel(root)
    score_window.title("Score Tracking")

    # ✅ Use `plt.Figure()` for score tracking (prevents extra pop-ups)
    score_fig = plt.Figure(figsize=(5, 4))  
    score_ax = score_fig.add_subplot(111)
    score_canvas = FigureCanvasTkAgg(score_fig, master=score_window)
    score_canvas.get_tk_widget().pack()

    # ✅ Score tracking variables
    plot_scores = []
    plot_mean_scores = []
    total_score = 0

    def update_visuals():
        # Clear all axes
        for ax in axs.flat:
            ax.clear()
        
        # 1. Action Distribution (unchanged)
        axs[0, 0].bar(['Left', 'Straight', 'Right'], agent.action_counts)
        axs[0, 0].set_title("Action Distribution")
        
        # 2. Q-Values Heatmap (improved)
        if agent.q_values:
            q_data = np.array(agent.q_values[-50:])  # Last 50 steps
            im = axs[0, 1].imshow(q_data.T, aspect='auto', cmap='viridis',
                                vmin=-1, vmax=1)  # Fixed scale for comparison
            axs[0, 1].set_title("Q-Values Over Time")
            axs[0, 1].set_xlabel("Time Step")
            axs[0, 1].set_yticks([0, 1, 2])
            axs[0, 1].set_yticklabels(['Left', 'Straight', 'Right'])
            
            if not hasattr(update_visuals, 'q_cbar'):
                update_visuals.q_cbar = fig.colorbar(im, ax=axs[0, 1])
                update_visuals.q_cbar.set_label("Q-Value")
        
        # 3. Rewards (unchanged)
        axs[1, 0].plot(agent.rewards[-50:])
        axs[1, 0].set_title("Rewards Over Time")
        axs[1, 0].set_xlabel("Time Step")
        
        # 4. Movement Heatmap (corrected version)
        heatmap_data = agent.heatmap.copy()
        
        # Normalize and handle empty cases
        if heatmap_data.max() > 0:
            heatmap_data = heatmap_data / heatmap_data.max()
        
        # Create heatmap with proper grid alignment
        im = axs[1, 1].imshow(heatmap_data, cmap='hot', 
                            interpolation='nearest',
                            origin='lower',
                            aspect='auto',
                            vmin=0, vmax=1)
        
        # Add grid lines at block boundaries
        axs[1, 1].set_xticks(np.arange(-0.5, 32, 1), minor=True)
        axs[1, 1].set_yticks(np.arange(-0.5, 24, 1), minor=True)
        axs[1, 1].grid(which='minor', color='white', linestyle='-', linewidth=0.2)
        axs[1, 1].set_title("Movement Heatmap")
        
        # Manage colorbar
        if not hasattr(update_visuals, 'heat_cbar'):
            update_visuals.heat_cbar = fig.colorbar(im, ax=axs[1, 1])
            update_visuals.heat_cbar.set_label("Visit Frequency")
        else:
            im.set_clim(vmin=0, vmax=1)
            update_visuals.heat_cbar.update_normal(im)
        
        canvas.draw()

    def game_loop():
        nonlocal total_score, record
        state_old = agent.get_state(game)
        final_move = agent.get_action(state_old)
        reward, done, score = game.play_step(final_move)

        state_new = agent.get_state(game)
        agent.train_short_memory(state_old, final_move, reward, state_new, done)
        agent.remember(state_old, final_move, reward, state_new, done)
        agent.rewards.append(reward)
        score_label.config(text=f"Score: {score}")
        epsilon_label.config(text=f"Epsilon: {agent.epsilon:.2f}")

        if done:
            game.reset()
            agent.n_games += 1
            agent.train_long_memory() 
            if score > record:
                record = score
                agent.model.save()
            print('Game', agent.n_games, 'Score', score, 'Record:', record)
            plot_scores.append(score)
            total_score += score
            mean_score = total_score / agent.n_games
            plot_mean_scores.append(mean_score)
            
            # Update score plot
            score_ax.clear()
            score_ax.plot(plot_scores, label='Scores')
            score_ax.plot(plot_mean_scores, label='Mean Scores')
            score_ax.set_title('Score Tracking')
            score_ax.set_xlabel('Games')
            score_ax.set_ylabel('Score')
            score_ax.legend()
            score_ax.grid(True)
            score_canvas.draw()
        update_visuals()
        root.after(100, game_loop)

    game_loop()
    root.mainloop()


if __name__ == '__main__':
    train()
