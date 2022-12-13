import functools
import math
import random

import pygame
import os
import config
import itertools
from queue import PriorityQueue

class BaseSprite(pygame.sprite.Sprite):
    images = dict()

    def __init__(self, x, y, file_name, transparent_color=None, wid=config.SPRITE_SIZE, hei=config.SPRITE_SIZE):
        pygame.sprite.Sprite.__init__(self)
        if file_name in BaseSprite.images:
            self.image = BaseSprite.images[file_name]
        else:
            self.image = pygame.image.load(os.path.join(config.IMG_FOLDER, file_name)).convert()
            self.image = pygame.transform.scale(self.image, (wid, hei))
            BaseSprite.images[file_name] = self.image
        # making the image transparent (if needed)
        if transparent_color:
            self.image.set_colorkey(transparent_color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)


class Surface(BaseSprite):
    def __init__(self):
        super(Surface, self).__init__(0, 0, 'terrain.png', None, config.WIDTH, config.HEIGHT)


class Coin(BaseSprite):
    def __init__(self, x, y, ident):
        self.ident = ident
        super(Coin, self).__init__(x, y, 'coin.png', config.DARK_GREEN)

    def get_ident(self):
        return self.ident

    def position(self):
        return self.rect.x, self.rect.y

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class CollectedCoin(BaseSprite):
    def __init__(self, coin):
        self.ident = coin.ident
        super(CollectedCoin, self).__init__(coin.rect.x, coin.rect.y, 'collected_coin.png', config.DARK_GREEN)

    def draw(self, screen):
        text = config.COIN_FONT.render(f'{self.ident}', True, config.RED)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)


class Agent(BaseSprite):
    def __init__(self, x, y, file_name):
        super(Agent, self).__init__(x, y, file_name, config.DARK_GREEN)
        self.x = self.rect.x
        self.y = self.rect.y
        self.step = None
        self.travelling = False
        self.destinationX = 0
        self.destinationY = 0

    def set_destination(self, x, y):
        self.destinationX = x
        self.destinationY = y
        self.step = [self.destinationX - self.x, self.destinationY - self.y]
        magnitude = math.sqrt(self.step[0] ** 2 + self.step[1] ** 2)
        self.step[0] /= magnitude
        self.step[1] /= magnitude
        self.step[0] *= config.TRAVEL_SPEED
        self.step[1] *= config.TRAVEL_SPEED
        self.travelling = True

    def move_one_step(self):
        if not self.travelling:
            return
        self.x += self.step[0]
        self.y += self.step[1]
        self.rect.x = self.x
        self.rect.y = self.y
        if abs(self.x - self.destinationX) < abs(self.step[0]) and abs(self.y - self.destinationY) < abs(self.step[1]):
            self.rect.x = self.destinationX
            self.rect.y = self.destinationY
            self.x = self.destinationX
            self.y = self.destinationY
            self.travelling = False

    def is_travelling(self):
        return self.travelling

    def place_to(self, position):
        self.x = self.destinationX = self.rect.x = position[0]
        self.y = self.destinationX = self.rect.y = position[1]

    # coin_distance - cost matrix
    # return value - list of coin identifiers (containing 0 as first and last element, as well)
    def get_agent_path(self, coin_distance):
        pass


