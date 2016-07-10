from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.controls import ControlManager, GravityWalker
from direct.showbase.DirectObject import *
import math
import SurfersGlobals

from toontown.minigame import ArrowKeys
from toontown.toonbase import TTLocalizer

class SurfersCamera:
    def __init__(self, player):
        self.player = player
        
    def start(self):
        camera.reparentTo(self.player.getAvatar())
        camera.setPos(0,-15,8)
        camera.setHpr(0,-15,0)
        
    def restart(self):
        self.start()
        
class SurfersController:
    lastY = 0.0
    speedForward = SurfersGlobals.ToonSpeedForward
    speedHorizontal = SurfersGlobals.ToonSpeedHorizontal
    def __init__(self, player):
        self.player = player
        self.arrowKeys = ArrowKeys.ArrowKeys()
        self.controlManager = ControlManager.ControlManager()
        self.win = False
        
    def start(self):
        grv = GravityWalker.GravityWalker()
        grv.setWallBitMask(BitMask32(1))
        grv.setFloorBitMask(BitMask32(2))
        grv.initializeCollisions(base.cTrav, self.player.getAvatar(), 1.4, 0.025, 4.0)
        grv.setAirborneHeightFunc(1)
        self.controlManager.add(grv, 'walk')
        self.controlManager.use('walk', self.player.getAvatar())
        self.controlManager.setSpeeds(0, 0, 0, 0)
        self.player.getAvatar().loop('run')
        taskMgr.add(self.__updateToonPos, 'update-toon-pos')
        
    def stop(self, forGood=1):
        if forGood:
            self.controlManager.remove('walk')
            self.controlManager.disable()
        taskMgr.remove('update-toon-pos')
        
    def restart(self):
        self.controlManager.enable()
        self.player.getAvatar().loop('run')
        taskMgr.add(self.__updateToonPos, 'update-toon-pos')
        
    def __updateToonPos(self, task):
        av = self.player.getAvatar()
        speed = (self.speedForward * (math.sqrt(2.) / 2.))
        distance = globalClock.getDt() * speed
        av.setFluidY(av.getY() + distance)
        
        # Check if toon is stuck
        if av.getY() == self.lastY:
            av.setX(av.getX() + 3)
        self.lastY = av.getY()

        speed = (self.speedHorizontal * (math.sqrt(2.) / 2.))
        distance = globalClock.getDt() * speed
        if self.arrowKeys.leftPressed():
            av.setFluidX(av.getX() - distance)
        elif self.arrowKeys.rightPressed():
            av.setFluidX(av.getX() + distance)
        return task.again
        
    def setSpeeds(self, forward = speedForward, horizontal = speedHorizontal):
        self.speedForward = forward
        self.speedHorizontal = horizontal

class SurfersPlayer(DirectObject):
    CollideWallEvent = 'SurfersLocalPlayerCollidedWall'
    def __init__(self, avatar):
        self.avatar = avatar
        self.win = False
        
    def getAvatar(self):
        return self.avatar
        
    def load(self):
        self.avatar.useLOD('1000')
        self.avatar.setScale(self.avatar.getScale() + 1)
        
    def unload(self):
        self.avatar.resetLOD()
        self.avatar.setScale(self.avatar.getScale() - 1)
        self.avatar.loop('neutral')
       
    def start(self):
        self.camera = SurfersCamera(self)
        self.camera.start()
        self.controller = SurfersController(self)
        self.controller.start()
        self.accept('WallCollidedBySurfersPlayer', self.__handlePlayerCollidedWall)
        
    def stop(self, forGood=1):
        base.surfersMinigame.factory.stopEvents()
        self.controller.stop(forGood)
        base.surfersMinigame.view.stop()
        
    def __handlePlayerCollidedWall(self, entry):
        messenger.send('StopFloorEvents')
        self.ignore('WallCollidedBySurfersPlayer')
        self.stop(forGood=0)
        base.surfersMinigame.cog.cogChase.stop()
        base.surfersMinigame.stopTheme()
        self.avatar.setY(self.avatar.getY() - 2)
        base.surfersMinigame.poster.slideUp(TTLocalizer.SurfersYouFell)
        slipIntr = Parallel(self.avatar.actorInterval('slip-backward',loop=0),
                            self.avatar.posInterval(0.6,(self.avatar.getX(),self.avatar.getY() - 4,
                            self.avatar.getZ())))
        seq = Sequence(slipIntr, Func(messenger.send, 'SurfersPlayerFell'), Func(self.accept, 'WallCollidedBySurfersPlayer', self.__handlePlayerCollidedWall))
        # Avoid crash
        try:
            seq.start()
        except:
            base.surfersMinigame.notify.warning('AVOID_CRASH: __handlePlayerCollidedWall')
        
    