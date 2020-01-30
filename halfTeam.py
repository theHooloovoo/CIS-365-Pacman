# baselineTeam.py
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


# baselineTeam.py
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
from game import Directions, Grid
import game
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'HalfReflexAgent', second = 'HalfReflexAgent'):
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
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)
    self.turnsAsPacman = -1
    self.loopProtection = 0
    self.debug_index = 2

  def chooseAction(self, gameState):
    """
    Picks among directions to move with the highest Q(s,a) judged by evaluation
    (decides how to move based on state data)
    """
    actions = gameState.getLegalActions(self.index)
    actions.remove('Stop') #DON'T STOP THE DISCO

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]

    if gameState.getAgentState(self.index).isPacman:
      self.turnsAsPacman+=1
    elif self.turnsAsPacman < 4 and self.turnsAsPacman > -1:
      self.loopProtection+=1
      if self.loopProtection > 2:
        self.loopProtection = -1
        self.turnsAsPacman = -1

    if self.index == self.debug_index:
      print(actions)
      print(values)
      # print(self.getPreviousObservation(), file=sys.stderr)

    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]
    # if self.index == 1:
    #   print(bestActions, file=sys.stderr)

    #run for start if enough food is held
    foodLeft = len(self.getFood(gameState).asList())

    """
    #maybe keep this, but it's not always efficient for hauler
    if foodLeft <= 2 or gameState.getAgentState(self.index).numCarrying > 5:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start,pos2)
        if dist < bestDist:
          bestAction = action
          bestDist = dist
      return bestAction
    """

    choice = random.choice(bestActions)

    if self.index == self.debug_index:
      print("Choice: " + choice)
      print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    return choice

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

    if self.index == self.debug_index:
      print(action + ":" + str(features) + str(weights))
      #print(gameState.getAgentState(self.index)) # Print out a text representation of the world.

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

