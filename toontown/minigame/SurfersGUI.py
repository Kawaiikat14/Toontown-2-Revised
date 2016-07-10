from panda3d.core import *
from direct.gui.DirectGui import *
from direct.interval.IntervalGlobal import *
from direct.showbase.Transitions import *
import SurfersGlobals

from toontown.toonbase import ToontownGlobals, TTLocalizer
from toontown.effects import DustCloud

class SurfersPoster:
    SUTextZ = 0.550
    SUTextX = -0.2
    def __init__(self):
        self.parent = aspect2d
        self.hold = {'slideUp':[]}
        self.curSlideUp = False
        
    def prepare(self):
        font1 = ToontownGlobals.getToonFont()
        slideUpTextNd = TextNode('slideUpText')
        slideUpTextNd.setFont(font1)
        slideUpTextNd.setTextColor(255,255,255,1)
        slideUpTextNd.setShadowColor(0,0,0,1)
        slideUpTextNd.setShadow(0.1,0.1)
        self.slideUpText = self.parent.attachNewNode(slideUpTextNd)
        self.slideUpText.setPos(self.SUTextX,0,self.SUTextZ)
        self.slideUpText.setScale(0)
        self.slideUpText.setR(-10)
        self.slideUpText.hide()
        
    def unload(self):
        self.slideUpText.removeNode()
        
    def slideUp(self, text, duration=1.0):
        if self.curSlideUp:
            self.putOnHold('slideUp',(text,duration))
            return
        self.curSlideUp = True
        self.slideUpText.setScale(0)
        self.slideUpText.show()
        self.slideUpText.node().setText(text)
        scaleUp = self.slideUpText.scaleInterval(0.5, (0.1,0.1,0.1))
        slideUp = Parallel(self.slideUpText.posInterval(0.4, (self.SUTextX,0,1)),
                            self.slideUpText.scaleInterval(0.4, (0,0,0)))
        def done():
            if self.slideUpText.isEmpty(): return
            self.slideUpText.hide()
            self.slideUpText.hide()
            self.slideUpText.setZ(self.SUTextZ)
            self.curSlideUp = False
            self.proccessHold('slideUp')
        seq = Sequence(scaleUp, Wait(duration), slideUp, Func(done))
        try:
            seq.start()
        except:
            base.surfersMinigame.notify.warning('AVOID_CRASH: slideUpText')
        
    def putOnHold(self, _type, args):
        self.hold[_type].append(args)
        
    def proccessHold(self,_type):
        for item in self.hold[_type]:
            del self.hold[_type][self.hold[_type].index(item)]
            self.slideUp(*item)
            break
            
class SurfersMap(NodePath):
    BlockImageDir = 'phase_4/maps/map_block.png'
    def __init__(self, parent):
        NodePath.__init__(self, 'SurfersMap')
        NodePath.reparentTo(self, parent)
        self.curBlockId = 0
    
    def load(self, numBlocks):
        self.blocks = {}
        self.lastBlockZ = 0.030
        for i in range(numBlocks):
            block = OnscreenImage(image=self.BlockImageDir,parent=self)
            block.setTransparency(TransparencyAttrib.MAlpha)
            block.setScale(0.030)
            block.setX(-.1)
            block.setZ(self.lastBlockZ + 0.060)
            self.blocks[len(self.blocks)] = block
            self.lastBlockZ = block.getZ()   
        self.title = OnscreenText(text=TTLocalizer.SurfersMap,font=ToontownGlobals.getToonFont(),parent=self)
        self.title.setPos(0,1)
        self.title.setR(-15)
        self.title.node().setTextColor(255,255,255,1)
        self.title.node().setShadowColor(0,0,0,1)
        self.title.node().setShadow(0.1,0.1)
        base.accept('NewModule', self.__handleNewBlock)
        
    def unload(self):
        self.removeNode()
        
    def __handleNewBlock(self, blockId):
        if blockId != self.curBlockId:
            self.blocks[self.curBlockId].setColor(0,1,0,1)
            self.curBlockId = blockId
            self.blocks[self.curBlockId].setColor(1,1,0,1)
            
