# -*- coding: utf-8 -*-


import pygame
import random

import numpy as np
from collections import deque




BLOCKTYPES = 5


# třída reprezentující prostředí
class Env:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.arr = np.zeros((height, width), dtype=int)
        self.startx = 0
        self.starty = 0
        self.goalx = width-1
        self.goaly = height-1
        
    def is_valid_xy(self, x, y):      
        if x >= 0 and x < self.width and y >= 0 and y < self.height and self.arr[y, x] == 0:
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
        if self.arr[y, x] == 0:
            return True
        return False
    
        
    def add_block(self, x, y):
        if self.arr[y, x] == 0:
            r = random.randint(1, BLOCKTYPES)
            self.arr[y, x] = r
                
    def get_neighbors(self, x, y):
        l = []
        if x-1 >= 0 and self.arr[y, x-1] == 0:
            l.append((x-1, y))
        
        if x+1 < self.width and self.arr[y, x+1] == 0:
            l.append((x+1, y))
            
        if y-1 >= 0 and self.arr[y-1, x] == 0:
            l.append((x, y-1))
        
        if y+1 < self.height and self.arr[y+1, x] == 0:
            l.append((x, y+1))
        
        return l
        
     
    def get_tile_type(self, x, y):
        return self.arr[y, x]
    
    
    # vrací dvojici 1. frontu dvojic ze startu do cíle, 2. seznam dlaždic
    # k zobrazení - hodí se např. pro zvýraznění cesty, nebo expandovaných uzlů
    # start a cíl se nastaví pomocí set_start a set_goal
        
    # path_planner parametry
    # 1 - GBFS
    # 2 - Dijkstra
    # 3 - A*
    def path_planner(self, method):

        # common params for all path searching algorithms
        # array of predecessors
        predecessors = np.full((self.width, self.height), None)
        # all active elements (empty cells that hasn't been expanded yet)             
        active_elements = set([(i, j) for i in range(self.width) for j in range(self.height) if self.is_empty(i, j)])

        # 1. Greedy best first search (GBFS)
        if method == 1:
            # heuristics for all cells
            heur = np.full((self.width, self.height), None)
            for i in range(self.width):
                for j in range(self.height):
                    if self.is_empty(i, j):
                        # calculating distance for every empty cell
                        heur[i, j] = ((i - self.goalx) ** 2 + (j - self.goaly) ** 2) ** 0.5

            # expanded cells - with the start cell inside
            fringe = {(self.startx, self.starty)}
            while True:
                active_indices_fringe = fringe & active_elements

                # if the fringe is full of inactive elements, there is no way to get to the finish
                if len(active_indices_fringe) == 0:
                    print("No solution!")
                    break

                # finding the element with the lowest heuristic in the fringe
                active_indices_fringe_list = list(active_indices_fringe)
                min_index_flat = np.argmin(heur[[i[0] for i in active_indices_fringe_list], [i[1] for i in active_indices_fringe_list]])
                min_alive = active_indices_fringe_list[min_index_flat]

                # expanding the node = removing from the active elements
                active_elements.remove(min_alive)

                # handle goal cell
                if min_alive == (self.goalx, self.goaly):
                    break

                 # exploring neighbors of the best heuristic cell
                for neighbor_x, neighbor_y in self.get_neighbors(min_alive[0], min_alive[1]):
                    # if optimal path to this element has already been found, continue
                    if (neighbor_x, neighbor_y) not in active_elements:
                        continue
                    else:
                        # save predecessor and add to fringe
                        predecessors[neighbor_x, neighbor_y] = (min_alive[0], min_alive[1])
                        fringe.add((neighbor_x, neighbor_y))
              


        # 2. Dijkstra
        if method == 2:
            # matrix of min distances for all cells, full of infinities
            d = np.full((self.width, self.height), np.inf)
            # start position = 0
            d[self.startx, self.starty] = 0

            while True:
                # find minimum in the d matrix
                active_indices_list = list(active_elements)
                # no active node inside the list
                if len(active_indices_list) == 0:
                    print("No solution!")
                    break
                min_index_flat = np.argmin(d[[i[0] for i in active_indices_list], [i[1] for i in active_indices_list]])
                min_alive = active_indices_list[min_index_flat]


                # remove min_element
                active_elements.remove(min_alive)
                # handle fgoal cell
                if min_alive == (self.goalx, self.goaly):
                    break
                for neighbor_x, neighbor_y in self.get_neighbors(min_alive[0], min_alive[1]):
                    # if optimal path to this element has already been found, continue
                    if (neighbor_x, neighbor_y) not in active_elements:
                        continue
                    # if new optimal route has been found, update lists
                    if d[min_alive[0], min_alive[1]] + 1 < d[neighbor_x, neighbor_y]:
                        d[neighbor_x, neighbor_y] = d[min_alive[0], min_alive[1]] + 1
                        predecessors[neighbor_x, neighbor_y] = (min_alive[0], min_alive[1])


        # 3. A*
        if method == 3:
            # best possible path + heuristics h(u) for all cells
            path_eval = np.empty((self.width, self.height), dtype=object)
            for i in range(self.width):
                for j in range(self.height):
                    # optimal distance so far (infinity), cell-goal Manhattan distance
                    path_eval[i, j] = np.array([np.inf, abs(i - self.goalx) + abs(j - self.goaly)])
            print(path_eval)
            # setting path length 0 for starting point
            path_eval[self.startx, self.starty][0] = 0

            # expanded cells - with the start cell inside
            fringe = {(self.startx, self.starty)}
            while True:
                active_indices_fringe = fringe & active_elements

                # if the fringe is full of inactive elements, there is no way to get to the finish
                if len(active_indices_fringe) == 0:
                    print("No solution!")
                    break

                # matrix f(u) = h(u) + g(u)
                sum_path_eval = np.zeros((self.width, self.height))
                for i in range(self.width):
                    for j in range(self.height):
                        sum_path_eval[i, j] = path_eval[i, j][0] + path_eval[i, j][1]

                # finding the element with the lowest path_eval in the fringe
                active_indices_fringe_list = list(active_indices_fringe)
                min_index_flat = np.argmin(sum_path_eval[[i[0] for i in active_indices_fringe_list], [i[1] for i in active_indices_fringe_list]])
                min_alive = active_indices_fringe_list[min_index_flat]

                # expanding the node = removing from the active elements
                active_elements.remove(min_alive)

                # handle goal cell
                if min_alive == (self.goalx, self.goaly):
                    break

                # exploring neighbors of the best f(u) cell
                for neighbor_x, neighbor_y in self.get_neighbors(min_alive[0], min_alive[1]):
                    # if optimal path to this element has already been found, continue
                    if (neighbor_x, neighbor_y) not in active_elements:
                        continue
                    else:
                        # save predecessor and add to fringe
                        fringe.add((neighbor_x, neighbor_y))
                        # updating the g(u) if it improves the path length
                        if path_eval[min_alive[0], min_alive[1]][0] + 1 < path_eval[neighbor_x, neighbor_y][0]:
                            path_eval[neighbor_x, neighbor_y][0] = path_eval[min_alive[0], min_alive[1]][0] + 1
                            predecessors[neighbor_x, neighbor_y] = (min_alive[0], min_alive[1])


        # expanded cells = predecessor value has been updatet at least once
        visited = [(i, j) for i in range(self.width) for j in range(self.height) if predecessors[i, j] != None]

        # reconstructing the path
        deque_path = deque()
        x, y = self.goalx, self.goaly
        while True:
            deque_path.appendleft((x, y))
            if x == self.startx and y == self.starty:
                break
            x, y = predecessors[x, y]
            
                
        return deque_path, visited
    
       
        
