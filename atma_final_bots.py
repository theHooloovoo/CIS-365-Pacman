"""
atma_final_bots.py

A reflex agent that plays Pacman.
Adapted from the provided vidar.py agent.

By Eric Blanchet, Andy Hudson, Zack Poorman, Chesten VanPelt
For CIS 365
"""
from __future__ import print_function
from captureAgents import CaptureAgent
import math
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint

#Creates a team; both team members use the same AI that varies based on their index
def createTeam(firstIndex, secondIndex, isRed,
               first = 'Atma', second = 'Atma'):
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

#Generic class for reflex agents; main behavior is to return the next action for the game
class ReflexCaptureAgent(CaptureAgent):
  #Records start position, calls parent method
  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

  def findPathAndCost(self, gameState, agentIndex, travelTo, maxCost, checkForDeadend):
    openNodes = [Node(gameState, None, None, 0, 0)]
    closedNodes = []

    #filter through nodes
    while(len(openNodes) != 0):
      nodeAndIndex = self.findLowestTotalCostNodeAndPop(openNodes)
      currentNode = nodeAndIndex[0]
      del openNodes[nodeAndIndex[1]]

      #for the lowest-cost node, get all legal actions
      legalActions = currentNode.state.getLegalActions(agentIndex)  

      successors = []
      for action in legalActions:
        successor = currentNode.state.generateSuccessor(agentIndex, action)
        #calculate all costs
        heuristics = self.calculateHeuristicCosts(successor, successor.getAgentPosition(agentIndex), travelTo)

        #do not use successor if it exceeds max cost
        if(currentNode.generalCost + heuristics[1] > maxCost):
          continue

        #use successor as Node
        successors.append(Node(
          successor,
          currentNode,
          action,
          currentNode.generalCost + 1 + heuristics[0],
          currentNode.generalCost + 1 + heuristics[1]
          ))

      #for all valid successors
      for s in successors:
        #if successor position matches travelTo position
        if(self.agentPositionMatchesDestination(s, travelTo)):
          #use this successor to generate and return a path/cost
          pathAndCost = self.generatePathOfActions(s)
          return pathAndCost
        #if successor should be opened, append it to the list (and the main loop will revisit it)
        if(self.nodeShouldBeOpened(s, openNodes, closedNodes)):
          openNodes.append(s)
      closedNodes.append(currentNode)
    return None

  #finds the lowest total cost node in the given list and returns it and its index in the list
  def findLowestTotalCostNodeAndPop(self, openList):
    lowestNode = openList[0]
    lowIndex = 0

    i = 0
    for o in openList:
      if(o.totalCost <= lowestNode.totalCost):
        lowestNode = o
        lowIndex = i
      i += 1

    return (lowestNode, lowIndex)

  #checks if agent position matches given position
  def agentPositionMatchesDestination(self, node, travelTo):
    agentX, agentY = node.state.getAgentPosition(self.index)
    if(agentX == int(travelTo[0]) and int(agentY) == int(travelTo[1])):
      return True
    return False

  #node should only be opened IF cost is LESS than all open/closed nodes AND node's position DOESN'T match any of them
  def nodeShouldBeOpened(self, node, openList, closedList):
    for o in openList:
      if(node.state.getAgentPosition(self.index) == o.state.getAgentPosition(self.index) and node.totalCost > o.totalCost):
        return False

    for c in closedList:
      if (node.state.getAgentPosition(self.index) == c.state.getAgentPosition(
              self.index) and node.totalCost > c.totalCost):
        return False

    return True

  #recursion; go through parent nodes and log actions; returns action list and node's cost
  def generatePathOfActions(self, node):
    totalCost = node.generalCost
    actionList = []
    currentNode = node
    while(currentNode.parent != None):
      actionList.insert(0, currentNode.action)
      currentNode = currentNode.parent

    return (actionList, totalCost)

  #calculates/returns (enemy cost, enemy + distance + teammate proximity cost)
  def calculateHeuristicCosts(self, gameState, travelFrom, travelTo):
    agentPosition = gameState.getAgentPosition(self.index)
    enemyCost = 0
    teamateProximityCost = 0
    closestEnemy = 999999

    distanceCost = self.getMazeDistance(travelFrom, travelTo)

    agents = self.getOpponents(gameState)
    for a in agents:
      state = gameState.getAgentState(a)
      if(state.scaredTimer == 0 and (not state.isPacman)):
        enemyPosition = gameState.getAgentPosition(a)
        proximity = 999999

        if(enemyPosition != None):
          proximity = self.getMazeDistance(agentPosition, enemyPosition)

        if(proximity < closestEnemy):
          closestEnemy = proximity

  #exponential growth for enemy distance -- required
    if(closestEnemy == 4):
      enemyCost = 3
    elif(closestEnemy == 3):
      enemyCost = 7
    elif(closestEnemy == 2):
      enemyCost = 15
    elif(closestEnemy == 1):
      enemyCost = 30

    team = self.getTeam(gameState)
    for t in team:
      if(t != self.index and self.getMazeDistance(agentPosition, gameState.getAgentPosition(t)) < 4):
        teamateProximityCost = 5

    return (enemyCost, distanceCost + enemyCost + teamateProximityCost)

  #generates a future gameState with the given action completed
  def getSuccessor(self, gameState, action):
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  #get path to nearest space on my side
  def getLowestCostRetreatPath(self, gameState):
    retreat = self.getRetreatCells(gameState)

    lowestCost = 125
    lowestPath = None

    for r in retreat:
      path = self.findPathAndCost(gameState, self.index, r, lowestCost, False)
      if (path != None and path[1] < lowestCost):
        lowestPath = path[0]
        lowestCost = path[1]

    return lowestPath

  #get path to predefined guard position
  def getLowestCostGuardPath(self, gameState):
    guard = self.guardPos
    path = self.findPathAndCost(gameState, self.index, guard, 999, False)
    return path[0]

  def getLowestCostFoodPath(self, gameState):
    #get food on agent's designated half of board
    board_height = 16
    food = self.getFood(gameState).asList()
    for f in food:
      if f[1] <= board_height / 2 and self.indexSmaller:
        food.remove(f)
      elif f[1] > board_height / 2 and not self.indexSmaller:
        food.remove(f)

    lowestCost = 60
    lowestPath = None

    while len(food) > 0:

      #find the closest food
      closestDistance = 99999
      closestIndex = 0
      i = 0
      """
    this was to avoid getting stuck in loops -- usually not necessary
    
      if self.hunger > 45:
        if self.hungerFood == None:
          self.hungerFood = food.pop(random.randrange(len(food) - 1))
        path = self.findPathAndCost(gameState, self.index, self.hungerFood, lowestCost * 3, True)
        return path[0]
      """

      for f in food:
        currentDistance = self.getMazeDistance(gameState.getAgentPosition(self.index), f)
        if(currentDistance < closestDistance):
          closestDistance = currentDistance
          closestIndex = i
        i += 1
      currentFood = food.pop(closestIndex)

      #for all food, find the lowest-cost path
      path = self.findPathAndCost(gameState, self.index, currentFood, lowestCost, True)
      if(path != None and path[1] < lowestCost):
        lowestPath = path[0]
        lowestCost = path[1]

    return lowestPath
  
  #returns closest cells that are safe from opponent
  def getRetreatCells(self, gameState):
    homeSquares = []
    wallsMatrix = gameState.data.layout.walls
    wallsList = wallsMatrix.asList()
    layoutX = wallsMatrix.width
    redX = (layoutX - 1) / 2
    blueX = (int)(math.ceil((float)(layoutX - 1) / 2))

    layoutY = wallsMatrix.height - 1

    if (gameState.isOnRedTeam(self.index)):
      for y in range(1, layoutY - 1):
        if ((redX, y) not in wallsList):
          homeSquares.append((redX, y))
    else:
      for y in range(1, layoutY - 1):
        if ((blueX, y) not in wallsList):
          homeSquares.append((blueX, y))

    return homeSquares

  #determines retreat based on agent state, opponent distance/scared state
  def shouldRetreat(self, gameState):
    opponents = self.getOpponents(gameState)
    for o in opponents:
      position = gameState.getAgentPosition(o)
      if(position != None and self.getMazeDistance(position, gameState.getAgentPosition(self.index)) <= 4
              and gameState.getAgentState(o).scaredTimer == 0) and gameState.getAgentState(self.index).isPacman:
        return True