class SurfersRadar(NodePath):
    proximityAlertSound = 'phase_4/audio/sfx/mg_surfers_radar.mp3'
    radarImageDir = 'phase_4/maps/radar_bg.png'
    def __init__(self, parent):
        NodePath.__init__(self, 'SurfersDistanceMap')
        NodePath.reparentTo(self, parent)
        self.alertingProximity = False
        
    def load(self):
        self.title = OnscreenText(text=TTLocalizer.SurfersRadar,font=ToontownGlobals.getToonFont(),parent=self)
        self.title.setPos(0.270,-0.660)
        self.title.node().setTextColor(255,255,255,1)
        self.title.node().setShadowColor(0,0,0,1)
        self.title.node().setShadow(0.1,0.1)
        icon = loader.loadModel('phase_6/models/karting/race_mapspot')
        icon.setScale(0.1)
        self.radarImage = OnscreenImage(image=self.radarImageDir,parent=self)
        self.radarImage.setTransparency(TransparencyAttrib.MAlpha)
        self.radarImage.setScale(0.290)
        self.radarImage.setPos(0.3,0,-0.320)
        self.toon = icon.copyTo(self.radarImage)
        self.toon.setColor(0,1,0,1)
        self.cog = icon.copyTo(self.radarImage)
        self.cog.setColor(1,0,0,1)
        self.proximitySound = base.loadSfx(self.proximityAlertSound)
        self.proximitySound.setLoop(1)
        self.proximitySound.setVolume(0.3)
        
        taskMgr.add(self.__updateDistance, 'update-map-distance')
        
    def unload(self):
        taskMgr.remove('update-map-distance')
        self.removeNode()
        self.proximitySound.stop()
        
    def startProximityAlert(self):
        self.alertingProximity = True
        self.proximitySound.play()
        blink1 = self.radarImage.colorInterval(1,(0.20,0.40,1,1))
        blink2 = self.radarImage.colorInterval(1,(1,1,1,1))
        self.radarBlinkInterval = Sequence(blink1, blink2)
        self.radarBlinkInterval.loop()
        
    def stopProximityAlert(self):
        self.alertingProximity = False
        self.proximitySound.stop()
        self.radarBlinkInterval.finish()
        
    def __updateDistance(self, task):
        if not hasattr(base.surfersMinigame, 'player'):
            base.surfersMinigame.notify.warning('AVOID_CRASH: Radar: Disable and we didn\'t notice')
        dtnm = (base.surfersMinigame.player.getAvatar().getY() - base.surfersMinigame.cog.getSuit().getY())
        dt = globalClock.getDt() * dtnm
        dt2d = (dt * 0.1) * 0.2
        self.cog.setZ(-dt2d)
        
        if dtnm < 15 and not self.alertingProximity:
            self.startProximityAlert()
        elif dtnm > 15 and self.alertingProximity:
            self.stopProximityAlert()
        return task.again
        
class SurfersJellybeansGUI(NodePath):
    def __init__(self):
        NodePath.__init__(self, 'SurfersJellybeans')
        NodePath.reparentTo(self, base.a2dTopRight)
        
    def load(self):
        self.setPos(-0.5,0,-0.115)
        self.jbs = OnscreenText(text='0',font=ToontownGlobals.getToonFont(),parent=self)
        self.jbs.node().setTextColor(1,1,0,1)
        self.jbs.node().setShadowColor(0,0,0,1)
        self.jbs.node().setShadow(0.1,0.1)
        self.jbs.setScale(0.1)
        self.icon = loader.loadModel('phase_4/models/minigames/jellyBean')
        self.icon.reparentTo(self)
        self.icon.setScale(0.1)
        self.icon.setPos(-.090,0,0.010)
        
    def add(self, qnt=1):
        self.jbs.setText(str(int(self.jbs.getText()) + qnt))
        base.surfersMinigame.updateJellybeans(int(self.jbs.getText()))
        
    def subt(self, qnt=1):
        self.jbs.setText(str(int(self.jbs.getText()) - qnt))
        base.surfersMinigame.updateJellybeans(int(self.jbs.getText()))
        
    def unload(self):
        self.removeNode()
        