# třída reprezentující ufo        
class Ufo:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.path = deque()
        self.tiles = []
        self.passed = []
    
   
    # přemístí ufo na danou pozici - nejprve je dobré zkontrolovat u prostředí, 
    # zda je pozice validní
    def move(self, x, y):
        self.x = x
        self.y = y
        self.passed.append((x, y))

   
    
    # reaktivní navigace <------------------------ !!!!!!!!!!!! ZDE DOPLNIT
    def reactive_go(self, env):
        r = random.random()
        
        dx = 0
        dy = 0
        
        if r > 0.5: 
            r = random.random()
            if r < 0.5:
                dx = -1
            else:
                dx = 1
            
        else:
            r = random.random()
            if r < 0.5:
                dy = -1
            else:
                dy = 1
        
        return (self.x + dx, self.y + dy)
        
    
    # nastaví cestu k vykonání 
    def set_path(self, p, t=[]):
        self.path = p
        self.tiles = t
   
    
    # vykoná naplánovanou cestu, v každém okamžiku na vyzvání vydá další
    # way point 
    def execute_path(self):
        if self.path:
            return self.path.popleft()
        return (-1, -1)
       




# definice prostředí -----------------------------------

TILESIZE = 50



#<------    definice prostředí a překážek !!!!!!
def create_env(WIDTH, HEIGHT, start, goal, blocks):
    env = Env(WIDTH, HEIGHT)
    env.set_start(start[0], start[1])
    env.set_goal(goal[0], goal[1])
    for x, y in blocks:
        env.add_block(x, y)

    ufo = Ufo(env.startx, env.starty)

    return env, ufo

