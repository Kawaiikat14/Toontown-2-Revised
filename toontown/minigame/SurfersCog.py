from panda3d.core import *
from direct.interval.IntervalGlobal import *
from direct.showbase.DirectObject import *
import random, math
import SurfersGlobals

from toontown.suit import Suit, SuitDNA
from toontown.battle import BattleProps
from toontown.toonbase import TTLocalizer

runningHor = False

class CogChase:
    speedForward = SurfersGlobals.CogSpeedForward
    speedHorizontal = SurfersGlobals.CogSpeedHorizontal
    initialSpeedForward = speedForward
    ignoreWall = 0
    MaxMoveTime = 100
    def __init__(self, cog):
        self.cog = cog
        
    def start(self):
        missRay = CollisionSegment(0,0,0,0,11.0,0)
        cn = CollisionNode('CogChaseMissRay')
        cn.addSolid(missRay)
        cn.setFromCollideMask(BitMask32(1))
        cn.setIntoCollideMask(BitMask32.allOff())
        self.missRay = self.cog.getSuit().attachNewNode(cn)
        self.missRay.setZ(5)
        self.missQueue = CollisionHandlerQueue()
        base.cTrav.addCollider(self.missRay, self.missQueue)
        self.lastDistance = base.surfersMinigame.y_distance_cog
        
        taskMgr.add(self.__updateSuitPos, 'update-suit-pos')
        
    def stop(self):
        taskMgr.remove('update-suit-pos')
        taskMgr.remove('fix-z')
        taskMgr.remove('fix-z-back')
        taskMgr.remove('add-z-back')
        taskMgr.remove('goto-x')
        
    def restart(self):
        self.start()
        
    def __updateSuitPos(self, task):
        suit = self.cog.getSuit()
        toon = base.surfersMinigame.player.getAvatar()
        
        dt = globalClock.getDt()
        # If the suit is near to a wall
        if not self.ignoreWall:
            numEntries = self.missQueue.getNumEntries()
            if numEntries > 0:
                for i in range(numEntries):
                    entry = self.missQueue.getEntry(i)
                    fromObj = entry.get_into_node()
                    if base.surfersMinigame.factory.isWallCollision(fromObj.getName()):
                        if suit.getX() > 3.00000023842 or suit.getX() < -3.20000052452:
                            break
                        def fix_z_back(task):
                            if suit.getZ() < 11:
                                suit.setZ(suit.getZ() + (dt * 18.0))
                                return task.again
                            self.speedForward = self.initialSpeedForward
                            global runningHor
                            runningHor = False
                            self.ignoreWall = 0
                            return task.done
                        def fix_z(task):
                            self.speedForward = 28.0 * 1.25
                            if suit.getZ() > -3:
                                suit.setZ(suit.getZ() - (dt * 18.0))
                                return task.again
                            def add_z_back(task):
                                taskMgr.add(fix_z_back, 'fix-z-back')
                                return task.done
                            taskMgr.doMethodLater(0.4, add_z_back, 'add-z-back')
                            return task.done
                        global runningHor
                        runningHor = True
                        messenger.send('CogChaseAvoidingWall')
                        taskMgr.add(fix_z, 'fix-z')
                        self.ignoreWall = 1
                        
        # If the suit is very near to the toon
        distance = (toon.getY() - suit.getY())
        if distance < 5 and not self.cog.attacking:
            self.cog.attackToon()
        
        # If the suit is getting out of the radar
        if distance >= 100:
            self.speedForward = SurfersGlobals.CogHurrySpeed
        else:
            if self.speedForward == SurfersGlobals.CogHurrySpeed:
                if distance < 45:
                    self.speedForward = SurfersGlobals.CogSpeedForward
        
        # Adjust camera
        if int(distance) != int(self.lastDistance):
            change = 0#.3
            if distance < self.lastDistance:
                camera.setY(camera.getY() - change)
            elif distance > self.lastDistance and camera.getY() < -15:
                camera.setY(camera.getY() + change)
        self.lastDistance = distance
            
        if suit.getX() != toon.getX() and not runningHor:
            def goto_x(task):
                global runningHor
                runningHor = True
                if suit.getX() != toon.getX():
                    speed = (self.speedHorizontal * (math.sqrt(2.) / 2.))
                    distance = globalClock.getDt() * speed
                    if toon.getX() > suit.getX():
                        suit.setFluidX(suit.getX() + distance)
                    elif toon.getX() < suit.getX():
                        suit.setFluidX(suit.getX() - distance)
                    return task.again
                runningHor = False
                return task.done
            taskMgr.add(goto_x, 'goto-x')
                    
        if distance > 2:
            speed = (self.speedForward * (math.sqrt(2.) / 2.))
            distance = globalClock.getDt() * speed
            suit.setFluidPos(suit.getX(), suit.getY() + distance, suit.getZ())
        return task.again
    
