# -*- coding: utf-8 -*-


import pygame
import random

import heapq

import numpy as np
from collections import deque

pygame.font.init()
random.seed(12345)

BLOCKTYPES = 4

VALUE_FONT = pygame.font.SysFont("comicsans", 20)   

    
# třída reprezentující prostředí
class Env:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.arr = np.zeros((width, height), dtype=int)
        
        # <----- jak reprezentovat hodnoty stavů/akcí?

        self.startx = 0
        self.starty = 0
        self.goalx = width-1
        self.goaly = height-1
        self.dieprob = 0.5
        self.diereward = 0.0
        self.movereward = 0.0
        self.goalreward = 0.0
        self.wallreward = 0.0
        self.episodenum = 0  # pocet epizod uceni/pocitani/...
    
        
    def is_valid_xy(self, x, y):      
        if x >= 0 and x < self.width and y >= 0 and y < self.height:
            return True
        return False 
        
    def set_start(self, x, y):
        if self.is_valid_xy(x, y):
            self.startx = x
            self.starty = y
            
    def set_goal(self, x, y):
        if self.is_valid_xy(x, y):
            self.goalx = x
            self.goaly = y
               
        
    def is_empty(self, x, y):
        if self.arr[x, y] == 0:
            return True
        return False
    
    
    # mnozina moznych tahu
    def possible_moves(self, x, y):
        moves = []
        if x-1 >= 0:
            moves.append(0)
        if y-1 >= 0:
            moves.append(1)
        if x+1 < self.width:
            moves.append(2)
        if y+1 < self.height:
            moves.append(3)
            
        return moves
    
        
    def add_danger_block(self, x, y):
        if self.arr[x, y] == 0:
            r = random.randint(1, BLOCKTYPES)
            self.arr[x, y] = r
            
    def get_tile_type(self, x, y):
        return self.arr[x, y]        
          
    # funkce aktualnich odmen
    # action = 0, 1, 2, 3 = left, up, right, down       
    # vraci nove x, y, odmenu, True pokud je stav terminalni
    def move(self, x, y, action):
        
        newx = x
        newy = y
        
        if action == 0:
            newx -= 1
        if action == 1:
            # newy += 1
            newy -= 1
        if action == 2:
            newx += 1
        if action == 3:
            # newy -= 1
            newy += 1
            
        # nevalidní koordinát - náraz do zdi
        if not self.is_valid_xy(newx, newy):
           return (x, y, self.wallreward, False) 
        
        # nebezpečí
        if self.arr[newx, newy] > 0:
            r = random.random()
            if r < self.dieprob:
                return (newx, newy, self.diereward, True)
            else:
                return (newx, newy, self.movereward, False)
        
        # dosáhnutí cíle
        if newx==self.goalx and newy==self.goaly:
            return (newx, newy, self.goalreward, True)
        
        return (newx, newy, self.movereward, False)
    
    

# definice prostředí -----------------------------------

TILESIZE = 100



#<------    definice prostředí a překážek !!!!!!

WIDTH = 4
HEIGHT = 4

env = Env(WIDTH, HEIGHT)



WIN = pygame.display.set_mode((env.width * TILESIZE, env.height * TILESIZE))

pygame.display.set_caption("Danger world, ep: " + str(env.episodenum))

pygame.font.init()

WHITE = (255, 255, 255)


DIRECTIONS = ["left", "down", "right", "up"]

FPS = 60



# pond, tree, house, car

BOOM_FONT = pygame.font.SysFont("comicsans", 100)   
LEVEL_FONT = pygame.font.SysFont("comicsans", 20)   


TILE_IMAGE = pygame.image.load("sprites/tile.jpg")
MTILE_IMAGE = pygame.image.load("sprites/markedtile.jpg")
DANGER1_IMAGE = pygame.image.load("sprites/danger1.jpg")
DANGER2_IMAGE = pygame.image.load("sprites/danger2.jpg")
DANGER3_IMAGE = pygame.image.load("sprites/danger3.jpg")
DANGER4_IMAGE  = pygame.image.load("sprites/danger4.jpg")
FLAG_IMAGE = pygame.image.load("sprites/flag.jpg")