random.seed(123)

blocks_env_1 = [
    (1, 1),
    (2, 2),
    (3, 3),
    (4, 4),
    (5, 5),
    (6, 6),
    (7, 7),
    (8, 8),
    (0, 8),
    (11, 1),
    (11, 6),
    (1, 3),
    (2, 4),
    (4, 5),
    (2, 6),
    (3, 7),
    (4, 8),
    (0, 8),
    (1, 8),
    (2, 8),
    (3, 5),
    (4, 8),
    (5, 6),
    (6, 4),
    (7, 2),
    (8, 1)
]



blocks_env_2 = list(set([(random.randint(0, 29), random.randint(0, 18)) for _ in range(180)]))
if (3, 3) in blocks_env_2:
    blocks_env_2.remove((3, 3))
if (25, 19) in blocks_env_2:
    blocks_env_2.remove((25, 19))

blocks_env_3 = blocks_env_2 + [(19, 10), (22, 9), (23, 9), (25, 8), (24, 15), (19, 16), (9, 17)]


y = int(input("Choose maze:\n1 = given maze\n2 = big easy maze\n3 = big complicated maze\nelse empty maze\n"))
print("_" * 40)

if y == 1:
    env, ufo = create_env(12, 9, (0, 0), (9, 7), blocks_env_1) # option 1
elif y == 2:
    env, ufo = create_env(30, 20, (3, 3), (28, 17), blocks_env_2) # option 2
elif y == 3:
    env, ufo = create_env(30, 20, (3, 3), (28, 17), blocks_env_3) # option 2
else:
    env, ufo = create_env(35, 18, (1, 7), (34, 9), [])



WIN = pygame.display.set_mode((env.width * TILESIZE, env.height * TILESIZE))

pygame.display.set_caption("Block world")

pygame.font.init()

WHITE = (255, 255, 255)



FPS = 10



# pond, tree, house, car

BOOM_FONT = pygame.font.SysFont("comicsans", 100)   
LEVEL_FONT = pygame.font.SysFont("comicsans", 20)   


