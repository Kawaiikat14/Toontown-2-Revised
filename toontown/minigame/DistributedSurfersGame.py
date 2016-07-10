from pandac.PandaModules import *
from toontown.toonbase.ToonBaseGlobal import *
from DistributedMinigame import *
from direct.fsm import ClassicFSM, State
from direct.fsm import State
from toontown.toonbase import TTLocalizer
from direct.interval.IntervalGlobal import *
from toontown.toonbase import ToontownTimer

from SurfersFactory import *
from SurfersPlayer import *
from SurfersCog import *
from SurfersView import *
from SurfersGUI import *
import SurfersGlobals

class DistributedSurfersGame(DistributedMinigame):
    TIME = SurfersGlobals.Timeout
    themeDir = 'phase_4/audio/bgm/mg_surfers.mp3'
    loseDir = 'phase_4/audio/sfx/mg_surfers_lose.mp3'
    y_distance_cog = 31

    def __init__(self, cr):
        DistributedMinigame.__init__(self, cr)
        self.gameFSM = ClassicFSM.ClassicFSM('DistributedSurfersGame', [State.State('off', self.enterOff, self.exitOff, ['play']), State.State('play', self.enterPlay, self.exitPlay, ['cleanup']), State.State('cleanup', self.enterCleanup, self.exitCleanup, [])], 'off', 'cleanup')
        self.addChildGameFSM(self.gameFSM)
        self.numWinners = 0
        self.timedOut = False

    def getTitle(self):
        return TTLocalizer.MinigameSurfersTitle

    def getInstructions(self):
        return TTLocalizer.MinigameSurfersInstructions

    def getMaxDuration(self):
        return self.TIME + 120

    def load(self):
        DistributedMinigame.load(self)
        base.surfersMinigame = self
        self.poster = SurfersPoster()
        self.poster.prepare()
        self.effects = SurfersEffects()
        self.effects.prepare()
        self.player = SurfersPlayer(base.localAvatar)
        self.cog = SurfersCog()
        self.gui = SurfersGUI()
        self.theme = base.loadMusic(self.themeDir)
        self.theme.setVolume(0.4)
        self.theme.setLoop(1)
        self.loseSfx = base.loadSfx(self.loseDir)

    def unload(self):
        self.notify.debug('unload')
        DistributedMinigame.unload(self)
        self.removeChildGameFSM(self.gameFSM)
        del self.gameFSM
        self.poster.unload()
        self.player.stop()
        self.cog.stop()
        del self.poster, self.player
        del self.cog

    def onstage(self):
        self.notify.debug('onstage')
        base.localAvatar.laffMeter.obscure(1)
        base.localAvatar.chatMgr.fsm.request('otherDialog')
        DistributedMinigame.onstage(self)
        self.factory = SurfersFactory()
        self.factory.generate()
        self.gui.load()
        self.player.load()
        self.cog.load()
        self.factory.addPlayer(self.player)
        self.factory.addCog(self.cog)
        self.view = SurfersView(self.factory)
        self.view.start()

    def offstage(self):
        self.notify.debug('offstage')
        base.localAvatar.laffMeter.obscure(0)
        base.localAvatar.chatMgr.fsm.request('mainMenu')
        base.localAvatar.show()
        DistributedMinigame.offstage(self)
        self.gui.unload()
        self.player.unload()
        self.cog.unload()
        self.cog.getSuit().removeNode()
        self.factory.unload()
        self.view.stop()
        camera.reparentTo(render)
        camera.setPos(0,0,0)
        camera.setHpr(0,0,0)

    def handleDisabledAvatar(self, avId):
        self.notify.debug('handleDisabledAvatar')
        self.notify.debug('avatar ' + str(avId) + ' disabled')
        self.gui.score.removePlayer(avId)

    def makeCameraInterval(self):
        iv = camera.posInterval(3,(0,25,7))
        iv2 = camera.posHprInterval(2,(0,-10,7),(0,0,0))
        iv3 = camera.posInterval(5,(0,-30,7))
        return Sequence(iv,iv2,iv3)
        
    def setGameReady(self):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameReady')
        if DistributedMinigame.setGameReady(self):
            return
        self.cameraIval = self.makeCameraInterval()
        self.cameraIval.start()

    def setGameStart(self, timestamp):
        if not self.hasLocalToon:
            return
        self.notify.debug('setGameStart')
        DistributedMinigame.setGameStart(self, timestamp)
        self.cameraIval.finish()
        self.gameFSM.request('play')

    def enterOff(self):
        self.notify.debug('enterOff')

    def exitOff(self):
        pass

    def enterPlay(self):
        self.notify.debug('enterPlay')
        self.gui.createScoresPanel(self.avIdList)
        self.timer = ToontownTimer.ToontownTimer()
        self.timer.posInTopRightCorner()
        self.timer.setTime(self.TIME)
        self.timer.countdown(self.TIME, self.__handleTimeout)
        self.player.start()
        self.cog.start()
        self.theme.stop()
        self.theme.setVolume(1)
        self.theme.play()

    def exitPlay(self):
        self.gui.removeScoresPanel()
        self.timer.stop()
        self.timer.destroy()
        self.player.stop()
        self.cog.stop()
        
    def __handleTimeout(self):
        self.notify.debug('timeout')
        self.timedOut = True
        if not self.player.win:
            self.stopTheme()
            self.loseSfx.play()
            self.__doCogTax()
            
            def gameOver(task):
                self.gameOver()
                return task.done
            self.finished()
            taskMgr.doMethodLater(5.0,gameOver,'gameover')
        
    def __doCogTax(self):
        self.notify.debug('cogTaz')
        tax = int(self.gui.jellybeans.jbs.getText()) / 2
        def _less(task):
            if int(self.gui.jellybeans.jbs.getText()) > tax:
                self.gui.jellybeans.subt()
                return task.again
            self.poster.slideUp(TTLocalizer.SurfersTax, 2.5)
            return task.done
        taskMgr.add(_less, 'less-jbs')
            

    def enterCleanup(self):
        self.notify.debug('enterCleanup')

    def exitCleanup(self):
        pass

    def stopAll(self):
        self.notify.debug('stopAll')
        self.player.stop(0)
        self.cog.stop()
        self.view.stop()
        self.gui.unload()
        self.stopTheme()
        
    def playTheme(self):
        self.theme.setPlayRate(0)
        self.theme.play()
        def playThemeTask(task):
            if self.theme.getPlayRate() < 1:
                self.theme.setPlayRate(self.theme.getPlayRate() + (globalClock.getDt() * 0.6))
                return task.again
            self.theme.setPlayRate(1)
            return task.done
        taskMgr.add(playThemeTask, 'play-theme-task')
        
    def stopTheme(self):
        self.theme.setPlayRate(1)
        def stopThemeTask(task):
            if self.theme.getPlayRate() > 0:
                self.theme.setPlayRate(self.theme.getPlayRate() - (globalClock.getDt() * 0.4))
                return task.again
            self.theme.stop()
            return task.done
        taskMgr.add(stopThemeTask, 'stop-theme-task')
        
    def restart(self, doneFunc = None, doneArgs = []):
        self.notify.debug('restart')
        curIndex = self.view.moduleIndex
        lastIndex = (curIndex - 1) if curIndex != 0 else curIndex
        last = self.factory.getModules()[lastIndex]
        lastGeom = last.getGeom()
        av = self.player.getAvatar()
        suit = self.cog.getSuit()
        last.posAvatar(self.player.getAvatar())
        last.posSuit(self.cog.getSuit())
        self.player.controller.restart()
        self.player.camera.restart()
        self.cog.reload()
        self.cog.restart()
        self.factory.startEvents()
        self.view.restart(newIndex=lastIndex)
        if doneFunc:
            doneFunc(*doneArgs)
        
    def updateJellybeans(self, jbs):
        self.sendUpdate('updateJellybeans', [jbs])
        
    def finished(self):
        self.sendUpdate('finished')
        
    def updatePlayerScore(self, avId, score):
        if avId in self.avIdList:
            self.gui.score.updatePlayerScore(avId, score)
            
    def playerFinished(self, avId, spot):
        if not self.timedOut:
            if avId in self.avIdList:
                self.gui.score.setSpotWinner(avId, spot)
                self.numWinners += 1
                if self.numWinners == len(self.avIdList):
                    self.gameOver()
            