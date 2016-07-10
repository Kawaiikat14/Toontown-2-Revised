from panda3d.core import *
from direct.showbase.DirectObject import *
from direct.interval.IntervalGlobal import *
import math, random

import SurfersSet, SurfersGlobals

EXIT_NODE = '**/EXIT'
ENTER_NODE = '**/ENTRANCE'
WALL_COLLISION_NAME = 'HallwayWallCollision_%s'
FLOOR_COLLISION_NAME = 'HallwayFloorCollision_%s'

class Pickup(DirectObject):
    def __init__(self, factory):
        self.factory = factory
        self.id = random.randint(0,1000)
        
    def getGeom(self):
        return self.geom
        
    def load(self):
        self.collectSound = base.loadSfx('phase_4/audio/sfx/SZ_DD_treasure.mp3')
        self.rotateInterval = self.geom.hprInterval(3.0, Point3(-360,0,0))
        self.rotateInterval.loop()
        self.__initCollisions()
       
    def unload(self):
        self.rotateInterval.finish()
        self.geom.removeNode()
        
    def __initCollisions(self):
        name = 'Pickup_%s' %self.id
        solid = CollisionSphere(0,0,0,0.2)
        solid.setTangible(0)
        cn = CollisionNode(name)
        cn.addSolid(solid)
        cn.setFromCollideMask(BitMask32(1))
        cn.setIntoCollideMask(BitMask32(1))
        self.sphereNodePath = self.geom.attachNewNode(cn)
        self.accept('enter%s' %name, self.__collected)
        
    def __collected(self, entry):
        self.collectSound.play()
        self.rewardPlayer()
        scaleiv = self.geom.scaleInterval(0.3,0)
        Sequence(scaleiv,Func(self.unload)).start()
        
class JellybeanPickup(Pickup):
    modelPath = 'phase_4/models/props/jellybean4'
    colors = SurfersGlobals.JellybeanPickupColors
    def __init__(self, factory):
        Pickup.__init__(self, factory)
        
    def load(self):
        self.geom = loader.loadModel(self.modelPath)
        self.geom.reparentTo(self.factory.getModule().getGeom())
        self.geom.setScale(7)
        self.geom.setColor(random.choice(self.colors))
        Pickup.load(self)
        
    def rewardPlayer(self):
        base.surfersMinigame.gui.jellybeans.add()
        
class SpeedupPickup(JellybeanPickup):
    colors = SurfersGlobals.SpeedupPickupColors
    def __init__(self, factory):
        JellybeanPickup.__init__(self, factory)
        
    def load(self):
        JellybeanPickup.load(self)
        self.geom.setScale(9)
        
    def rewardPlayer(self):
        base.surfersMinigame.gui.speedups.add()
        
class PickupFactory:
    pickups = {
        0:JellybeanPickup,
        1:SpeedupPickup
    }
    def __init__(self, module, key):
        self.module = module
        self.key = key
        self.picks = []
        
    def generate(self):
        if self.module.getObstaclesMapIndex() != -1:
            if SurfersSet.PickMaps.has_key(self.key):
                pickMaps = SurfersSet.PickMaps[self.key]
                _map = pickMaps[self.module.getObstaclesMapIndex()]
                for obj in _map:
                    k, pos, rang, dist, xIsY = obj
                    pos = Vec3(*pos)
                    if rang:
                        for i in range(rang):
                            pick = self.pickups[k](self)
                            pick.load()
                            if i != 0:
                                oy = self.picks[len(self.picks) -1].getGeom().getY()
                                ox = self.picks[len(self.picks) -1].getGeom().getX()
                                if not xIsY:
                                    pos.setY(oy + dist)
                                else:
                                    pos.setX(ox + dist)
                            pick.getGeom().setPos(pos)
                            self.picks.append(pick)
                    else:
                        pick = self.pickups[k](self)
                        pick.load()
                        pick.getGeom().setPos(pos)
                        self.picks.append(pick)
        
    def getModule(self):
        return self.module
        
    def getPickups(self):
        return self.picks
        
    def unload(self):
        for pick in self.picks:
            pick.unload()
        

