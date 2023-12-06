# -*- coding: utf-8 -*-
import pygame
import numpy as np
import random
import math


from deap import base
from deap import creator
from deap import tools


pygame.font.init()

random.seed(13246)

#-----------------------------------------------------------------------------
# Parametry hry 
#-----------------------------------------------------------------------------

WIDTH, HEIGHT = 900, 500

WIN = pygame.display.set_mode((WIDTH, HEIGHT))

WHITE = (255, 255, 255)


TITLE = "Boom Master"
pygame.display.set_caption(TITLE)

FPS = 80
ME_VELOCITY = 5
MAX_MINE_VELOCITY = 3



BOOM_FONT = pygame.font.SysFont("comicsans", 100)   
LEVEL_FONT = pygame.font.SysFont("comicsans", 20)   



ENEMY_IMAGE  = pygame.image.load("mine.png")
ME_IMAGE = pygame.image.load("me.png")
SEA_IMAGE = pygame.image.load("sea.png")
FLAG_IMAGE = pygame.image.load("flag.png")


ENEMY_SIZE = 50
ME_SIZE = 50

ENEMY = pygame.transform.scale(ENEMY_IMAGE, (ENEMY_SIZE, ENEMY_SIZE))
ME = pygame.transform.scale(ME_IMAGE, (ME_SIZE, ME_SIZE))
SEA = pygame.transform.scale(SEA_IMAGE, (WIDTH, HEIGHT))
FLAG = pygame.transform.scale(FLAG_IMAGE, (ME_SIZE, ME_SIZE))






# ----------------------------------------------------------------------------
# třídy objektů 
# ----------------------------------------------------------------------------

# trida reprezentujici minu
class Mine:
    def __init__(self):

        # random x direction
        if random.random() > 0.5:
            self.dirx = 1
        else: 
            self.dirx = -1
            
        # random y direction    
        if random.random() > 0.5:
            self.diry = 1
        else: 
            self.diry = -1

        x = random.randint(200, WIDTH - ENEMY_SIZE) 
        y = random.randint(200, HEIGHT - ENEMY_SIZE) 
        self.rect = pygame.Rect(x, y, ENEMY_SIZE, ENEMY_SIZE)
        
        self.velocity = random.randint(1, MAX_MINE_VELOCITY)
        
  
    
  
# trida reprezentujici me, tedy meho agenta        
class Me:
    def __init__(self):
        self.rect = pygame.Rect(10, 10, ME_SIZE, ME_SIZE)  
        self.default_position = (10, 10)
        self.alive = True
        self.won = False
        self.timealive = 0
        self.sequence = []
        self.fitness = 0
        self.dist = 0
        self.last_movement = None
        self.changes = 0
    
    
# třída reprezentující cíl = praporek    
class Flag:
    def __init__(self):
        self.rect = pygame.Rect(WIDTH - ME_SIZE, HEIGHT - ME_SIZE - 10, ME_SIZE, ME_SIZE)
        

# třída reprezentující nejlepšího jedince - hall of fame   
class Hof:
    def __init__(self):
        self.sequence = []
        
    
    
# -----------------------------------------------------------------------------    
# nastavení herního plánu    
#-----------------------------------------------------------------------------
    

# rozestavi miny v danem poctu num
def set_mines(num):
    l = []
    for i in range(num):
        m = Mine()
        l.append(m)
        
    return l
    

# inicializuje me v poctu num na start 
def set_mes(num):
    l = []
    for i in range(num):
        m = Me()
        l.append(m)
        
    return l

# zresetuje vsechny mes zpatky na start
def reset_mes(mes, pop):
    for i in range(len(pop)):
        me = mes[i]
        me.rect.x = 10
        me.rect.y = 10
        me.alive = True
        me.dist = 0
        me.won = False
        me.timealive = 0
        me.sequence = pop[i]
        me.fitness = 0



    

# -----------------------------------------------------------------------------    
# senzorické funkce 
# -----------------------------------------------------------------------------    

