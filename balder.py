from __future__ import print_function
from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint


def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveReflexAgent', second = 'DefensiveReflexAgent'):### DefensiveReflexAgent, OffensiveReflexAgent  CHARACTER TRAITS
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

class ReflexCaptureAgent(CaptureAgent):
  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

  def chooseAction(self, gameState):
    actions = gameState.getLegalActions(self.index)

    values = [self.evaluate(gameState, a) for a in actions]

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    foodLeft = len(self.getFood(gameState).asList())
    if foodLeft <= 2 or gameState.getAgentState(self.index).numCarrying > 2:#carrying weight
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start,pos2)
        if dist < bestDist:
          bestAction = action
          bestDist = dist
      return bestAction

    return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)

    return features * weights

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)

    return features

  def getWeights(self, gameState, action):
    return {'successorScore': 1.0}

class OffensiveReflexAgent(ReflexCaptureAgent):
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    foodList = self.getFood(successor).asList()   
    features['successorScore'] = -len(foodList)

    if len(foodList) > 0: 
      myPos = successor.getAgentState(self.index).getPosition()
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance

    close_dist = 9999.0
    if self.index == 1 and gameState.getAgentState(self.index).isPacman:
      opp_fut_state = [successor.getAgentState(i) for i in self.getOpponents(successor)]
      chasers = [p for p in opp_fut_state if p.getPosition() != None and not p.isPacman]
      if len(chasers) > 0:
        close_dist =  min([float(self.getMazeDistance(myPos, c.getPosition())) for c in chasers])

    features['fleeEnemy'] = 1.0/close_dist

    if action == Directions.STOP: 
      features['stop'] = 1
      rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]####test if it can back up under pressure
      if action == rev: 
        features['reverse'] = 100000

    return features

  def getWeights(self, gameState, action):
    return {'successorScore': 100, 'distanceToFood': -1, 'fleeEnemy': -2.0}

class DefensiveReflexAgent(ReflexCaptureAgent):
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    intruders = [a for a in enemies if a.getPosition() != None] 
    features['numInvaders'] = len(invaders)

    if len(intruders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in intruders]
      features['invaderDistance'] = min(dists)
      features['reverse'] = -1

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1    
    
    return features
  
  def getWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -20, 'stop': -100, 'reverse': -5}