class SurfersSpeedupsGUI(NodePath):
    firstTime = True
    def __init__(self):
        NodePath.__init__(self, 'SurfersSpeedups')
        NodePath.reparentTo(self, base.a2dTopRight)
        
    def load(self):
        self.setPos(-0.8,0,-0.115)
        self.ups = OnscreenText(text='0',font=ToontownGlobals.getToonFont(),parent=self)
        self.ups.node().setTextColor(1,1,0,1)
        self.ups.node().setShadowColor(0,0,0,1)
        self.ups.node().setShadow(0.1,0.1)
        self.ups.setScale(0.1)
        self.icon = loader.loadModel('phase_4/models/minigames/jellyBean')
        self.icon.setColor(SurfersGlobals.SpeedupPickupColors[0])
        self.button = DirectButton(image=self.icon,relief=None,parent=self,command=self.__useSpeed)
        self.button.reparentTo(self)
        self.button.setScale(0.1)
        self.button.setPos(-.080,0,0.010)
        self.arrow = loader.loadModel('phase_3/models/props/arrow')
        self.arrow.reparentTo(self)
        self.arrow.setScale(0.130)
        self.arrow.setR(-70)
        self.arrow.setPos(-0.090,0,-0.1)
        self.arrow.hide()
        
    def add(self,qnt=1):
        self.ups.setText(str(int(self.ups.getText()) + qnt))
        if self.firstTime:
            self.arrow.show()
            a = self.arrow
            z = (a.getZ() + 0.050)
            up = self.arrow.posInterval(0.5,(a.getX(),0,z))
            down = self.arrow.posInterval(0.5,(a.getX(),0,z - 0.050))
            scale = self.arrow.scaleInterval(0.8,(0,0,0))
            def fin():
                self.arrow.hide()
                self.firstTime = False
            Sequence(up,down,up,down,up,down,scale,Func(fin)).start()
            
    def subt(self, qnt=1):
        self.ups.setText(str(int(self.ups.getText()) - qnt))
        
    def __useSpeed(self):
        speeds = int(self.ups.getText())
        if speeds > 0:
            speeds -= 1
            self.ups.setText(str(speeds))
            self.hide()
            player = base.surfersMinigame.player
            av = player.getAvatar()
            def getDustCloudIval():
                dustCloud = DustCloud.DustCloud(fBillboard=0, wantSound=1)
                dustCloud.setBillboardAxis(2.0)
                dustCloud.setZ(3)
                dustCloud.setScale(0.4)
                dustCloud.createTrack()
                return Sequence(Func(dustCloud.reparentTo, av), dustCloud.track, Func(dustCloud.destroy), name='dustCloadIval')
            def normalizeSpeed(task):
                def ivalDone():
                    av.clearCheesyEffect()
                    player.controller.setSpeeds(SurfersGlobals.ToonSpeedForward, SurfersGlobals.ToonSpeedHorizontal)
                    base.surfersMinigame.theme.setPlayRate(1)
                    try: self.show()
                    except AssertionError: pass # The NP was removed and we didn't know
                self.normalizeSeq = Sequence(Func(getDustCloudIval().start),Wait(0.5),Func(ivalDone))
                self.normalizeSeq.start()
            def applySpeed():
                av.applyCheesyEffect(ToontownGlobals.CETransparent,0.5) # CEVirtual is fucked as hell
                newSpeed = SurfersGlobals.SpeedupToonSpeed
                player.controller.setSpeeds(newSpeed[0],newSpeed[1])
                base.surfersMinigame.poster.slideUp(TTLocalizer.SurfersSpeedup)
                base.surfersMinigame.theme.setPlayRate(1.5)
                taskMgr.doMethodLater(SurfersGlobals.SpeedupEffectDuration,normalizeSpeed, 'normalize-speed')
            dust = getDustCloudIval()
            Sequence(Func(dust.start),Wait(0.5),Func(applySpeed)).start()
            
    def unload(self):
        self.removeNode()
        taskMgr.remove('normalize-speed')
        if hasattr(self, 'normalizeSeq'):
            self.normalizeSeq.finish()
        av = base.surfersMinigame.player.getAvatar()
        av.clearCheesyEffect()
        