# distance between two object (Pythagoras)
def rect_distance(obj1, obj2):
    return math.sqrt( \
        (((obj1.rect.x + obj1.rect.width) // 2) - (obj2.rect.x + obj2.rect.width) // 2) ** 2 + \
        (((obj1.rect.y + obj1.rect.height) // 2) - (obj2.rect.y + obj2.rect.height) // 2) ** 2 \
    )

# distance between two objects (Manhattan)
def rect_manhattan_distance(obj1, obj2):
    return abs(((obj1.rect.x + obj1.rect.width) // 2) - ((obj2.rect.x + obj2.rect.width) // 2)) + \
           abs(((obj1.rect.y + obj1.rect.height) // 2) - ((obj2.rect.y + obj2.rect.height) // 2))

# center of a mine
def mine_center(mine):
    return ((mine.rect.x + mine.rect.width) // 2, ((mine.rect.y + mine.rect.height) // 2))

# distance between me and a mine (centers)
def mine_distance(me, mine):
    me_center = ((me.rect.x + me.rect.width) // 2, ((me.rect.y + me.rect.height) // 2))
    mine_cent = mine_center(mine)
    me_mine_distance = math.sqrt((me_center[0] - mine_cent[0]) ** 2 + (me_center[1] - mine_cent[1]) ** 2)
    mine_direction = (mine.dirx, mine.diry)
    return(me_mine_distance, mine_direction)

# checks for mines in my sight (3* my width) in a given direction 
def mine_in_sight(me, mine, direction):
    if direction == 1:
        x = me.rect.x
        y = max(me.rect.y - me.rect.height * 3, 0)
        width = me.rect.width
        height = me.rect.y - y
    elif direction == 2:
        x = me.rect.x
        y = me.rect.y - me.rect.height
        width = me.rect.width
        height = min(me.rect.height * 3, HEIGHT - me.rect.y)
    elif direction == 3:
        x = max(me.rect.x - me.rect.height * 3, 0)
        y = me.rect.y
        width = min(me.rect.x, me.rect.width * 3)
        height = me.rect.height
    elif direction == 4:
        x = me.rect.x + me.rect.width
        y = me.rect.y
        width = min(WIDTH - me.rect.x + me.rect.width, me.rect.width * 3)
        height = me.rect.height
    view = pygame.Rect(x, y, width, height)
    return view.colliderect(mine.rect)

def my_senzor(me, mines, flag):

    # two different distances calculations between me and the flag
    me_flag_distance = rect_distance(me, flag)

    # distance in either x and y direction
    me_flag_x_distance = abs(me.rect.x - flag.rect.x)
    me_flag_y_distance = abs(me.rect.y - flag.rect.y)

    # distance to the closest mine + its directions of movement
    me_mines_distances = [mine_distance(me, mine) for mine in mines] 
    closest_mine_distance, (closest_mine_xdir, closest_mine_ydir) = min(me_mines_distances, key=lambda x: x[0])
                                                                      
    # number of mines in corresponding directions
    n_mines_up = [mine_in_sight(me, mine, 1) for mine in mines].count(True)
    n_mines_down = [mine_in_sight(me, mine, 2) for mine in mines].count(True)
    n_mines_left = [mine_in_sight(me, mine, 3) for mine in mines].count(True)
    n_mines_right = [mine_in_sight(me, mine, 4) for mine in mines].count(True)


    return [
        me_flag_distance,
        me_flag_x_distance,
        me_flag_y_distance,
        closest_mine_distance,
        closest_mine_xdir,
        closest_mine_ydir,
        n_mines_up,
        n_mines_down,
        n_mines_left,
        n_mines_right
           ]



# ---------------------------------------------------------------------------
# funkce řešící pohyb agentů
# ----------------------------------------------------------------------------


# konstoluje kolizi 1 agenta s minama, pokud je kolize vraci True
def me_collision(me, mines):    
    for mine in mines:
        if me.rect.colliderect(mine.rect):
            #pygame.event.post(pygame.event.Event(ME_HIT))
            return True
    return False
            
            
# kolidujici agenti jsou zabiti, a jiz se nebudou vykreslovat
def mes_collision(mes, mines):
    for me in mes: 
        if me.alive and not me.won:
            if me_collision(me, mines):
                me.alive = False
            
            
# vraci True, pokud jsou vsichni mrtvi Dave            
def all_dead(mes):    
    for me in mes: 
        if me.alive:
            return False
    
    return True


# vrací True, pokud již nikdo nehraje - mes jsou mrtví nebo v cíli
def nobodys_playing(mes):
    for me in mes: 
        if me.alive and not me.won:
            return False
    
    return True


# rika, zda agent dosel do cile
def me_won(me, flag):
    if me.rect.colliderect(flag.rect):
        return True
    
    return False


# vrací počet živých mes
def alive_mes_num(mes):
    c = 0
    for me in mes:
        if me.alive:
            c += 1
    return c



# vrací počet mes co vyhráli
def won_mes_num(mes):
    c = 0
    for me in mes: 
        if me.won:
            c += 1
    return c

         
    
# resi pohyb miny        
def handle_mine_movement(mine):
        
    if mine.dirx == -1 and mine.rect.x - mine.velocity < 0:
        mine.dirx = 1
       
    if mine.dirx == 1  and mine.rect.x + mine.rect.width + mine.velocity > WIDTH:
        mine.dirx = -1

    if mine.diry == -1 and mine.rect.y - mine.velocity < 0:
        mine.diry = 1
    
    if mine.diry == 1  and mine.rect.y + mine.rect.height + mine.velocity > HEIGHT:
        mine.diry = -1
         
    mine.rect.x += mine.dirx * mine.velocity
    mine.rect.y += mine.diry * mine.velocity


# resi pohyb min
def handle_mines_movement(mines):
    for mine in mines:
        handle_mine_movement(mine)


#----------------------------------------------------------------------------
# vykreslovací funkce 
#----------------------------------------------------------------------------


# vykresleni okna
def draw_window(mes, mines, flag, level, generation, timer):
    WIN.blit(SEA, (0, 0))   
    
    t = LEVEL_FONT.render("level: " + str(level), 1, WHITE)   
    WIN.blit(t, (10  , HEIGHT - 30))
    
    t = LEVEL_FONT.render("generation: " + str(generation), 1, WHITE)   
    WIN.blit(t, (150  , HEIGHT - 30))
    
    t = LEVEL_FONT.render("alive: " + str(alive_mes_num(mes)), 1, WHITE)   
    WIN.blit(t, (350  , HEIGHT - 30))
    
    t = LEVEL_FONT.render("won: " + str(won_mes_num(mes)), 1, WHITE)   
    WIN.blit(t, (500  , HEIGHT - 30))
    
    t = LEVEL_FONT.render("timer: " + str(timer), 1, WHITE)   
    WIN.blit(t, (650  , HEIGHT - 30))
    
    
    
    
    

    WIN.blit(FLAG, (flag.rect.x, flag.rect.y))    
         
    # vykresleni min
    for mine in mines:
        WIN.blit(ENEMY, (mine.rect.x, mine.rect.y))
        
    # vykresleni me
    for me in mes: 
        if me.alive:
            WIN.blit(ME, (me.rect.x, me.rect.y))
        
    pygame.display.update()



def draw_text(text):
    t = BOOM_FONT.render(text, 1, WHITE)   
    WIN.blit(t, (WIDTH // 2  , HEIGHT // 2))     
    
    pygame.display.update()
    pygame.time.delay(1000)







#-----------------------------------------------------------------------------
# funkce reprezentující neuronovou síť, pro inp vstup a zadané váhy wei, vydá
# čtveřici výstupů pro nahoru, dolu, doleva, doprava   
#----------------------------------------------------------------------------

# closure for creating neural network function
# layers - tuple with number of neurons in corresponding i-th layer (including input and output layers)
def create_nn_function(layers):

    # input - array of inputs of the NN input ==> first layer
    # weights - array of weights as a genom from evolution algorithm
    def nn_function(input, weights):
        
        # checking if the length of the genom "fits" into the NN structure
        assert len(weights) == sum(layers[i] * layers[i + 1] for i in range(len(layers) - 1)), "The structure of genom doesn't fit the NN layers!"
        
        weights_matrices = []
    
        # reshaping the weights genom into weights matrices
        for i in range(len(layers) - 1):
            index = layers[i] * layers[i + 1]
            weight_array = np.array(weights[:index])
            weight_matrix = np.reshape(weight_array, (layers[i], layers[i + 1]))
            weights_matrices.append(weight_matrix)
            weights = weights[index:]
        
        current_layer = input
        
        # performing multiple matrix multiplication
        for weight_matrix in weights_matrices:
            current_layer = current_layer @ weight_matrix
            
            # applying ReLU activation function with bias 0 - changing all negative values to 0
            current_layer[current_layer < 0] = 0
            
        return current_layer

    return nn_function


# naviguje jedince pomocí neuronové sítě a jeho vlastní sekvence v něm schované
def nn_navigate_me(me, inp, nn_function):
       
    movement = None
    
    # calling the neural network function given data from sensors and the current genom
    outputs = nn_function(inp, me.sequence)

    ind = np.argmax(outputs)
    if ind != me.last_movement:
        me.changes += 1
        me.last_movement = ind
    
    # nahoru, pokud není zeď
    if ind == 0 and me.rect.y - ME_VELOCITY > 0:
        me.rect.y -= ME_VELOCITY
        me.dist += ME_VELOCITY
    
    # dolu, pokud není zeď
    if ind == 1 and me.rect.y + me.rect.height + ME_VELOCITY < HEIGHT:
        me.rect.y += ME_VELOCITY  
        me.dist += ME_VELOCITY
    
    # doleva, pokud není zeď
    if ind == 2 and me.rect.x - ME_VELOCITY > 0:
        me.rect.x -= ME_VELOCITY
        me.dist += ME_VELOCITY
        
    # doprava, pokud není zeď    
    if ind == 3 and me.rect.x + me.rect.width + ME_VELOCITY < WIDTH:
        me.rect.x += ME_VELOCITY
        me.dist += ME_VELOCITY
    
    
        

# updatuje, zda me vyhrali 
def check_mes_won(mes, flag):
    for me in mes: 
        if me.alive and not me.won:
            if me_won(me, flag):
                me.won = True
    


# resi pohyb mes
def handle_mes_movement(mes, mines, flag, nn):
    
    for me in mes:

        if me.alive and not me.won:
            
            inp = my_senzor(me, mines, flag)  
            
            nn_navigate_me(me, inp, nn)



# updatuje timery jedinců
def update_mes_timers(mes, timer):
    for me in mes:
        if me.alive and not me.won:
            me.timealive = timer



# ---------------------------------------------------------------------------
# fitness funkce výpočty jednotlivců
#----------------------------------------------------------------------------

# function designed to penalize individual if he moves further away from the mine, give him 0 evaluation, if he moves only in one direction
# and rewarding him when moving towards the flag
def mover_func(me, flag):
    default_distance_x = abs(me.default_position[0] - flag.rect.x)
    default_distance_y = abs(me.default_position[1] - flag.rect.y)
    current_distance_x = abs(me.rect.x - flag.rect.x)
    current_distance_y = abs(me.rect.y - flag.rect.y)
    difference_x = abs(default_distance_x - current_distance_x)
    difference_y = abs(default_distance_y - current_distance_y)
    product = difference_x * difference_y
    if not (current_distance_x < default_distance_x and current_distance_y < default_distance_y):
        product *= -1
    return product



# funkce pro výpočet fitness všech jedinců
def handle_mes_fitnesses(mes, flag): 
    
      
    for me in mes:
        # calculating optimal factor
        default_distance_x = abs(me.default_position[0] - flag.rect.x)
        default_distance_y = abs(me.default_position[1] - flag.rect.y)
        optimal_factor = default_distance_x * default_distance_y

        # rewarding the individual for winning
        fitness = me.won * optimal_factor

        # rewarding for distance covered
        fitness += me.dist * 3

        # rewarding based on mover_func
        fitness += mover_func(me, flag)
        
        me.fitness = fitness
    
    

# uloží do hof jedince s nejlepší fitness
def update_hof(hof, mes):
    l = [me.fitness for me in mes]
    ind = np.argmax(l)
    hof.sequence = mes[ind].sequence.copy()
    

# ----------------------------------------------------------------------------
# main loop 
# ----------------------------------------------------------------------------

def main():
    
    # creating an outline of the neural network. Weights are set later on.
    # 9 inputs, *hidden layers, 4 outputs
    NN_layout = [10, 6, 6, 4]
    NN = create_nn_function(NN_layout)
    n_weights = sum(NN_layout[i] * NN_layout[i + 1] for i in range(len(NN_layout) - 1))
    
    
    # =====================================================================
    VELIKOST_POPULACE = 50
    EVO_STEPS = 20  # pocet kroku evoluce
    DELKA_JEDINCE = n_weights   # záleží na počtu vah a prahů u neuronů !!!!!
    NGEN = 30        # počet generací
    CXPB = 0.6          # pravděpodobnost crossoveru na páru
    MUTPB = 0.2      # pravděpodobnost mutace
    
    SIMSTEPS = 500
    
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)
    
    toolbox = base.Toolbox()

    toolbox.register("attr_rand", random.random)
    toolbox.register("individual", tools.initRepeat, creator.Individual, toolbox.attr_rand, DELKA_JEDINCE)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    def mutRandom(individual, indpb):
        for i in range(len(individual)):
            if random.random() < indpb:
                individual[i] = random.random()
        return individual,

    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", mutRandom, indpb=0.05)
    toolbox.register("select", tools.selRoulette)
    toolbox.register("selectbest", tools.selBest)
    
    pop = toolbox.population(n=VELIKOST_POPULACE)
        
    # =====================================================================
    
    clock = pygame.time.Clock()

    
    
    # =====================================================================
    # testování hraním a z toho odvození fitness 
   
    
    mines = []
    mes = set_mes(VELIKOST_POPULACE)    
    flag = Flag()
    
    hof = Hof()
    
    
    run = True

    level = 5  # <--- ZDE nastavení obtížnosti počtu min !!!!!
    generation = 0
    
    evolving = True
    evolving2 = False
    timer = 0
    
    while run:  
        
        clock.tick(FPS)
        
               
        # pokud evolvujeme pripravime na dalsi sadu testovani - zrestartujeme scenu
        if evolving:           
            timer = 0
            generation += 1
            reset_mes(mes, pop) # přiřadí sekvence z populace jedincům a dá je na start !!!!
            mines = set_mines(level) 
            evolving = False
            
        timer += 1    
            
        check_mes_won(mes, flag)
        handle_mes_movement(mes, mines, flag, NN)
        
        
        handle_mines_movement(mines)
        
        mes_collision(mes, mines)
        
        if all_dead(mes):
            evolving = True
            #draw_text("Boom !!!")"""

            
        update_mes_timers(mes, timer)        
        draw_window(mes, mines, flag, level, generation, timer)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
    

        
        
        
        
        # ---------------------------------------------------------------------
        # <---- ZDE druhá část evoluce po simulaci  !!!!!
        
        # druhá část evoluce po simulaci, když všichni dohrají, simulace končí 1000 krocích

        if timer >= SIMSTEPS or nobodys_playing(mes): 
            
            # přepočítání fitness funkcí, dle dat uložených v jedinci
            handle_mes_fitnesses(mes, flag)   # <--------- ZDE funkce výpočtu fitness !!!!
            
            update_hof(hof, mes)
            
            
            #plot fitnes funkcí
            #ff = [me.fitness for me in mes]
            
            #print(ff)
            
            # přiřazení fitnessů z jedinců do populace
            # každý me si drží svou fitness, a každý me odpovídá jednomu jedinci v populaci
            for i in range(len(pop)):
                ind = pop[i]
                me = mes[i]
                ind.fitness.values = (me.fitness, )
            
            
            # selekce a genetické operace
            offspring = toolbox.select(pop, len(pop))
            offspring = list(map(toolbox.clone, offspring))
            

            
            
            

            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:
                    toolbox.mate(child1, child2)

            for mutant in offspring:
                if random.random() < MUTPB:
                    toolbox.mutate(mutant)  
            
            pop[:] = offspring
            
            
            evolving = True
                   
        
    # po vyskočení z cyklu aplikace vytiskne DNA sekvecni jedince s nejlepší fitness
    # a ukončí se
    
    pygame.quit()    


if __name__ == "__main__":
    main()