class Obstacle:
    geoms = {
        0:('CashBotSafe',),
        1:('CBMetalCrate',),
        2:('CBWoodCrate',),
        3:('crates_A',),
        4:('crates_C1',),
        5:('crates_D',),
        6:('gears_A1',),
        7:('gears_B2',),
        8:('gears_C2',),
        9:('GoldBar',),
        10:('MoneyBag',),
        11:('pipes_A1',),
        12:('pipes_A2',),
        13:('shelf_A1',),
        14:('shelf_A1Gold',),
        15:('shelf_A1Money',),
        16:('shelf_A1MoneyBags',),
        17:('crates_E',)
    }
    def __init__(self, factory):
        self.factory = factory
        
    def load(self, geomId):
        geom = self.geoms[geomId]
        self.geom = loader.loadModel('phase_10/models/cashbotHQ/%s.bam' %geom)
        self.geom.reparentTo(self.factory.getModule().getGeom())
        
    def getGeom(self):
        return self.geom
        
    def setPHS(self, p, h, s):
        self.getGeom().setPos(*p)
        self.getGeom().setHpr(*h)
        self.getGeom().setScale(s)
        
class ObstacleFactory:
    def __init__(self, module, key):
        self.module = module
        self.key = key
        self.mapIndex = -1
        
    def generate(self):
        if SurfersSet.ObtMaps.has_key(self.key):
            obtMaps = SurfersSet.ObtMaps[self.key]
            _map = random.choice(obtMaps)
            self.mapIndex = obtMaps.index(_map)
            for obj in _map:
                k, pos, hpr, scale = obj
                obt = Obstacle(self)
                obt.load(k)
                obt.setPHS(pos, hpr, scale)
        
    def getModule(self):
        return self.module
        
    def getMapIndex(self):
        return self.mapIndex
        

class Module(DirectObject):
    wantObts = True
    wantPicks = True
    def __init__(self):
        self.id = random.randint(0,100000)
        
    def getExitJoint(self):
        return self.getGeom().find(EXIT_NODE)
        
    def getEnterJoint(self):
        return self.getGeom().find(ENTER_NODE)
        
    def getGeom(self):
        return self.geom
        
    def initCollisions(self):
        allColls = self.getGeom().findAllMatches('**/+CollisionNode')
        self.wallColls = []
        for coll in allColls:
            if str(coll).find('wall') != -1:
                self.wallColls.append(coll)

        if len(self.wallColls) > 0:
            for wallColl in self.wallColls:
                name = WALL_COLLISION_NAME %self.id
                wallColl.setName(name)
                wallColl.setY(wallColl.getY() - 1)
                
        self.floorColls = []
        for coll in allColls:
            if str(coll).find('floor') != -1:
                self.floorColls.append(coll)

        if len(self.floorColls) > 0:
            for floorColl in self.floorColls:
                name = FLOOR_COLLISION_NAME %self.id
                floorColl.setName(name)
        self.startEvents()
        
    def getFloorEvents(self):
        events = []
        for col in self.floorEvents:
            events.append('enter%s' %col.getName())
        return events
    
    def startEvents(self):
        for col in self.wallColls:
            self.accept('enter%s' %col.getName(), lambda x: self.stopAndSend('WallCollidedBySurfersPlayer', [x]))
        for col in self.floorColls:
            self.accept('enter%s' %col.getName(), lambda x: self.stopAndSend('FloorCollidedBySurfersPlayer', [self.id]))
        
    def stopEvents(self):
        for col in self.wallColls:
            self.ignore('enter%s' %col.getName())
        for col in self.floorColls:
            self.ignore('enter%s' %col.getName())
            
    def stopAndSend(self, msg, args):
        self.handleFloorCollided()
        self.stopEvents()
        messenger.send(msg, args)
        
    def handleFloorCollided(self): pass
        
    def load(self):
        self.initCollisions()
        if self.wantObts:
            self.obstacles = ObstacleFactory(self, self.key)
            self.obstacles.generate()
        if self.wantPicks:
            self.pickups = PickupFactory(self, self.key)
            self.pickups.generate()
            
    def unload(self):
        self.geom.removeNode()
        if self.wantPicks:
            self.pickups.unload()
        
    def getObstaclesMapIndex(self):
        return self.obstacles.getMapIndex()