class ScorePanel(DirectFrame):
    def __init__(self, avId, avName):
        self.avId = avId
        if base.cr.doId2do.has_key(self.avId):
            self.avatar = base.cr.doId2do[self.avId]
        else:
            self.avatar = None
        DirectFrame.__init__(self, relief=None, image_color=ToontownGlobals.GlobalDialogColor, image_scale=(0.4, 1.0, 0.24), image_pos=(0.0, 0.1, 0.0))
        self['image'] = DGG.getDefaultDialogGeom()
        self.scoreText = DirectLabel(self, relief=None, text='0', text_scale=TTLocalizer.MASPscoreText, pos=(0.1, 0.0, -0.09))
        self.nameText = DirectLabel(self, relief=None, text=avName, text_scale=TTLocalizer.MASPnameText, text_pos=(0.0, 0.06), text_wordwrap=7.5, text_shadow=(1, 1, 1, 1))
        self.spotText = OnscreenText(pos=(-0.080,-0.05),scale=TTLocalizer.MASPscoreText,parent=self)
        self.spotText.node().setShadow(0.1,0.1)
        self.spotText.node().setShadowColor(0,0,0,1)
        self.show()
        return

    def cleanup(self):
        del self.scoreText
        del self.nameText
        del self.spotText
        self.destroy()

    def setScore(self, score):
        self.scoreText['text'] = str(score)

    def getScore(self):
        return int(self.scoreText['text'])

    def makeTransparent(self, alpha):
        self.setTransparency(1)
        self.setColorScale(1, 1, 1, alpha)
        
class SurfersScore:
    spotColors = {
        1:(0,1,0,1),
        2:(1,1,0,1),
        3:(1,0,0,1)
    }
    def __init__(self, avIds):
        self.avIds = avIds
        self.scorePanels = {}
        self.lastPanelX = 0
    
    def load(self):
        for avId in self.avIds:
            av = base.cr.doId2do.get(avId)
            if av and (av.doId != localAvatar.doId):
                panel = ScorePanel(av.doId, av.getName())
                panel.reparentTo(base.a2dBottomLeft)
                panel.setZ(0.2)
                panel.setX(self.lastPanelX + 0.560)
                self.scorePanels[av.doId] = panel
                self.lastPanelX = panel.getX()
                
    def removePlayer(self, avId):
        if avId in self.avIds:
            self.scorePanels[avId].cleanup()
            del self.scorePanels[avId]
            self.avIds.pop(self.avIds.index(avId))
                
    def unload(self):
        for panel in self.scorePanels.values():
            panel.cleanup()
            
    def updatePlayerScore(self, avId, score):
        if avId in self.scorePanels.keys():
            self.scorePanels[avId].setScore(score)
            
    def setSpotWinner(self, avId, spot):
        if avId in self.scorePanels.keys():
            panel = self.scorePanels[avId]
            panel.spotText.setText(str(spot))
            panel.spotText.node().setTextColor(self.spotColors[spot])

class SurfersGUI:
    def __init__(self):
        pass
        
    def load(self):
        self.map = SurfersMap(base.a2dBottomRight)
        numBlocks = len(base.surfersMinigame.factory.getModules())
        self.map.load(numBlocks)
        self.radar = SurfersRadar(base.a2dTopLeft)
        self.radar.load()
        self.jellybeans = SurfersJellybeansGUI()
        self.jellybeans.load()
        self.speedups = SurfersSpeedupsGUI()
        self.speedups.load()
        
    def unload(self):
        self.map.unload()
        self.radar.unload()
        self.jellybeans.unload()
        self.speedups.unload()
        
    def createScoresPanel(self, avIds):
        self.score = SurfersScore(avIds)
        self.score.load()
        
    def removeScoresPanel(self):
        self.score.unload()
            
class SurfersEffects(Transitions):
    IrisModelName = "models/misc/iris.egg"
    FadeModelName = "models/misc/fade.egg"
    def __init__(self):
        Transitions.__init__(self, loader)
        self.curEffect = None
        
    def prepare(self):
        pass
        
        