class SurfersCog(DirectObject):
    attacking = False
    loseSoundPath = 'phase_4/audio/sfx/mg_surfers_lose.mp3'
    def __init__(self):
        pass
       
    def getSuit(self):
        return self.suit
        
    def load(self):
        self.suit = Suit.Suit()
        dna = SuitDNA.SuitDNA()
        dna.newSuitRandom(level=0,dept='m')
        self.suit.setDNA(dna)
        self.suit.reparentTo(render)
        self.suit.setScale(self.suit.getScale() + 1)
        self.suit.nametag3d.stash()
        floatIntvDw = self.suit.actorInterval('landing',startFrame=0,endFrame=15,playRate=0.5)
        floatIntvUp = self.suit.actorInterval('landing',startFrame=15,endFrame=0,playRate=0.5)
        self.floatSeq = Sequence(floatIntvDw,floatIntvUp)
        self.floatSeq.loop()
        self.propeller = BattleProps.globalPropPool.getProp('propeller')
        self.propeller.reparentTo(self.suit.find('**/joint_head*') or self.suit.find('**/to_head*'))
        self.propeller.loop('propeller',fromFrame=0,toFrame=20)
        
    def unload(self):
        self.propeller.removeNode()
        self.suit.cleanup()
    
    def start(self):
        self.cogChase = CogChase(self)
        self.cogChase.start()
        self.accept('SurfersPlayerFell', self.__handleSurfersPlayerFell)
        
    def restart(self):
        self.start()
        
    def stop(self,stopFloat=True):
        self.cogChase.stop()
        self.ignore('SurfersPlayerFell')
        messenger.send('CogChaseAvoidingWall')
        if stopFloat:
            if hasattr(self, 'floatSeq'):
                self.floatSeq.finish()
                del self.floatSeq
        
    def reload(self):
        if not hasattr(self, 'floatSeq'):
            floatIntvDw = self.suit.actorInterval('landing',startFrame=0,endFrame=15,playRate=0.5)
            floatIntvUp = self.suit.actorInterval('landing',startFrame=15,endFrame=0,playRate=0.5)
            self.floatSeq = Sequence(floatIntvDw,floatIntvUp)
            self.floatSeq.loop()
            self.propeller.loop('propeller',fromFrame=0,toFrame=20)
        
    def __handleSurfersPlayerFell(self):
        toon = base.surfersMinigame.player.getAvatar()
        y = (toon.getY() - 3)
        pre_land = Parallel(self.suit.posInterval(1.6, (toon.getX(),y,-2)),
                            camera.posInterval(1.6, (camera.getX(), camera.getY() - 8, camera.getZ())))
        grabToon = Func(toon.loop,'struggle',fromFrame=0,toFrame=15)
        def restartDone():
            base.surfersMinigame.playTheme()
            base.surfersMinigame.effects.irisIn()
        
        lose = base.loadMusic(self.loseSoundPath)
        lose.play()
        landSeq = Sequence(pre_land,grabToon,Wait(1.5),Func(base.surfersMinigame.effects.irisOut),Wait(.6),
                            Func(base.surfersMinigame.restart, restartDone))
        # Avoid crash
        try:
            landSeq.start()
        except:
            base.surfersMinigame.notify.warning('AVOID_CRASH: LandSeq')
        
    def attackToon(self):
        self.attacking = True
        suit = self.suit
        toon = base.surfersMinigame.player.getAvatar()
        def nevermind():
            def fix_z(task):
                if suit.getZ() < 5:
                    suit.setZ(suit.getZ() + 0.2)
                    return task.again
                self.attacking = False
                return task.done
            taskMgr.add(fix_z, 'fix-z-nvm')
        def grab_toon():
            toonGrabbedAnim = Func(toon.loop,'struggle',fromFrame=0,toFrame=15)
            def stop_toon():
                base.surfersMinigame.player.stop(0)
            def stop_cog():
                self.stop(False)
            def restartDone():
                self.attacking = False
                base.surfersMinigame.effects.irisIn()
            base.surfersMinigame.poster.slideUp(TTLocalizer.SurfersCogReach)
            seq = Sequence(Func(camera.posInterval(1.6, (camera.getX(), camera.getY() - 8, camera.getZ())).start),
                        Func(stop_toon),Func(stop_cog),toonGrabbedAnim,Wait(1.5),
                        Func(base.surfersMinigame.effects.irisOut),Wait(.6),Func(base.surfersMinigame.restart, restartDone))
            # Avoid crash
            try:
                seq.start()
            except:
                base.surfersMinigame.notify.warning('AVOID_CRASH: attackToon')
        def get_near_enough(task):
            rt = False
            if(toon.getY() - suit.getY()) > 5:
                nevermind()
                return task.done
            #if (toon.getY() - suit.getY()) < 2:
            #    suit.setFluidY(suit.getY() + 0.1)
            #    rt = True
            if suit.getZ() > -1.7:
                suit.setZ(suit.getZ() - 0.1)
                rt = True
            global runningHor
            if suit.getX() != toon.getX() and not runningHor:
                runningHor = True
                if suit.getX() != toon.getX():
                    speed = (self.cogChase.speedHorizontal * (math.sqrt(2.) / 2.))
                    distance = globalClock.getDt() * speed
                    if toon.getX() > suit.getX():
                        suit.setFluidX(suit.getX() + distance)
                    elif toon.getX() < suit.getX():
                        suit.setFluidX(suit.getX() - distance)
                    return task.again
            if rt:
                return task.again
            runningHor = False
            grab_toon()
            return task.done
        taskMgr.add(get_near_enough, 'get-near-enough')
        def _cancel():
            taskMgr.remove('get-near-enough')
            taskMgr.remove('fix-z-nvm')
            self.attacking = False
        self.accept('CogChaseAvoidingWall', _cancel)