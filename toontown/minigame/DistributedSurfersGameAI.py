from DistributedMinigameAI import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
import SurfersGlobals

class DistributedSurfersGameAI(DistributedMinigameAI):

    def __init__(self, air, minigameId):
        try:
            self.DistributedMinigameTemplateAI_initialized
        except:
            self.DistributedMinigameTemplateAI_initialized = 1
            DistributedMinigameAI.__init__(self, air, minigameId)
            self.gameFSM = ClassicFSM.ClassicFSM('DistributedSurfersGameAI', [State.State('inactive', self.enterInactive, self.exitInactive, ['play']), State.State('play', self.enterPlay, self.exitPlay, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, ['inactive'])], 'inactive', 'inactive')
            self.addChildGameFSM(self.gameFSM)
        self.finishRequests = 0
        self.lastSpot = 1
        
    def generate(self):
        self.notify.debug('generate')
        DistributedMinigameAI.generate(self)

    def delete(self):
        self.notify.debug('delete')
        del self.gameFSM
        DistributedMinigameAI.delete(self)

    def setGameStart(self, timestamp):
        self.notify.debug('setGameStart')
        DistributedMinigameAI.setGameStart(self, timestamp)
        self.gameFSM.request('play')

    def setGameAbort(self):
        self.notify.debug('setGameAbort')
        if self.gameFSM.getCurrentState():
            self.gameFSM.request('cleanup')
        DistributedMinigameAI.setGameAbort(self)

    def enterInactive(self):
        self.notify.debug('enterInactive')

    def exitInactive(self):
        pass

    def enterPlay(self):
        self.notify.debug('enterPlay')
        taskMgr.doMethodLater(SurfersGlobals.Timeout, self.__timeout, 'timeout')
        
    def __timeout(self, task):
        for avId in self.scoreDict.keys():
            self.scoreDict[avId] = min(1,self.scoreDict[avId])
        self.__safeGameOver()

    def exitPlay(self):
        taskMgr.remove('timeout')

    def enterCleanup(self):
        self.notify.debug('enterCleanup')
        self.gameFSM.request('inactive')

    def exitCleanup(self):
        pass
        
    def updateJellybeans(self, jbs):
        sender = self.air.getAvatarIdFromSender()
        if sender in self.avIdList:
            self.scoreDict[sender] = jbs
            self.broadcastScore(sender, self.scoreDict[sender])
            
    def broadcastScore(self, avId, score):
        self.sendUpdate('updatePlayerScore', [avId,score])
        
    def finished(self):
        sender = self.air.getAvatarIdFromSender()
        if sender in self.avIdList:
            self.finishRequests += 1
            if self.lastSpot == 1:
                self.scoreDict[sender] += 30
            elif self.lastSpot == 2:
                self.scoreDict[sender] += 15
            elif self.lastSpot == 3:
                self.scoreDict[sender] += 1
            self.sendUpdate('playerFinished', [sender, self.lastSpot])
            self.lastSpot += 1
            if self.finishRequests == len(self.avIdList):
                def finishGame(task):
                    self.__safeGameOver()
                    return task.done
                taskMgr.doMethodLater(5.5, finishGame, 'finishgame')

    def __safeGameOver(self):
        if hasattr(self, 'frameworkFSM'):
            self.gameOver()
            