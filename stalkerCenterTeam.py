# stalkerCenterTeam.py
# ---------------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


# stalkerCenterTeam.py
# ---------------
# Licensing Information: Please do not distribute or publish solutions to this
# project. You are free to use and extend these projects for educational
# purposes. The Pacman AI projects were developed at UC Berkeley, primarily by
# John DeNero (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# For more info, see http://inst.eecs.berkeley.edu/~cs188/sp09/pacman.html
from __future__ import print_function
from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys
from game import Directions
import game
from util import nearestPoint


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'PredatorReflexAgent', second = 'PredatorReflexAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """
  def registerInitialState(self, gameState):
    self.mode = 0  # mode 0 = center defense, mode 1 = rally
    self.targetEnemy = 0  # enemy this agent must target
    self.guardCol = 12
    self.guardRow = [3, 10]
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

    #each teammate has one target enemy
    enemies = self.getOpponents(gameState)
    teammates = self.getTeam(gameState)
    self.targetEnemy = enemies[teammates.index(self.index)]
    print("Targeting Enemy: "+str(self.targetEnemy))

    #switch column defense range for blue
    if not self.red:
      self.guardCol = 18

  def chooseAction(self, gameState):
    """
    Picks among directions to move with the highest Q(s,a) judged by evaluation
    (decides how to move based on state data)
    Gives a summation of every (weight * feature) per action, so that the "best" action is taken
    """
    actions = gameState.getLegalActions(self.index)

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()

    values = [self.evaluate(gameState, a) for a in actions]
    if self.index == 0:
      print(values, file=sys.stderr)
      # print(self.getPreviousObservation(), file=sys.stderr)

    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    # if self.index == 1:
    #   print(bestActions, file=sys.stderr)

    #run for the border if you can win or you have 6 food, otherwise, randomly choose from weighted actions
    #(usually, there will only be one action in bestActions)
    if len(self.getFood(gameState).asList()) <= 2 or gameState.getAgentState(self.index).numCarrying > 5:
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
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """

    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)

    if self.index == 0:
      print(str(features) + str(weights), file=sys.stderr)
      # print(gameState.getAgentState(self.index)) # Print out a text representation of the world.

    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)

    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}

class PredatorReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that works with its teammate to straddle the center,
  and when enemy pacmen are captured, will rally one dot.
  """

  def getFeatures(self, gameState, action):
    features = util.Counter()
    #projection state via movement
    successor = self.getSuccessor(gameState, action)

    #projected state
    projectedState = successor.getAgentState(self.index)
    #projected position
    projectedPos = projectedState.getPosition()

    # Computes whether we're on defense (1) or offense (0)
    """
    features['onDefense'] = 1
    if myState.isPacman:
      features['onDefense'] = 0
    """

    #if target enemy is in start position, switch from mode 0 to mode 1
    #target = self.getPreviousObservation()

    target = successor.getAgentState(self.targetEnemy)
    targetPos = target.getPosition()
    unknownDistance = successor.getAgentDistances()[self.targetEnemy]

    #if target != None:
      #targetPos = target.getPosition()
      #targetPos = target.getAgentState(self.targetEnemy).getPosition()

    #print(targetPos)

    #if targetPos != None:
    #if targetPos == target.start and self.mode == 0: #not comparable?
    #  self.mode = 1
    # if pellet is held, switch from mode 1 to mode 0
    if projectedState.numCarrying == 1 and self.mode == 1:
      self.mode = 0

    features['distanceFromCenter'] = 0
    features['unknownEnemyDistance'] = 0
    features['enemyDistance'] = 0
    features['moveToFood'] = 0

    if self.mode == 0:
      features['distanceFromCenter'] = col_range(self.guardCol, projectedPos[0]) - 2 #column tolerance of 2 is acceptable
      #features['moveToEnemyRow'] = row_range(targetPos[1], projectedPos[1]) #minimize row to capture enemy
      features['unknownEnemyDistance'] = unknownDistance
      if targetPos != None:
        features['enemyDistance'] = self.getMazeDistance(projectedPos, targetPos)
      #if not there, move towards guard column (take into account either side)
      #if not there, then move towards enemy row
      #if near or outside

      #if mode 1, move towards nearest food evasively

      # Computes distance to invaders
    """
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0:
      dists = [self.getMazeDistance(projectedPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1
    """

    return features

  #notably, the base weights are multiplied by the features
  def getWeights(self, gameState, action):
    return {'distanceFromCenter': 15, 'enemyDistance': 2, 'unknownEnemyDistance': 1, 'moveToFood': 1}

#helper functions
def col_range(guardCol, myCol):
  return abs(guardCol - myCol)
def row_range(enemyRow, myRow):
  return abs(enemyRow - myRow)