import tkinter as tk
import random
from enum import Enum
from collections import namedtuple
import time

# Define game constants
BLOCK_SIZE = 20
SPEED = 150  # Lower is faster
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

class SnakeGameTk:
    def __init__(self, root, width=WIDTH, height=HEIGHT):
        self.root = root
        self.root.title("Snake Game")
        self.root.resizable(False, False)
        
        self.w = width
        self.h = height
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(root, width=self.w, height=self.h, bg=BLACK)
        self.canvas.pack()
        
        # Create score label
        self.score_var = tk.StringVar()
        self.score_var.set("Score: 0")
        self.score_label = tk.Label(root, textvariable=self.score_var, fg=WHITE, bg=BLACK, font=("Arial", 16))
        self.score_label.place(x=10, y=10)
        
        # Set up key bindings
        self.root.bind("<Left>", lambda e: self.change_direction(Direction.LEFT))
        self.root.bind("<Right>", lambda e: self.change_direction(Direction.RIGHT))
        self.root.bind("<Up>", lambda e: self.change_direction(Direction.UP))
        self.root.bind("<Down>", lambda e: self.change_direction(Direction.DOWN))
        
        # Initialize game state
        self.reset_game()
        
        # Start game loop
        self.update()
    
    def reset_game(self):
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
        self.place_food()
        self.game_over = False
    
    def place_food(self):
        x = random.randint(0, (self.w-BLOCK_SIZE)//BLOCK_SIZE) * BLOCK_SIZE
        y = random.randint(0, (self.h-BLOCK_SIZE)//BLOCK_SIZE) * BLOCK_SIZE
        self.food = Point(x, y)
        if self.food in self.snake:
            self.place_food()
    
    def change_direction(self, direction):
        # Prevent 180-degree turns
        if (direction == Direction.LEFT and self.direction != Direction.RIGHT) or \
           (direction == Direction.RIGHT and self.direction != Direction.LEFT) or \
           (direction == Direction.UP and self.direction != Direction.DOWN) or \
           (direction == Direction.DOWN and self.direction != Direction.UP):
            self.direction = direction
    
    def move(self):
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
        self.snake.insert(0, self.head)
        
        # Check if we ate food
        if self.head.x == self.food.x and self.head.y == self.food.y:
            self.score += 1
            self.score_var.set(f"Score: {self.score}")
            self.place_food()
        else:
            self.snake.pop()
    
    def is_collision(self):
        # Check if hit boundary
        if self.head.x >= self.w or self.head.x < 0 or self.head.y >= self.h or self.head.y < 0:
            return True
        
        # Check if hit self
        if self.head in self.snake[1:]:
            return True
        
        return False
    
    def update_ui(self):
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
    
    def update(self):
        if not self.game_over:
            self.move()
            self.game_over = self.is_collision()
            
            if self.game_over:
                self.canvas.create_text(
                    self.w/2, self.h/2, 
                    text=f"Game Over! Score: {self.score}", 
                    fill=WHITE, font=("Arial", 24))
                self.canvas.create_text(
                    self.w/2, self.h/2 + 40, 
                    text="Press Space to play again", 
                    fill=WHITE, font=("Arial", 18))
                self.root.bind("<space>", lambda e: self.reset_game())
            else:
                self.update_ui()
                self.root.after(SPEED, self.update)

if __name__ == "__main__":
    root = tk.Tk()
    game = SnakeGameTk(root)
    root.mainloop()
