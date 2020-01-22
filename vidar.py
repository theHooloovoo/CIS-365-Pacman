from __future__ import print_function
from captureAgents import CaptureAgent
import math
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint

def createTeam(firstIndex, secondIndex, isRed,
               first = 'CapsuleReflexAgent', second = 'AttackReflexAgent'):
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

class ReflexCaptureAgent(CaptureAgent):
  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

  def findPathAndCost(self, gameState, agentIndex, travelTo, maxCost, checkForDeadend):
    openNodes = [Node(gameState, None, None, 0, 0)]
    closedNodes = []

    while(len(openNodes) != 0):
      nodeAndIndex = self.findLowestTotalCostNodeAndPop(openNodes)
      currentNode = nodeAndIndex[0]
      del openNodes[nodeAndIndex[1]]

      legalActions = currentNode.state.getLegalActions(agentIndex)  # gameState.getLegalActions(self.index)

      successors = []
      for action in legalActions:
        successor = currentNode.state.generateSuccessor(agentIndex, action)
        heuristics = self.calculateHeuristicCosts(successor, successor.getAgentPosition(agentIndex), travelTo)

        if(currentNode.generalCost + heuristics[1] > maxCost):
          continue

        successors.append(Node(
          successor,
          currentNode,
          action,
          currentNode.generalCost + 1 + heuristics[0],
          currentNode.generalCost + 1 + heuristics[1]
          ))

      for s in successors:
        if(self.agentPositionMatchesDestination(s, travelTo)):
          pathAndCost = self.generatePathOfActions(s)
          return pathAndCost

        if(self.nodeShouldBeOpened(s, openNodes, closedNodes)):
          openNodes.append(s)
      closedNodes.append(currentNode)
    return None

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

  def agentPositionMatchesDestination(self, node, travelTo):
    agentX, agentY = node.state.getAgentPosition(self.index)
    if(agentX == int(travelTo[0]) and int(agentY) == int(travelTo[1])):
      return True
    return False

  def nodeShouldBeOpened(self, node, openList, closedList):
    for o in openList:
      if(node.state.getAgentPosition(self.index) == o.state.getAgentPosition(self.index) and node.totalCost > o.totalCost):
        return False

    for c in closedList:
      if (node.state.getAgentPosition(self.index) == c.state.getAgentPosition(
              self.index) and node.totalCost > c.totalCost):
        return False

    return True

  def generatePathOfActions(self, node):
    totalCost = node.generalCost
    actionList = []
    currentNode = node
    while(currentNode.parent != None):
      actionList.insert(0, currentNode.action)
      currentNode = currentNode.parent

    return (actionList, totalCost)

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

  def getSuccessor(self, gameState, action):
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

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

  def getLowestCostFoodPath(self, gameState):
    food = self.getFood(gameState).asList()

    lowestCost = 60
    lowestPath = None

    while len(food) > 0:

      closestDistance = 99999
      closestIndex = 0
      i = 0
      for f in food:
        currentDistance = self.getMazeDistance(gameState.getAgentPosition(self.index), f)
        if(currentDistance < closestDistance):
          closestDistance = currentDistance
          closestIndex = i
        i += 1
      currentFood = food.pop(closestIndex)


      path = self.findPathAndCost(gameState, self.index, currentFood, lowestCost, True)
      if(path != None and path[1] < lowestCost):
        lowestPath = path[0]
        lowestCost = path[1]

    return lowestPath

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

  def shouldRetreat(self, gameState):
    opponents = self.getOpponents(gameState)
    for o in opponents:
      position = gameState.getAgentPosition(o)
      if(position != None and self.getMazeDistance(position, gameState.getAgentPosition(self.index)) <= 4
              and gameState.getAgentState(o).scaredTimer == 0) and gameState.getAgentState(self.index).isPacman:
        return True

class CapsuleReflexAgent(ReflexCaptureAgent):

  def chooseAction(self, gameState):
    opponents = self.getOpponents(gameState)
    capsule = self.getCapsules(gameState)

    if((gameState.getAgentState(opponents[0]).scaredTimer == 0 or gameState.getAgentState(opponents[1]).scaredTimer == 0)
            and len(capsule) != 0):
      capsulePath = self.findPathAndCost(gameState, self.index, capsule[0], 150, True)
      if(capsulePath != None):
        return capsulePath[0][0]

    if(self.shouldRetreat(gameState)):
      retreatPath = self.getLowestCostRetreatPath(gameState)
      if(retreatPath != None):
        return retreatPath[0]

    if (len(self.getFood(gameState).asList()) > 2):
        foodPath = self.getLowestCostFoodPath(gameState)
        if(foodPath != None):
          return foodPath[0]

    retreatPath = self.getLowestCostRetreatPath(gameState)
    if(retreatPath != None):
      return retreatPath[0]

    return "Stop"

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

