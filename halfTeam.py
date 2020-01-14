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
    self.debug_index = 0

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

class HaulerReflexAgent(ReflexCaptureAgent):
  def registerInitialState(self, gameState):
    ReflexCaptureAgent.registerInitialState(self, gameState)

    #get one of the foods closest to the center and closest to the map edge
    food = self.getFood(gameState).asList()
    self.firstFood = None
    self.blacklist = []

    if self.red:
      self.firstFood = food[random.randrange(0,len(food),1)]
      self.safeColumn = 15
    else:
      self.firstFood = (10,15)
      self.safeColumn = 16

    #safe red-blue border locations
    self.safe = []
    for row in range(0, 15):
      if not gameState.hasWall(self.safeColumn, row):
        self.safe.append((self.safeColumn, row))

  """
  A reflex agent that makes a loop around the edge to get as much food as possible,
  then (hopefully) gets the capsule for a safe trip home.
  """
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

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
    opp_fut_state = None

    features['startHaul'] = 0
    features['distanceToFood'] = 0
    features['fleeEnemy'] = 0
    features['retreat'] = 0
    features['getCapsule'] = 0

    # Determine if the enemy is closer to you than they were last time
    # and you are in their territory, as well as their absolute distance to you
    delta_dist = 0
    absolute_dist = 999

    if currentState.isPacman:
      chasers = []
      for o in opponents:
        oppnState = successor.getAgentState(o)
        if oppnState.getPosition() != None and not oppnState.isPacman and not oppnState.scaredTimer > 0:
          chasers.append(o)

      closestChaser = None
      if len(chasers) > 0:
        for c in chasers:
          oppnState = successor.getAgentState(c)
          chaseDist = self.getMazeDistance(projectedPos, oppnState.getPosition())
          if chaseDist < absolute_dist:
            absolute_dist = chaseDist
            closestChaser = c

      if closestChaser != None:
        oppnPos = successor.getAgentState(closestChaser).getPosition()
        oppnPrevPos = prevGameState.getAgentState(closestChaser).getPosition()
        #new position - old position
        if oppnPrevPos != None and oppnPos != None:
          delta_dist = self.getMazeDistance(oppnPrevPos, prevPosition) - \
                       self.getMazeDistance(oppnPos, currentPos)


    pursuitConcern = (delta_dist >= 1)

    #protect from targeting the same food and getting stuck in a loop with a ghost
    if self.loopProtection == 2:
      minValue = 999
      blacklistedFood = None
      for f in self.getFood(successor).asList():
        food_dist = self.getMazeDistance(projectedPos, f)
        if food_dist < minValue:
          minValue = food_dist
          blacklistedFood = f
      self.blacklist.append(blacklistedFood)

    if self.firstFood != None:
      features['startHaul'] = self.getMazeDistance(projectedPos, self.firstFood)
      if projectedState.numCarrying == 1 or currentPos == self.start:
        self.firstFood = None

    foodList = self.getFood(successor).asList()
    for f in self.blacklist:
      foodList.remove(foodList.index(f))
    #features['successorScore'] = -len(foodList)#self.getScore(successor)

    # Compute distance to the nearest food
    minDistance = 100
    if projectedFood > currentFood:
      minDistance = 0
      self.blacklist = []
    elif len(foodList) > 0: # This should always be True,  but better safe than sorry
      minDistance = min([self.getMazeDistance(projectedPos, food) for food in foodList])

    #find closest safe spot (on my side) distance
    minSafe = 999
    for pos in self.safe:
      dist = self.getMazeDistance(projectedPos, pos)
      if dist < minSafe:
        minSafe = dist

    #find closest capsule distance
    minCapsule = 999
    for c in self.getCapsules(gameState):
      dist = self.getMazeDistance(projectedPos, c)
      if dist < minCapsule:
        minCapsule = dist

    """
    #determine if you're being followed!
    if close_dist <= self.previousDistance and not close_dist == 0:
      self.previousDistance = close_dist
      self.pursued += 1
    elif close_dist > self.previousDistance or close_dist == 0:
      self.previousDistance = 100
      self.pursued = 0
    """

    #for the first pellet collected, ignore closest pellet
    if features['startHaul'] == 0:
      features['distanceToFood'] = minDistance

    #print("Delta Dist: "+str(delta_dist))
    #if being pursued, ignore food and RUN
    if pursuitConcern:
      print("!!!Pursued!!!")
      features['distanceToFood'] = 0
      #if absolute_dist == 1:
      features['fleeEnemy'] = 100 #absolute_dist
    #otherwise, only run if you'll be captured due to going for food
    else:
      fleeEnemy = False
      if absolute_dist != 999:
        # check for food path viability compared to enemy distance
        flee = absolute_dist - (minDistance * 2)
        if flee <= 0:
          fleeEnemy = True
        if absolute_dist == 1:
          fleeEnemy = True
      #fleeing is only a weight if the enemy is relevant
      if fleeEnemy:
        features['fleeEnemy'] = absolute_dist + (minDistance * 2)

    #if the enemy is scared, weight retreat by how long they will be scared
    if currentState.isPacman:
      if opp_fut_state != None:
        for s in opponents:
          oppnState = successor.getAgentState(s)
          if not oppnState.isPacman and oppnState.scaredTimer > 0:
            features['retreat'] -= (40 - oppnState.scaredTimer)
      #weight retreat according to the distance to the safe point and the amount of food
      features['retreat'] = minSafe - int(currentFood**1.25)
      #if a capsule exists, do the same as above (capsules are weighted more heavily as a retreat option)
      if minCapsule != 999:
        features['getCapsule'] = minCapsule - int(currentFood**1.25)

    return features

  def getWeights(self, gameState, action):
    return {'startHaul': -1, 'distanceToFood': -2,
            'fleeEnemy': 1, 'retreat': -0.5, 'getCapsule': -0.25}

class CenterReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """
  def registerInitialState(self, gameState):
    ReflexCaptureAgent.registerInitialState(self, gameState)

    if self.red:
      self.guardPos = (12, 8) #c, r
    else:
      self.guardPos = (19 ,8)

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

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
    oppState = [gameState.getAgentState(o) for o in opponents]

    features['guard'] = 0
    features['guardRow'] = 0
    features['guardColumn'] = 0

    features['guard'] = self.getMazeDistance(projectedPos, self.guardPos)

    closestEnemy = None
    dist = 999
    mazeDist = 999
    for s in oppState:
      if s.getPosition() != None:
        mazeDist = self.getMazeDistance(s.getPosition(),projectedPos)
        if mazeDist < dist:
          closestEnemy = opponents[oppState.index(s)]
          dist = mazeDist

    if closestEnemy != None:
      oppPos = gameState.getAgentState(closestEnemy).getPosition()
      features['guardRow'] = abs(projectedPos[1] - oppPos[1])

    features['guardColumn'] = abs(projectedPos[0] - self.guardPos[0])

    return features

  def getWeights(self, gameState, action):
    return {'guard': -3, 'guardRow': -2, 'guardColumn': -1}

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
    teammates = self.getTeam(gameState)
    self.indexSmaller = (teammates.index(self.index) == 0)

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

    if prevGameState != None:
      prevState = prevGameState.getAgentState(self.index)
      prevPos = prevState.getPosition()

      opponents = self.getOpponents(gameState)

      if currentState.isPacman:
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
    if self.delta_dist >= 0:
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
    self.defense = ((self.red and score + carrying > 0) or (not self.red and score - carrying < 0)) and currentState.scaredTimer == 0

    #set debug index to get player output
    if self.index == self.debug_index:
      print("STATUS: "+"def="+str(self.defense)+" pursued="+str(self.pursued))
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
      if f[1] > board_height / 2 and self.indexSmaller:
        food.remove(f)
      elif f[1] < board_height / 2 and not self.indexSmaller:
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

    #if on offense with valid enemies, food to collect: if next food is too dangerous, don't go for it
    if (currentState.isPacman and features['distEnemy'] > 0 and features['distFood'] > 0):
      flee = features['distEnemy'] - (features['distFood'] * 2)
      if flee <= 0:
        features['distFood'] = 0

    #if defending, reverse weight of enemy to attack them, do not go for food or capsules
    if self.defense:
      features['distFood'] = 0
      features['distCapsule'] = 0
      if closestEnemy != None:
        if oppState.isPacman:
          features['distEnemy'] = -features['distEnemy']
        else:
          features['distEnemy'] = 0

    #if being pursued OR carrying too much (which shouldn't be an issue; this AI does not maximize score):
    if self.pursued >= 2 or currentState.numCarrying >= 9:
      features['distFood'] = 0

    return features

  #distance increased between guard position, nearest food, nearest capsules is BAD
  #distance increased between enemy (while on offense) is GOOD
  def getWeights(self, gameState, action):
    return {'guard': -1, 'distFood': -2,'distCapsule': -3, 'distEnemy': 3}