TILE_IMAGE = pygame.image.load(r".\sprites\tile.jpg")
MTILE_IMAGE = pygame.image.load(r".\sprites\markedtile.jpg")
MTILE2_IMAGE = pygame.image.load(r".\sprites\markedtile2.jpg")
HOUSE1_IMAGE = pygame.image.load(r".\sprites\house1.jpg")
HOUSE2_IMAGE = pygame.image.load(r".\sprites\house2.jpg")
HOUSE3_IMAGE = pygame.image.load(r".\sprites\house3.jpg")
TREE1_IMAGE  = pygame.image.load(r".\sprites\tree1.jpg")
TREE2_IMAGE  = pygame.image.load(r".\sprites\tree2.jpg")
UFO_IMAGE = pygame.image.load(r".\sprites\ufo.jpg")
FLAG_IMAGE = pygame.image.load(r".\sprites\flag.jpg")


TILE = pygame.transform.scale(TILE_IMAGE, (TILESIZE, TILESIZE))
MTILE = pygame.transform.scale(MTILE_IMAGE, (TILESIZE, TILESIZE))
MTILE2 = pygame.transform.scale(MTILE2_IMAGE, (TILESIZE, TILESIZE))
HOUSE1 = pygame.transform.scale(HOUSE1_IMAGE, (TILESIZE, TILESIZE))
HOUSE2 = pygame.transform.scale(HOUSE2_IMAGE, (TILESIZE, TILESIZE))
HOUSE3 = pygame.transform.scale(HOUSE3_IMAGE, (TILESIZE, TILESIZE))
TREE1 = pygame.transform.scale(TREE1_IMAGE, (TILESIZE, TILESIZE))
TREE2 = pygame.transform.scale(TREE2_IMAGE, (TILESIZE, TILESIZE))
UFO = pygame.transform.scale(UFO_IMAGE, (TILESIZE, TILESIZE))
FLAG = pygame.transform.scale(FLAG_IMAGE, (TILESIZE, TILESIZE))




        
        
        

def draw_window(ufo, env):

    for i in range(env.width):
        for j in range(env.height):
            t = env.get_tile_type(i, j)
            if t == 1:
                WIN.blit(TREE1, (i*TILESIZE, j*TILESIZE))
            elif t == 2:
                WIN.blit(HOUSE1, (i*TILESIZE, j*TILESIZE))
            elif t == 3:
                WIN.blit(HOUSE2, (i*TILESIZE, j*TILESIZE))
            elif t == 4:
                WIN.blit(HOUSE3, (i*TILESIZE, j*TILESIZE))  
            elif t == 5:
                WIN.blit(TREE2, (i*TILESIZE, j*TILESIZE))     
            else:
                WIN.blit(TILE, (i*TILESIZE, j*TILESIZE))
    
        
    for (x, y) in ufo.tiles:
        WIN.blit(MTILE, (x*TILESIZE, y*TILESIZE))
        
    for (x, y) in ufo.passed:
        WIN.blit(MTILE2, (x*TILESIZE, y*TILESIZE))
    
    WIN.blit(FLAG, (env.goalx * TILESIZE, env.goaly * TILESIZE))        
    WIN.blit(UFO, (ufo.x * TILESIZE, ufo.y * TILESIZE))
        
    pygame.display.update()
    
    


    

def main():
    
    
    #  <------------   nastavení startu a cíle prohledávání !!!!!!!!!!
    
    # path_planner parametry
    # 1 - GBFS
    # 2 - Dijkstra
    # 3 - A*
    x = int(input("Choose maze solving algorithm:\n1 = GBSF\n2 = Dijkstra\n3 = A*\n"))
    print("_" * 40)
    p, t = env.path_planner(x)   # cesta pomocí path_planneru prostředí
    ufo.set_path(p, t)
 
    
    clock = pygame.time.Clock()
    
    run = True
    go = False    
    
    while run:  
        
        clock.tick(FPS)
        

        # <---- reaktivní pohyb dokud nedojde do cíle 
        if (ufo.x != env.goalx) or (ufo.y != env.goaly):        
            x, y = ufo.execute_path()
            
            if env.is_valid_xy(x, y):
                ufo.move(x, y)
            else:
                print('[', x, ',', y, ']', "wrong coordinate !")
        

                        
        draw_window(ufo, env)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
    
    pygame.quit()    


if __name__ == "__main__":
    main()