class Begin(Module):
    geoms = { # Do not add nor remove
        3:('ZONE03a',Vec3(0,-3,0)),
    }
    def __init__(self, gameFactory):
        Module.__init__(self)
        self.gameFactory = gameFactory
        self.jointNode = 0
        
    def load(self):
        self.key = random.choice(self.geoms.keys())
        geom = self.geoms[self.key][0]
        self.geom = loader.loadModel('phase_10/models/cashbotHQ/%s.bam' %geom)
        self.geom.reparentTo(render)
        Module.load(self)
        
    def posAvatar(self, av):
        if type(av) == type(base.surfersMinigame.player):
            av = av.getAvatar()
        av.setPos(self.geoms[self.key][1])
        av.setHpr(0,0,0)
        if av.getParent() != render:
            av.reparentTo(render)
        
    def posSuit(self, suit):
        if type(suit) == type(base.surfersMinigame.cog):
            suit = suit.getSuit()
        suit.setPos(self.geoms[self.key][1])
        suit.setY(base.surfersMinigame.player.getAvatar().getY() - base.surfersMinigame.y_distance_cog)
        suit.setZ(SurfersGlobals.CogHeight)
        if suit.getParent() != render:
            suit.reparentTo(render)
            
class Hallway(Module):
    geoms = {
        4:('ZONE04a',),
        13:('ZONE13a',),
        15:('ZONE15a',),
    }
    def __init__(self, factory):
        Module.__init__(self)
        self.factory = factory
    
    def load(self):
        self.key = random.choice(self.geoms.keys())
        geom = self.geoms[self.key][0]
        self.geom = loader.loadModel('phase_10/models/cashbotHQ/%s.bam' %geom)
        prvMod = self.factory.getPrevious()
        prvModJoint = prvMod.getExitJoint()
        modJoint = self.geom.find(ENTER_NODE)
        tempNode = prvModJoint.attachNewNode('tempRotNode')
        self.geom.reparentTo(tempNode)
        self.geom.clearMat()
        self.geom.setPos(Vec3(0) - modJoint.getPos(self.geom))
        tempNode.setH(-modJoint.getH(prvModJoint))
        self.geom.wrtReparentTo(prvMod.getGeom().getParent())
        tempNode.removeNode()
        self.doorFrame = loader.loadModel('phase_10/models/cashbotHQ/DoorFrame.bam')
        self.doorFrame.reparentTo(modJoint)
        Module.load(self)
        
    def posAvatar(self, av):
        av.setPos(self.geom.getPos())
        av.setHpr(0,0,0)
        av.setY(self.geom.find(ENTER_NODE).getY(render))
        
    def posSuit(self, suit):
        suit.setPos(self.geom.getPos())
        suit.setY(base.surfersMinigame.player.getAvatar().getY() - base.surfersMinigame.y_distance_cog)
        suit.setZ(SurfersGlobals.CogHeight)
            
class HallwayFactory:
    Min = SurfersGlobals.MinHallways
    Max = SurfersGlobals.MaxHallways
    def __init__(self, factory):
        self.factory = factory
    
    def generate(self):
        total = random.randint(self.Min, self.Max)
        for i in range(total):
            m = Hallway(self)
            m.load()
            self.factory.addModule(m)
        
    def getPrevious(self):
        return self.factory.getLastModule()
        
