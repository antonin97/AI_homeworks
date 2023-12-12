# -*- coding: utf-8 -*-


import pygame
import random

import heapq

import numpy as np
from collections import deque

pygame.font.init()


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
    
        
    def add_block(self, x, y, t):
        if self.arr[x, y] == 0:
            #r = random.randint(1, BLOCKTYPES)
            self.arr[x, y] = t
            
    def get_tile_type(self, x, y):
        return self.arr[x, y]        
          
    # funkce aktualnich odmen
    # action = 0, 1, 2, 3 = left, up, right, down       
    # vraci nove x, y, odmenu, false pokud je stav terminalni
    def move(self, x, y, action):
        
        newx = x
        newy = y
        
        if action == 0:
            newx -= 1
        if action == 1:
            newy += 1
        if action == 2:
            newx += 1
        if action == 3:
            newy -= 1
            
        if not self.is_valid_xy(newx, newy):
           return (x, y, self.wallreward, False) 
        
        if self.arr[newx, newy] > 0:
            r = random.random()
            if r < self.dieprob:
                return (newx, newy, self.diereward, True)
            else:
                return (newx, newy, self.movereward, False)
        
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


DIRECTIONS = ["left", "up", "right", "down"]

FPS = 1



# pond, tree, house, car

BOOM_FONT = pygame.font.SysFont("comicsans", 100)   
LEVEL_FONT = pygame.font.SysFont("comicsans", 20)   


TILE_IMAGE = pygame.image.load("tile.jpg")
MTILE_IMAGE = pygame.image.load("markedtile.jpg")
DANGER1_IMAGE = pygame.image.load("danger1.jpg")
DANGER2_IMAGE = pygame.image.load("danger2.jpg")
DANGER3_IMAGE = pygame.image.load("danger3.jpg")
DANGER4_IMAGE  = pygame.image.load("danger4.jpg")
FLAG_IMAGE = pygame.image.load("flag.jpg")


TILE = pygame.transform.scale(TILE_IMAGE, (TILESIZE, TILESIZE))
MTILE = pygame.transform.scale(MTILE_IMAGE, (TILESIZE, TILESIZE))
DANGER1 = pygame.transform.scale(DANGER1_IMAGE, (TILESIZE, TILESIZE))
DANGER2 = pygame.transform.scale(DANGER2_IMAGE, (TILESIZE, TILESIZE))
DANGER3 = pygame.transform.scale(DANGER3_IMAGE, (TILESIZE, TILESIZE))
DANGER4 = pygame.transform.scale(DANGER4_IMAGE, (TILESIZE, TILESIZE))
FLAG = pygame.transform.scale(FLAG_IMAGE, (TILESIZE, TILESIZE))




        
        
        

def draw_window(env):

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

            direct = DIRECTIONS[0]  #<------ vypis akce, ci cohokoli jineho
            
            t = VALUE_FONT.render(direct, 1, WHITE)   

            WIN.blit(t, (i*TILESIZE + 10, (env.height - j - 1)*TILESIZE + 10))    
       
    pygame.display.update()
    
    
    

def main():
    
    
    # start a cil
    env.set_start(0, 0)
    env.set_goal(WIDTH-1, HEIGHT-1)
    
    
    # pravdepodobnost umrti na neprazdnych polickach
    env.dieprob = 0.2
    
    # nastaveni odmen
    env.diereward = -100 # umrti
    env.wallreward = -1.0 # odmena za vykroceni z herniho planu
    env.movereward = 0.0 # pohyb
    env.goalreward = 30.0 # nalezeni cil
    

    # nebezpeci
    env.add_block(2, 1, 1)
    env.add_block(2, 3, 3)   
    env.add_block(0, 3, 4)   
    
    clock = pygame.time.Clock()
    
    run = True
    
    while run:  
        
        clock.tick(FPS)
        

       # <------ update strategie, uceni, vypoctu?

        env.episodenum += 1
        pygame.display.set_caption("Danger world, ep: " + str(env.episodenum))

                        
        
        draw_window(env)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
    
    pygame.quit()    


if __name__ == "__main__":
    main()