"""
Extension of ReflexCaptureAgent.

Has three unique features:
-future path generation via vidar.py implementation
-half-board behavior: guard positions, food are both split between agents
-guard behavior: decides whether to play offense/defense
"""
class Atma(ReflexCaptureAgent):
  def registerInitialState(self, gameState):
    #call parent method
    ReflexCaptureAgent.registerInitialState(self, gameState)
    #get all teammate indices
    self.teammates = self.getTeam(gameState)
    #get agent index is the smaller of all teammates
    self.indexSmaller = (self.teammates.index(self.index) == 0)

    """
    These lines were for infinite loop protection
    
    self.hunger = 0
    self.hungerFood = None
    self.previousCarrying = 0

    These lines were testing to see if caching all maze distances would make getMazePosition() act differently

    #cache all maze distances
    nextPt = (0,0)
    walls = gameState.getWalls().asList()
    while(nextPt != (15,15)):
      if (nextPt) not in walls:
        for c in range(nextPt[0],15):
          for r in range(nextPt[1],15):
            if (c,r) not in walls:
              self.getMazeDistance(nextPt,(c,r))
      if nextPt[0] == 15:
        nextPt = (0, nextPt[1] + 1)
      else:
        nextPt = (nextPt[0] + 1, nextPt[1])
    """

    #whether to play defense
    self.defense = False
    # set defensive positions (for default map -- if map is changed, these can be calculated instead)
    self.guardPos = None
    if self.indexSmaller:
      if self.red:
        self.guardPos = (12, 11)  # c, r
      else:
        self.guardPos = (18, 11)
    else:
      if self.red:
        self.guardPos = (13, 4)  # c, r
      else:
        self.guardPos = (19, 4)

  def chooseAction(self, gameState):
    opponents = self.getOpponents(gameState)
    capsule = self.getCapsulesYouAreDefending(gameState)
    score = self.getScore(gameState)
    currentState = gameState.getAgentState(self.index)
    currentPos = currentState.getPosition()

    carrying = 0
    for a in self.teammates:
      carrying += gameState.getAgentState(a).numCarrying
    myFoodCount = (len(self.getFood(gameState).asList()) <= 2)

    self.defense = (((self.red and score + carrying > 0) or (
              not self.red and -score - carrying < 0)) and gameState.getAgentState(self.index).scaredTimer < 10) or myFoodCount

    if self.defense:
      #head for enemy if they are pacmen, then guard position
      """
      "agent vision" -- this was difficult to figure out
      
      print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")
      print("INDEX: "+str(self.index))
      for o in opponents:
        oppnState = gameState.getAgentState(o)
        oppnPos = oppnState.getPosition()
        if oppnState != None and oppnPos != None:
          nextDist = self.getMazeDistance(currentPos, oppnPos)
          print("Opponent "+str(o)+" at "+str(oppnPos))
          print("distance is "+str(nextDist))
        else:
          print("Opponent " + str(o) + " OOB")
      """

      #find nearest opponent (if possible)
      closestOpponent = None
      closestDist = 999
      for o in opponents:
        oppnState = gameState.getAgentState(o)
        oppnPos = oppnState.getPosition()
        if oppnState != None and oppnPos != None:
          nextDist = self.getMazeDistance(currentPos, oppnPos)
          if nextDist < closestDist:
            closestDist = nextDist
            closestOpponent = o

      #if there's a capsule, defend it
      """
      Didn't end up being necessary
      
      if len(capsule) > 0 and not self.indexSmaller:
        guard = capsule[0]
      else:
        guard = self.guardPos
      """

      #if there's a nearest opponent, hunt them down
      if closestOpponent != None and gameState.getAgentState(closestOpponent).isPacman and \
              (self.getMazeDistance(currentPos, self.guardPos) < 5):
        oppnPos = gameState.getAgentState(closestOpponent).getPosition()
        if oppnPos != None:
          enemyPath = self.findPathAndCost(gameState, self.index, oppnPos, 9999, False)
          if enemyPath != None:
            return enemyPath[0][0]

      guardPath = self.getLowestCostGuardPath(gameState)
      if guardPath != None:
        return guardPath[0]
    else:
      #go for capsule ONLY when retreating
      """
      Going for the capsule ended up not being necessary
      
      if((gameState.getAgentState(opponents[0]).scaredTimer == 0 or gameState.getAgentState(opponents[1]).scaredTimer == 0)
              and len(capsule) != 0):
        capsulePath = self.findPathAndCost(gameState, self.index, capsule[0], 150, True)
        if(capsulePath != None):
          return capsulePath[0][0]
          
      print("INDEX: "+str(self.index)+" hunger="+str(self.hunger))
      if currentState.numCarrying > self.previousCarrying:
        self.hunger = 0
        self.hungerFood = None
      else:
        self.hunger += 1
      """

      #go for food
      if (len(self.getFood(gameState).asList()) > 2):
        foodPath = self.getLowestCostFoodPath(gameState)
        if(foodPath != None):
          return foodPath[0]

      #retreat
      if(self.shouldRetreat(gameState)):
        retreatPath = self.getLowestCostRetreatPath(gameState)
        if(retreatPath != None):
          return retreatPath[0]

      """
      retreatPath = self.getLowestCostRetreatPath(gameState)
      if(retreatPath != None):
        return retreatPath[0]
      """

    return "Stop"
"""
only one AI was necessary

class AttackReflexAgent(ReflexCaptureAgent):

  def chooseAction(self, gameState):

    if (self.shouldRetreat(gameState)):
      retreatPath = self.getLowestCostRetreatPath(gameState)
      if (retreatPath != None):
        return retreatPath[0]

    if (len(self.getFood(gameState).asList()) > 2):
      foodPath = self.getLowestCostFoodPath(gameState)
      if (foodPath != None):
        return foodPath[0]

    retreatPath = self.getLowestCostRetreatPath(gameState)
    if(retreatPath != None):
      return retreatPath[0]

    return "Stop" 
"""

#stores game state and related information for path generation
class Node:
  state = None
  parent = None
  action = None
  generalCost = 0
  totalCost = 0

  def __init__(self, s, p, a, g, t):
    self.state = s
    self.parent = p
    self.action = a
    self.generalCost = g
    self.totalCost = t