class End(Hallway):
    geoms = { # Do not add nor remove
        15:('ZONE15a',),
    }
    wantObts = False
    wantPicks = False
    winSoundPath = 'phase_4/audio/sfx/mg_surfers_win.mp3'
    def __init__(self, factory):
        Hallway.__init__(self, factory)
        self.factory = factory
        
    def load(self):
        Hallway.load(self)
        
    def unload(self):
        Hallway.unload(self)
        print 'unload!'
        
    def handleFloorCollided(self):
        base.surfersMinigame.stopAll()
        base.surfersMinigame.player.win = True
        camera.reparentTo(self.geom)
        camera.setPos(50,-10,4)
        camera.setHpr(80,5,0)
        avatar = base.surfersMinigame.player.getAvatar()
        avatar.loop('run')
        suit = base.surfersMinigame.cog.getSuit()
        suit.setPos(self.geom,-60,0,SurfersGlobals.CogHeight)
        avatar.setPos(self.geom,-40,0,0)
        footstep = base.loadSfx('phase_3.5/audio/sfx/AV_footstep_runloop.ogg')
        footstep.setLoop(1)
        footstep.setVolume(1.3)
        avRun = Sequence(Func(footstep.play),avatar.posInterval(3,(60,0,0),other=self.geom),
                            Func(avatar.hide),Func(footstep.stop))
        suitMissWall = suit.posInterval(0.8,(-45,0,-1),other=self.geom)
        suitFixHeight = suit.posInterval(0.8,(-35,0,SurfersGlobals.CogHeight),other=self.geom)
        hurry = suit.posInterval(1.3,(40,0,18),other=self.geom)
        propSound = base.loadSfx('phase_4/audio/sfx/TB_propeller.ogg')
        propSound.setVolume(1.5)
        propSound.setLoop(1)
        _break = base.loadSfx('phase_6/audio/sfx/KART_Skidding_On_Asphalt.ogg')
        def posCamera():
            camera.setPos(-40,-10,4)
            camera.setHpr(-80,5,0)
        def animSuit():
            suit.loop("flail",fromFrame=24)
        def explode():
            def createKapowExplosionTrack(parent, explosionPoint = None, scale = 1.0):
                explosionTrack = Sequence()
                explosion = loader.loadModel('phase_3.5/models/props/explosion.bam')
                explosion.setBillboardPointEye()
                explosion.setDepthWrite(False)
                if not explosionPoint:
                    explosionPoint = (0,-3.6,2.1)
                explosionTrack.append(Func(explosion.reparentTo, parent))
                explosionTrack.append(Func(explosion.setPos, explosionPoint))
                explosionTrack.append(Func(explosion.setScale, 0.4 * scale))
                explosionTrack.append(Wait(0.6))
                explosionTrack.append(Func(suit.stash))
                explosionTrack.append(Func(explosion.removeNode))
                return explosionTrack
            explosion = createKapowExplosionTrack(suit)
            explosionSound = base.loadSfx('phase_3.5/audio/sfx/ENC_cogfall_apart.ogg')
            Sequence(Func(explosion.start),Func(propSound.stop),Func(explosionSound.play)).start()
        def _finish():
            winSound = base.loadMusic(self.winSoundPath)
            winSound.play()
            base.surfersMinigame.finished()
            
        self.movie = Sequence(Func(avRun.start),Wait(1.5),Func(propSound.play),suitMissWall,suitFixHeight,
                        Func(hurry.start),Wait(0.5),Func(posCamera),Func(animSuit),Func(_break.play),
                        Wait(0.6),Func(explode),Wait(1.4),Func(_finish))
        # Avoid crash
        try:
            self.movie.start()
        except:
            base.surfersMinigame.notify.warning('AVOID_CRASH: FINAL_MOVIE')
        
        
        
        

class SurfersFactory:
    def __init__(self):
        self.lastModule = None
        self.modules = {}
        
    def generate(self):
        self.begin = Begin(self)
        self.begin.load()
        self.addModule(self.begin)
        self.hallwayFactory = HallwayFactory(self)
        self.hallwayFactory.generate()
        self.end = End(self.hallwayFactory)
        self.end.load()
        self.addModule(self.end)
        
    def unload(self):
        for module in self.modules.values():
            module.unload()
        
    def stopEvents(self):
        for module in self.modules.values():
            module.stopEvents()
            
    def startEvents(self):
        for module in self.modules.values():
            module.startEvents()
            
    def isWallCollision(self, wallName):
        return (wallName.find(WALL_COLLISION_NAME.split('_')[0]) != -1)
        
    def addModule(self, mdl):
        self.modules[len(self.modules)] = mdl
        
    def getModules(self):
        return self.modules
        
    def getLastModule(self):
        return self.modules[len(self.modules) - 1]
        
    def addPlayer(self, player):
        self.begin.posAvatar(player)
        
    def addCog(self, cog):
        self.begin.posSuit(cog)