TILE = pygame.transform.scale(TILE_IMAGE, (TILESIZE, TILESIZE))
MTILE = pygame.transform.scale(MTILE_IMAGE, (TILESIZE, TILESIZE))
DANGER1 = pygame.transform.scale(DANGER1_IMAGE, (TILESIZE, TILESIZE))
DANGER2 = pygame.transform.scale(DANGER2_IMAGE, (TILESIZE, TILESIZE))
DANGER3 = pygame.transform.scale(DANGER3_IMAGE, (TILESIZE, TILESIZE))
DANGER4 = pygame.transform.scale(DANGER4_IMAGE, (TILESIZE, TILESIZE))
FLAG = pygame.transform.scale(FLAG_IMAGE, (TILESIZE, TILESIZE))




        
        
        

def draw_window(env, Q):

    for i in range(env.width):
        for j in range(env.height):
            t = env.get_tile_type(i, j)
            if t == 1:
                WIN.blit(DANGER1, (i*TILESIZE, (env.height - j - 1)*TILESIZE))
            elif t == 2:
                WIN.blit(DANGER2, (i*TILESIZE, (env.height - j - 1)*TILESIZE))
            elif t == 3:
                WIN.blit(DANGER3, (i*TILESIZE, (env.height - j - 1)*TILESIZE))
            elif t == 4:
                WIN.blit(DANGER4, (i*TILESIZE, (env.height - j - 1)*TILESIZE))  
            else:
                WIN.blit(TILE, (i*TILESIZE, (env.height - j - 1)*TILESIZE))
                 
    
    WIN.blit(FLAG, (env.goalx * TILESIZE, (env.height - env.goaly - 1) * TILESIZE))   
    WIN.blit(MTILE, (env.startx * TILESIZE, (env.height - env.starty - 1) * TILESIZE))

    for i in range(env.width):
        for j in range(env.height):  

            direct = DIRECTIONS[np.argmax(Q[i, j, :])] #<------ vypis akce, ci cohokoli jineho

            t = VALUE_FONT.render(direct, 1, WHITE)   

            WIN.blit(t, (i*TILESIZE + 10, (env.height - j - 1)*TILESIZE + 10))
    
       
    pygame.display.update()
    
    
    

def main():
    
    
    # start a cil
    env.set_start(0, 0)
    env.set_goal(WIDTH-1, HEIGHT-1)
    
    

    # pravdepodobnost umrti na danger polickach
    env.dieprob = 0.7
    
    # nastaveni odmen
    env.diereward = -100 # umrti
    env.wallreward = -5.0 # odmena za vykroceni z herniho planu
    env.movereward = 0.0 # pohyb
    env.goalreward = 40.0 # nalezeni cil
    

    # nebezpeci
    env.add_danger_block(2, 1)
    env.add_danger_block(2, 3)   
    env.add_danger_block(0, 3)   
    
    clock = pygame.time.Clock()
    
    run = True

    # Initialize Q-matrix
    Q = np.zeros((env.width, env.height, len(DIRECTIONS)))

    # Hyperparameters
    learning_rate = 0.1
    discount_factor = 0.9
    exploration_prob = 0.2
    num_episodes = 1000

    def epsilon_greedy_action(x, y, exploation=False):
        if not exploation and np.random.rand() < exploration_prob:
            return np.random.choice(len(DIRECTIONS))
        else:
            return np.argmax(Q[x, y, :])

    def update_q_value(x, y, action, new_x, new_y, reward):
        Q[x, y, action] = (1 - learning_rate) * Q[x, y, action] + \
                        learning_rate * (reward + discount_factor * np.max(Q[new_x, new_y, :]))

    def train_q_learning(env):
        for episode in range(num_episodes):
            x, y = env.startx, env.starty
            terminal = False

            while not terminal:
                action = epsilon_greedy_action(x, y)
                new_x, new_y, reward, terminal = env.move(x, y, action)

                update_q_value(x, y, action, new_x, new_y, reward)

                x, y = new_x, new_y

    # reinforcement Q learning
    train_q_learning(env)
    
    while run:  
        clock.tick(FPS)
                
        # choose action using learned Q-values
        action = epsilon_greedy_action(env.startx, env.starty, True)

        # execute chosen action and get new state
        new_x, new_y, reward, terminal = env.move(env.startx, env.starty, action)

        # update Q-value based on the new state and reward
        update_q_value(env.startx, env.starty, action, new_x, new_y, reward)

        # Update agent's position
        env.startx, env.starty = new_x, new_y

        env.episodenum += 1
        pygame.display.set_caption("Danger world, ep: " + str(env.episodenum))

        
        draw_window(env, Q)

        if terminal:
            env.startx, env.starty = 0, 0
            clock.tick(FPS)
            draw_window(env, Q)
        
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
    
    pygame.quit()    


if __name__ == "__main__":
    main()