class HalfReflexAgent(ReflexCaptureAgent):
  """
  -A reflex agent that focuses pellets on a top/bottom half of the map and
  defends its half if score is in its favor.
  -Made to win, not to maximize score.
  -Probably would be vulnerable to team coordination when playing defense
  -Fleeing algorithm is far from perfect, but not always required to win
  """

  #override ReflexAgent's initial state
  def registerInitialState(self, gameState):
    ReflexCaptureAgent.registerInitialState(self, gameState)

    #number of consecutive turns on offense that enemy distance to you is <= previous distance
    self.pursued = 0
    #for above
    self.dist_delta = -1
    #whether to play defense or not
    self.defense = False

    #what half you will take (bottom, top)
    self.teammates = self.getTeam(gameState)
    self.indexSmaller = (self.teammates.index(self.index) == 0)

    #split ghosts up enough
    self.splitGuard = 0

    #set best defensive positions (for default map -- if map is changed, these can be calculated instead)
    self.guardPos = None
    if self.indexSmaller:
      if self.red:
        self.guardPos = (12, 11) #c, r
      else:
        self.guardPos = (18 ,11)
    else:
      if self.red:
        self.guardPos = (13, 4) #c, r
      else:
        self.guardPos = (19 ,4)

  def chooseAction(self, gameState):
    """
    Picks among directions to move with the highest Q(s,a) judged by evaluation
    (decides how to move based on state data)
    """

    actions = gameState.getLegalActions(self.index)
    actions.remove('Stop') #never stop moving!

    # You can profile your evaluation time by uncommenting these lines
    values = [self.evaluate(gameState, a) for a in actions]
    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    choice = random.choice(bestActions)

    # calculate dist_delta: the new state's distance from the enemy compared to the current state
    absolute_dist = 999
    self.delta_dist = -1

    currentState = gameState.getAgentState(self.index)
    currentPos = currentState.getPosition()
    prevGameState = self.getPreviousObservation()

    prevState = None
    prevPos = None
    if prevGameState != None:
      prevState = prevGameState.getAgentState(self.index)
      prevPos = prevState.getPosition()

      opponents = self.getOpponents(gameState)

      if currentState.isPacman:
        #paranoid - default is that you're being hunted
        self.delta_dist = 999

        chasers = []
        for o in opponents:
          oppnState = gameState.getAgentState(o)
          if oppnState.getPosition() != None and not oppnState.isPacman and not oppnState.scaredTimer > 0:
            chasers.append(o)

        closestChaser = None
        if len(chasers) > 0:
          for c in chasers:
            oppnState = gameState.getAgentState(c)
            chaseDist = self.getMazeDistance(currentPos, oppnState.getPosition())
            if chaseDist < absolute_dist:
              absolute_dist = chaseDist
              closestChaser = c

        if closestChaser != None:
          oppnPos = gameState.getAgentState(closestChaser).getPosition()
          oppnPrevPos = self.getPreviousObservation().getAgentState(closestChaser).getPosition()
          # new position - old position
          if oppnPrevPos != None and oppnPos != None:
            self.delta_dist = self.getMazeDistance(oppnPrevPos, prevPos) - \
                         self.getMazeDistance(oppnPos, currentPos)

    #if the closest enemy is closer or the same distance from last time, increment pursuit counter
    if not self.defense and self.delta_dist >= 0:
      self.pursued += 1
      #immediate flee trigger for close distances
      if absolute_dist <= 4:
        self.pursued += 1
    else:
      self.pursued = 0

    #calculate whether to play defense: based on projected score (notably, NOT what the opponent is holding)
    successor = self.getSuccessor(gameState, choice)
    myTeam = self.getTeam(successor)
    score = self.getScore(successor)
    carrying = 0
    for a in myTeam:
      carrying += successor.getAgentState(a).numCarrying

    #no reason to play defense if you're scared -- go on offense instead
    self.defense = ((self.red and score + carrying > 0) or (not self.red and -score - carrying < 0)) and currentState.scaredTimer == 0

    if prevPos != None and prevPos == self.start:
      self.splitGuard = 25
    elif self.splitGuard > 0:
      self.splitGuard -= 1

    #set debug index to get player output
    if self.index == self.debug_index:
      print("STATUS: "+"def="+str(self.defense)+" pursued="+str(self.pursued)+" splitGuard="+str(self.splitGuard))
      print(actions)
      print(values)
      print("Choice: " + choice)
      print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~")

    return choice

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    #initial variables (not all are used, but are there for convenience)
    currentState = gameState.getAgentState(self.index)
    currentPos = currentState.getPosition()
    currentFood = currentState.numCarrying

    projectedState = successor.getAgentState(self.index)
    projectedPos = projectedState.getPosition()
    projectedFood = projectedState.numCarrying

    prevGameState = self.getPreviousObservation()
    prevPosition = None
    if prevGameState != None:
      prevState = prevGameState.getAgentState(self.index)
      prevPosition = prevState.getPosition()

    opponents = self.getOpponents(successor)
    oppAllStates = [gameState.getAgentState(o) for o in opponents]
    capsules = self.getCapsules(successor)

    #initial weights
    features['guard'] = 0
    features['distFood'] = 0
    features['distCapsule'] = 0
    features['distEnemy'] = 0

    #distance to guard position
    features['guard'] = self.getMazeDistance(projectedPos, self.guardPos)

    #update food list
    board_height = 16
    food = self.getFood(gameState).asList()
    for f in food:
      if f[1] <= board_height / 2 and self.indexSmaller:
        food.remove(f)
      elif f[1] > board_height / 2 and not self.indexSmaller:
        food.remove(f)

    #get distance to closest food (notably, in your half only)
    if len(food) > 0:  # This should always be True,  but better safe than sorry
      features['distFood'] = min([self.getMazeDistance(projectedPos, f) for f in food])

    #only the top player will get the capsule; get distance to closest capsule
    if not self.indexSmaller:
      if len(capsules) > 0:  # This should always be True,  but better safe than sorry
        features['distCapsule'] = min([self.getMazeDistance(projectedPos, c) for c in capsules])

    #get distance to closest enemy
    closestEnemy = None
    oppState = None
    dist = 999
    mazeDist = 999
    for s in oppAllStates:
      if s.getPosition() != None:
        mazeDist = self.getMazeDistance(s.getPosition(),projectedPos)
        if mazeDist < dist:
          closestEnemy = opponents[oppAllStates.index(s)]
          dist = mazeDist

    if (currentState.isPacman or self.defense) and closestEnemy != None:
      oppState = gameState.getAgentState(closestEnemy)
      oppPos = oppState.getPosition()
      features['distEnemy'] = self.getMazeDistance(oppPos, projectedPos)
      #do not flee enemy if they are scared...
      if oppState.scaredTimer > 0:
        features['distEnemy'] = 0

    #if defending, reverse weight of enemy to attack them, do not go for food or capsules
    if self.defense:
      features['distFood'] = 0
      features['distCapsule'] = 0
      if closestEnemy != None:
        if oppState.isPacman:
          features['distEnemy'] = -features['distEnemy']

          # defenders should ignore pacmen if there are defending teammates closer to them
          for o in opponents:
            oppnPos = gameState.getAgentState(o).getPosition()
            if oppnPos != None:
              closerToSome = False
              for t in self.teammates:
                if self.getMazeDistance(gameState.getAgentState(t).getPosition(), oppnPos) < self.getMazeDistance(
                              currentPos, oppnPos):
                  features['distEnemy'] = 0
                  break
        else:
          features['distEnemy'] = 0
    elif self.splitGuard > 0:
      features['guard'] *= 4
    elif self.pursued < 2:
      features['guard'] = 0

    #if being pursued OR carrying too much (which shouldn't be an issue; this AI does not maximize score):
    if self.pursued >= 2: #or currentState.numCarrying >= 9:
      # if on offense with valid enemies, food to collect: if next food is too dangerous, don't go for it
      if (currentState.isPacman and features['distEnemy'] > 0 and features['distFood'] > 0):
        flee = features['distEnemy'] - (features['distFood'] * 2)
        if flee <= 0:
          features['distFood'] = 0
    #else:
      #features['distEnemy'] /= 2
      #features['distFood'] = 0

    return features

  #distance increased between guard position, nearest food, nearest capsules is BAD
  #distance increased between enemy (while on offense) is GOOD
  def getWeights(self, gameState, action):
    return {'guard': -1, 'distFood': -2,'distCapsule': -3, 'distEnemy': 3}