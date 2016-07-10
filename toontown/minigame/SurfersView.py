from panda3d.core import *
from direct.showbase.DirectObject import *
from direct.interval.IntervalGlobal import *

class SurfersView(DirectObject):
    def __init__(self, factory):
        self.factory = factory
        self.moduleIndex = 0
        
    def start(self):
        base.setBackgroundColor(0,0,0,0)
        modules = self.factory.getModules()
        for module in modules.values():
            module.getGeom().stash()
            module.getGeom().setColor(0,0,0,0)
        self.updateView()
        self.accept('FloorCollidedBySurfersPlayer',self.__handleFloorCollided)
        
    def restart(self, newIndex = 0):
        modules = self.factory.getModules()
        for module in modules.values():
            module.getGeom().stash()
            module.getGeom().setColor(0,0,0,0)
        self.moduleIndex = newIndex
        self.updateView()
        self.accept('FloorCollidedBySurfersPlayer',self.__handleFloorCollided)
        messenger.send('NewModule', [self.moduleIndex])
        
    def __handleFloorCollided(self, moduleId):
        modules = self.factory.getModules()
        if moduleId == modules[self.moduleIndex].id:
            return
        cur = modules[self.moduleIndex].getGeom()
        for module in modules.values():
            if module.id == moduleId:
                self.moduleIndex = modules.values().index(module)
        messenger.send('NewModule', [self.moduleIndex])
        Sequence(Wait(0.6),Func(cur.stash),Func(self.updateView)).start()
        
    def stop(self):
        self.ignore('FloorCollidedBySurfersPlayer')
        
    def updateView(self):
        modules = self.factory.getModules()
        cur = modules[self.moduleIndex].getGeom()
        cur.unstash()
        p = Parallel(cur.colorInterval(1,(255,255,255,1)))
        if modules.has_key(self.moduleIndex+1):
            next = modules[self.moduleIndex + 1].getGeom()
            next.unstash()
            p.append(next.colorInterval(1,(255,255,255,1)))
        if modules.has_key(self.moduleIndex + 2):
            afterNext = modules[self.moduleIndex + 2].getGeom()
            afterNext.unstash()
            p.append(afterNext.colorInterval(1,(255,255,255,1)))
        p.start()
        