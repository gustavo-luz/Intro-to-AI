import tkinter as tk
import random
from enum import Enum
from collections import namedtuple
import numpy as np
import time

# Define game constants
BLOCK_SIZE = 20
# SPEED = 40 # for now disabled for max speed
WIDTH = 640
HEIGHT = 480

# Define colors
WHITE = "#FFFFFF"
RED = "#FF0000"
BLUE1 = "#0000FF"
BLUE2 = "#0064FF"
BLACK = "#000000"

class Direction(Enum):
    RIGHT = 1
    LEFT = 2
    UP = 3
    DOWN = 4

Point = namedtuple('Point', 'x, y')

class SnakeGameAI:
    def __init__(self, w=WIDTH, h=HEIGHT):
        self.w = w
        self.h = h
        
        # Create the main window
        self.root = tk.Tk()
        self.root.title("Snake AI")
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(self.root, width=self.w, height=self.h, bg=BLACK)
        self.canvas.pack()
        
        # Create score label
        self.score_var = tk.StringVar()
        self.score_var.set("Score: 0")
        self.score_label = tk.Label(self.root, textvariable=self.score_var, fg=WHITE, bg=BLACK, font=("Arial", 16))
        self.score_label.place(x=10, y=10)
        
        # Initialize game state
        self.reset()
        
        # For controlling game speed
        self.last_update_time = time.time()
    
    def on_close(self):
        self.root.quit()
        self.root.destroy()
    
    def reset(self):
        # Init game state
        self.direction = Direction.RIGHT
        
        self.head = Point(self.w/2, self.h/2)
        self.snake = [
            self.head,
            Point(self.head.x-BLOCK_SIZE, self.head.y),
            Point(self.head.x-(2*BLOCK_SIZE), self.head.y)
        ]
        
        self.score = 0
        self.score_var.set(f"Score: {self.score}")
        self.food = None
        self._place_food()
        self.frame_iteration = 0
    
    def _place_food(self):
        x = random.randint(0, (self.w-BLOCK_SIZE)//BLOCK_SIZE) * BLOCK_SIZE
        y = random.randint(0, (self.h-BLOCK_SIZE)//BLOCK_SIZE) * BLOCK_SIZE
        self.food = Point(x, y)
        if self.food in self.snake:
            self._place_food()
    
    def play_step(self, action):
        self.frame_iteration += 1
        
        # Process any pending events
        self.root.update()
        
        # Move based on action
        self._move(action)
        self.snake.insert(0, self.head)
        
        # Check if game over
        reward = 0
        game_over = False
        if self.is_collision() or self.frame_iteration > 100*len(self.snake):
            game_over = True
            reward = -10
            return reward, game_over, self.score
        
        # Place new food or just move
        if self.head.x == self.food.x and self.head.y == self.food.y:
            self.score += 1
            reward = 10
            self.score_var.set(f"Score: {self.score}")
            self._place_food()
        else:
            self.snake.pop()
        
        # Update UI
        self._update_ui()
        
        # Control game speed
        # current_time = time.time()
        # elapsed = current_time - self.last_update_time
        # # sleep_time = max(0, (1.0/SPEED) - elapsed)
        # sleep_time = max(0, (0.01) - elapsed)  # Fixed fast speed (10ms)
        sleep_time = 0.0001  # Fixed fast speed (10ms)
        time.sleep(sleep_time)
        self.last_update_time = time.time()
        
        return reward, game_over, self.score
    
    def is_collision(self, pt=None):
        if pt is None:
            pt = self.head
        
        # Hits boundary
        if pt.x >= self.w or pt.x < 0 or pt.y >= self.h or pt.y < 0:
            return True
        
        # Hits itself
        if pt in self.snake[1:]:
            return True
        
        return False
    
    def _update_ui(self):
        self.canvas.delete("all")
        
        # Draw snake
        for pt in self.snake:
            self.canvas.create_rectangle(
                pt.x, pt.y, pt.x + BLOCK_SIZE, pt.y + BLOCK_SIZE, 
                fill=BLUE1, outline="")
            self.canvas.create_rectangle(
                pt.x + 4, pt.y + 4, pt.x + BLOCK_SIZE - 4, pt.y + BLOCK_SIZE - 4, 
                fill=BLUE2, outline="")
        
        # Draw food
        self.canvas.create_rectangle(
            self.food.x, self.food.y, self.food.x + BLOCK_SIZE, self.food.y + BLOCK_SIZE,
            fill=RED, outline="")
        
        self.canvas.update()
    
    def _move(self, action):
        # [straight, right, left]
        clock_wise = [Direction.RIGHT, Direction.DOWN, Direction.LEFT, Direction.UP]
        idx = clock_wise.index(self.direction)
        
        if np.array_equal(action, [1, 0, 0]):
            new_dir = clock_wise[idx]  # No change
        elif np.array_equal(action, [0, 1, 0]):
            next_idx = (idx + 1) % 4
            new_dir = clock_wise[next_idx]  # Right turn r -> d -> l -> u
        else:  # [0, 0, 1]
            next_idx = (idx - 1) % 4
            new_dir = clock_wise[next_idx]  # Left turn r -> u -> l -> d
        
        self.direction = new_dir
        
        x = self.head.x
        y = self.head.y
        if self.direction == Direction.RIGHT:
            x += BLOCK_SIZE
        elif self.direction == Direction.LEFT:
            x -= BLOCK_SIZE
        elif self.direction == Direction.DOWN:
            y += BLOCK_SIZE
        elif self.direction == Direction.UP:
            y -= BLOCK_SIZE
        
        self.head = Point(x, y)

# Example usage (for testing)
if __name__ == "__main__":
    game = SnakeGameAI()
    
    # Simple test loop - snake moves randomly
    while True:
        # Generate random action [straight, right, left]
        action = np.zeros(3)
        action[random.randint(0, 2)] = 1
        
        # Play one step
        reward, game_over, score = game.play_step(action)
        
        if game_over:
            print(f"Game Over! Final Score: {score}")
            break
    
    game.root.mainloop()  # Keep window open after game over