class ExampleAgent(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = [i for i in range(1, len(coin_distance))]
        random.shuffle(path)
        return [0] + path + [0]


class Aki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        path = [0]
        nextCoinIndex = 0

        while True:
            # if all coins are collected dfs is completed
            if len(path) == len(coin_distance):
                break
            currentRow = coin_distance[nextCoinIndex]
            minValue = min(x for x in currentRow if x != 0 and currentRow.index(x) not in path)
            nextCoinIndex = currentRow.index(minValue)
            path.append(nextCoinIndex)

        return path + [0]


class Jocke(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    def get_agent_path(self, coin_distance):
        allCoinsIndex = [i for i in range(1, len(coin_distance))]
        allPaths = list(itertools.permutations(allCoinsIndex))
        bestPath = []
        bestPathCost = float('inf')

        for path in allPaths:
            currentPathCost = 0
            currentPathCost += coin_distance[0][path[0]]
            currentPathCost += coin_distance[path[len(coin_distance) - 2]][0]
            for i in range(0, len(coin_distance) - 2):
                currentPathCost += coin_distance[path[i]][path[i+1]]
            if currentPathCost < bestPathCost:
                bestPathCost = currentPathCost
                bestPath = path

        # bestPath is currently tuple so need to be converted to array
        return [0] + list(bestPath) + [0]


@functools.total_ordering
class Pq_Element_Uki(object):
    def __init__(self, value, coin_distance):
        self.val = value
        self.coin_distance = coin_distance

    def __lt__(self, other):

        if self.val["cost"] < other.val["cost"]:
            return True

        elif self.val["cost"] == other.val["cost"]:
            if len(self.val["path"]) > len(other.val["path"]):
                return True
            elif len(self.val["path"]) == len(other.val["path"]):
                if self.val["path"][len(self.val["path"]) - 1] < other.val["path"][len(other.val["path"]) - 1]:
                    return True

        return False

    def getValue(self):
        return self.val

class Uki(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    @staticmethod
    def getPathCost(pathHash):
        return pathHash["cost"]


    def get_agent_path(self, coin_distance):
        bestPath = []
        #partialPaths = []

        partialPaths = PriorityQueue()

        #partialPaths.append({"path": [0], "cost": 0})

        partialPaths.put(Pq_Element_Uki({"path": [0], "cost": 0}, coin_distance))

        while True:
            # when 2 partial paths have same cost take path which leads to coin with lower identificator

            #partialPaths.sort(key=Uki.getPathCost)
            #currentCost = partialPaths[0].get("cost")
            #currentElement = partialPaths[0]
            #currentCost = float('inf')
            #currentElement = {}

            #index = 0

            # for i in range(0, len(partialPaths)):
            #     if partialPaths[i].get("cost") < currentCost:
            #         currentElement = partialPaths[i]
            #         currentCost = partialPaths[i].get("cost")
            #         index = i
            #     elif partialPaths[i].get("cost") == currentCost:
            #         if len(partialPaths[i].get("path")) > len(currentElement.get("path")):
            #             currentElement = partialPaths[i]
            #             currentCost = partialPaths[i].get("cost")
            #             index = i
            #         elif len(partialPaths[i].get("path")) == len(currentElement.get("path")):
            #             #if partialPaths[i].get("path")[len(partialPaths[i].get("path")) - 2] < currentElement.get("path")[len(currentElement.get("path")) - 2]:
            #             if partialPaths[i].get("path")[len(partialPaths[i].get("path")) - 1] < currentElement.get("path")[len(currentElement.get("path")) - 1]:
            #             #if partialPaths[i].get("path")[1] < currentElement.get("path")[1]:
            #                 currentElement = partialPaths[i]
            #                 index = i
            #                 currentCost = partialPaths[i].get("cost")


            # currentElement = partialPaths.pop(index)
            currentElement = (partialPaths.get()).getValue()

            currentPath = currentElement.get("path")
            currentCost = currentElement.get("cost")
            currentRow = coin_distance[currentPath[len(currentPath) - 1]]


            if len(currentPath) == (len(coin_distance) + 1):
                bestPath = currentPath
                break

            if len(currentPath) == len(coin_distance):
                #partialPaths.append({"path": currentPath + [0], "cost": currentCost + currentRow[0]})
                partialPaths.put(Pq_Element_Uki({"path": currentPath + [0], "cost": currentCost + currentRow[0]}, coin_distance))
                continue


            for i in range(0, len(currentRow)):
                if currentRow[i] != 0 and i not in currentPath:
                    #partialPaths.append({"path": currentPath + [i], "cost": currentCost + currentRow[i]})
                    partialPaths.put(Pq_Element_Uki({"path": currentPath + [i], "cost": currentCost + currentRow[i]},coin_distance))


        return bestPath




functools.total_ordering
class Pq_Element_Micko(object):
    def __init__(self, value, coin_distance):
        self.val = value
        self.coin_distance = coin_distance

    def __lt__(self, other):
        if (self.val["cost"] + self.val["heuristic"]) < (other.val["cost"] + other.val["heuristic"]):
            return True

        elif self.val["cost"] == other.val["cost"]:
            if len(self.val["path"]) > len(other.val["path"]):
                return True
            elif len(self.val["path"]) == len(other.val["path"]):
                if self.val["path"][len(self.val["path"]) - 1] < other.val["path"][len(other.val["path"]) - 1]:
                    return True

        return False

    def getValue(self):
        return self.val


class Micko(Agent):
    def __init__(self, x, y, file_name):
        super().__init__(x, y, file_name)

    @staticmethod
    def getPathCost(pathHash):
        return pathHash["cost"] + pathHash["heuristic"]

    @staticmethod
    def isCyclic(node1, node2, allNodesSet):
        flag = False
        for i in range(0, len(allNodesSet[node1])):
            for j in range(0, len(allNodesSet[node2])):
                if allNodesSet[node1][i] == allNodesSet[node2][j]:
                    flag = True
        return flag

    @staticmethod
    def sortPaths(pathHash):
        return pathHash["cost"]

    @staticmethod
    def getcurrentHeuristic(currentPath, coin_distance):
        # heuristic based on minimal spanning tree

        pathToIncludeInMst = [i for i in range(0, len(coin_distance))]
        heuristicCost = 0

        if len(currentPath) == 1:

            visitedNodes = []

            allPathsWithCost = []
            for i in range(0, len(coin_distance)):
                for j in range(i + 1, len(coin_distance)):
                    if i in pathToIncludeInMst and j in pathToIncludeInMst:
                        allPathsWithCost.append({"path": [i, j], "cost": coin_distance[i][j]})

            allPathsWithCost.sort(key=Micko.sortPaths)

            allNodesSet = [[] for i in range(0, len(coin_distance))]
            number = 0

            while True:
                if number == (len(pathToIncludeInMst) - 1):
                    break

                currentPathWithCost = allPathsWithCost.pop(0)
                nodes = currentPathWithCost.get("path")
                cost = currentPathWithCost.get("cost")

                if not(Micko.isCyclic(nodes[0], nodes[1], allNodesSet)):
                    number += 1
                    heuristicCost += cost
                    if not(nodes[0] in visitedNodes):
                        allNodesSet[nodes[0]].append(nodes[1])
                        visitedNodes.append(nodes[0])
                    if not(nodes[1] in visitedNodes):
                        allNodesSet[nodes[1]].append(nodes[0])
                        visitedNodes.append(nodes[1])

            return heuristicCost

        elif len(currentPath) == len(coin_distance):
            return heuristicCost
        else:

            set_difference = set(pathToIncludeInMst) - set(currentPath)
            list_difference = list(set_difference)
            pathToIncludeInMst = [0] + list_difference

            visitedNodes = []

            allPathsWithCost = []
            for i in range(0, len(coin_distance)):
                for j in range(i + 1, len(coin_distance)):
                    if i in pathToIncludeInMst and j in pathToIncludeInMst:
                        allPathsWithCost.append({"path": [i, j], "cost": coin_distance[i][j]})

            allPathsWithCost.sort(key=Micko.sortPaths)

            allNodesSet = [[] for i in range(0, len(coin_distance))]
            number = 0

            while True:
                if number == (len(pathToIncludeInMst) - 1):
                    break

                currentPathWithCost = allPathsWithCost.pop(0)
                nodes = currentPathWithCost.get("path")
                cost = currentPathWithCost.get("cost")

                if not (Micko.isCyclic(nodes[0], nodes[1], allNodesSet)):
                    number += 1
                    heuristicCost += cost
                    if not (nodes[0] in visitedNodes):
                        allNodesSet[nodes[0]].append(nodes[1])
                        visitedNodes.append(nodes[0])
                    if not (nodes[1] in visitedNodes):
                        allNodesSet[nodes[1]].append(nodes[0])
                        visitedNodes.append(nodes[1])

            return heuristicCost

    def get_agent_path(self, coin_distance):
        bestPath = []
        #partialPaths = []
        partialPaths = PriorityQueue()


        firstHeuristic = Micko.getcurrentHeuristic([0], coin_distance)
        #partialPaths.append({"path": [0], "cost": 0, "heuristic": firstHeuristic})
        partialPaths.put(Pq_Element_Micko({"path": [0], "cost": 0, "heuristic": firstHeuristic}, coin_distance))

        while True:
            # when 2 partial paths have same cost take path which leads to coin with lower identificator

            #partialPaths.sort(key=Micko.getPathCost)
            #currentCost = partialPaths[0].get("cost")
            #currentHeuristic = partialPaths[0].get("heuristic")
            #currentElement = partialPaths[0]
            #index = 0

            # for i in range(1, len(partialPaths)):
            #     if (partialPaths[i].get("cost") + partialPaths[i].get("heuristic")) == (currentCost + currentHeuristic):
            #         if len(partialPaths[i].get("path")) > len(currentElement.get("path")):
            #             currentElement = partialPaths[i]
            #             index = i
            #         elif len(partialPaths[i].get("path")) == len(currentElement.get("path")):
            #             #if partialPaths[i].get("path")[len(partialPaths[i].get("path")) - 2] < currentElement.get("path")[len(currentElement.get("path")) - 2]:
            #             if partialPaths[i].get("path")[len(partialPaths[i].get("path")) - 1] < currentElement.get("path")[len(currentElement.get("path")) - 1]:
            #             #if partialPaths[i].get("path")[1] < currentElement.get("path")[1]:
            #                 currentElement = partialPaths[i]
            #                 index = i

            #currentElement = partialPaths.pop(index)
            currentElement = (partialPaths.get()).getValue()

            currentPath = currentElement.get("path")
            currentCost = currentElement.get("cost")
            currentHeuristic= currentElement.get("heuristic")
            currentRow = coin_distance[currentPath[len(currentPath) - 1]]

            newHeuristic = Micko.getcurrentHeuristic(currentPath, coin_distance)


            if len(currentPath) == (len(coin_distance) + 1):
                bestPath = currentPath
                break

            if len(currentPath) == len(coin_distance):
                #print(currentRow[0])
                #partialPaths.append({"path": currentPath + [0], "cost": currentCost + currentRow[0], "heuristic": newHeuristic})
                partialPaths.put(Pq_Element_Micko({"path": currentPath + [0], "cost": currentCost + currentRow[0], "heuristic": newHeuristic}, coin_distance))
                continue

            for i in range(0, len(currentRow)):
                if currentRow[i] != 0 and i not in currentPath:
                    #partialPaths.append({"path": currentPath + [i], "cost": currentCost + currentRow[i], "heuristic": newHeuristic})
                    partialPaths.put(Pq_Element_Micko({"path": currentPath + [i], "cost": currentCost + currentRow[i], "heuristic": newHeuristic},coin_distance))

        return bestPath