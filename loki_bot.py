from __future__ import print_function
from captureAgents import CaptureAgent
import distanceCalculator
import random, time, util, sys, math
from game import Directions
import game
from util import nearestPoint


def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveReflexAgent', second = 'DefensiveReflexAgent'):
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

    if len(self.observationHistory) > 15:
        movementHistory = [self.observationHistory[-1*i].getAgentState(self.index).getDirection() for i in range(2,10)]
        reversingHistory = [movementHistory[0] if j % 2 == 0 else Directions.REVERSE[movementHistory[0]] for j in range(8)]

        if movementHistory == reversingHistory:
            return random.choice(actions)

    foodLeft = len(self.getFood(gameState).asList())

    if foodLeft <= 2:
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

  def __init__(self,index,timeForComputing=.1):
    self.centroids = None
    self.cluster_sizes = None
    self.random_centroid = None
    self.last_score = 99999

    ReflexCaptureAgent.__init__(self,index,timeForComputing)

  def chooseAction(self, gameState):
    foodList = self.getFood(gameState).asList()

    if gameState.getAgentState(self.index).getPosition() == self.start:
      self.centroids, self.cluster_sizes = self.kmeans(foodList, gameState)
      self.last_score = len(foodList)

      self.random_centroid = random.choice(self.centroids)

    if self.getScore(gameState) <= 0:
      if len(foodList) != self.last_score:
          self.centroids, self.cluster_sizes = self.kmeans(foodList, gameState)
          self.last_score = len(foodList)
    return ReflexCaptureAgent.chooseAction(self, gameState)

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    if self.getScore(gameState) <= 0:
      foodList = self.getFood(successor).asList()    
      features['successorScore'] = -len(foodList)

      if action == Directions.STOP:
          features['stop'] = 1
      else:
          features['stop'] = 0

      if len(foodList) > 0: 
        myPos = successor.getAgentState(self.index).getPosition()
        minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
        features['distanceToFood'] = minDistance

        if self.random_centroid != None:
            features['distanceToCentroid'] = self.getMazeDistance(myPos,self.random_centroid)

        distBigCentroid = self.getMazeDistance(myPos, self.centroids[self.cluster_sizes.index(max(self.cluster_sizes))])
        features['distanceToBigGroup'] = distBigCentroid

      if not gameState.getAgentState(self.index).isPacman:
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        ghosts = [a for a in enemies if not a.isPacman and a.getPosition() != None]

        features['numEnemies'] = len(invaders)

        if len(invaders) > 0:
          invader_dist = min([self.getMazeDistance(myPos, invader.getPosition()) for invader in invaders])
          features['flee'] = -1/invader_dist

        if len(ghosts) > 0:
            features['ghost'] = 1.0 /min([self.getMazeDistance(myPos, ghost.getPosition()) for ghost in ghosts])
        else:
            features['ghost'] = 0

      close_dist = 9999.0
      features['intowall'] = 0
      scared = False
      if gameState.getAgentState(self.index).isPacman:
        opp_fut_state = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        chasers = [p for p in opp_fut_state if p.getPosition() != None and not p.isPacman]
        features['numEnemies'] = len(chasers)
        if len(chasers) > 0:
          scared = chasers[0].scaredTimer > 0
          close_dist = min([float(self.getMazeDistance(myPos, c.getPosition())) for c in chasers])
          
          legal_actions = successor.getLegalActions(self.index)
          if action == Directions.STOP:
              features['intowall'] = -1000000000

          rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
          if legal_actions == [Directions.STOP] or legal_actions == [Directions.STOP, rev] or \
                  legal_actions == [rev, Directions.STOP]:
              features['intowall'] = -1000000000
      
      if scared:
        features['fleeEnemy'] = -1.0/close_dist

      else:
        features['fleeEnemy'] = 1.0/close_dist

      if gameState.getAgentState(self.index).numCarrying > 1:
        features['carry'] = gameState.getAgentState(self.index).numCarrying * self.getMazeDistance(myPos, self.start)
      else:
        features['carry'] = 0


    else:
      features['onDefense'] = 1
      if myState.isPacman: features['onDefense'] = 0

      enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
      invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
      features['numInvaders'] = len(invaders)

      if len(invaders) > 0:
        dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
        features['invaderDistance'] = min(dists)

      else:
        foodList = self.getFoodYouAreDefending(gameState).asList()
        dist = min([self.getMazeDistance(myPos, food) for food in foodList])
        features['byFood'] = dist
          
        team = [successor.getAgentState(i) for i in self.getTeam(successor) if i != self.index]
        defenders = [a for a in team if not a.isPacman and a.getPosition() != None]

        if len(defenders) > 0:
            ally_dist = min([self.getMazeDistance(myPos, ally.getPosition()) for ally in defenders])
            features['byAlly'] = 1.0/(ally_dist+.000000001)

      if action == Directions.STOP: features['stop'] = 1
      rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
      if action == rev: features['reverse'] = 1

    return features


  def kmeans(self,foodList,gameState):
    last_dist = 99999999999
    last_centroids = []
    last_clusters = []

    for i in range(1,7):
      clusters = [[] for j in range(i)]
      centroids = [self.findCentroid(cluster, gameState) for cluster in clusters]

      for j in range(40):
        clusters = [[] for k in range(i)]
        for food in foodList:
          distances = [self.getMazeDistance(food, centroid) for centroid in centroids]
          clusters[distances.index(min(distances))].append(food)
        centroids = [self.findCentroid(cluster, gameState) for cluster in clusters]
        
      tot_dist = self.calcTotalDist(centroids, clusters)

      if tot_dist >= last_dist:
          return (last_centroids, len(last_clusters))
      else:
          last_centroids = centroids
          last_clusters = clusters
      
    return (last_centroids, [len(clust) for clust in last_clusters])

  def calcTotalDist(self, centroids, clusters):
    dists = []
    for i in range(len(centroids)):
      dists.append(sum([self.getMazeDistance(centroids[i], food) for food in clusters[i]]))

    return sum(dists)

  def findCentroid(self, cluster, gameState):
    if len(cluster) == 0:
        x_avg, y_avg = (random.randint(1,30), random.randint(1,14))

    else:
      x_avg = sum([food[0] for food in cluster]) / len(cluster)
      y_avg = sum([food[1] for food in cluster]) / len(cluster)

    i = 1
    while gameState.hasWall(x_avg, y_avg):
        if x_avg - i >= 0 and not gameState.hasWall(x_avg - i, y_avg):
            x_avg = x_avg - i
        elif y_avg + i <= 15 and not gameState.hasWall(x_avg, y_avg + i):
            y_avg = y_avg + i
        elif x_avg + i <= 31 and not gameState.hasWall(x_avg + i, y_avg):
            x_avg = x_avg + i
        elif y_avg - i >= 0 and not gameState.hasWall(x_avg, y_avg - i):
            y_avg = y_avg - i
        i = i + 1
    return (x_avg, y_avg)

  def getWeights(self, gameState, action):
      if self.getScore(gameState) <= 0:
        return {'successorScore': 120, 'distanceToFood': -1.8, 'fleeEnemy': -50, 'distanceToCentroid': -.7,\
                'distanceToBigGroup': -.1,'carry': -1.6, 'intowall': 1, 'numEnemies': -500, 'stop': -10, 'ghost': -200}
      else:
          return {'numInvaders': -1000, 'onDefense': 5000, 'invaderDistance': -70, 'stop': -100, 'reverse': -2, 'byFood': -.2, \
                  'byAlly':-3}

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
    features['numInvaders'] = len(invaders)
    if len(invaders) > 0:
      features['byFood'] = 0
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)

    else:
        foodList = self.getFoodYouAreDefending(successor).asList()
        dist = min([self.getMazeDistance(myPos, food) for food in foodList])
        features['byFood'] = dist
        capsules = self.getCapsulesYouAreDefending(successor)
        if len(capsules) > 0:
            features['byCapsule'] = min([self.getMazeDistance(myPos, capsule) for capsule in capsules])
        team = [successor.getAgentState(i) for i in self.getTeam(successor) if i != self.index]
        defenders = [a for a in team if not a.isPacman and a.getPosition() != None]
        if len(defenders) > 0:
            ally_dist = min([self.getMazeDistance(myPos, ally.getPosition()) for ally in defenders])
            features['byAlly'] = 1.0/(ally_dist+.000000001)

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    return features

  def getWeights(self, gameState, action):
      return {'numInvaders': -1000, 'onDefense': 5000, 'invaderDistance': -100, 'stop': -100, 'reverse': -2, 'byFood': -.2, \
              'byCapsule': -.22, 'byAlly': -3}
