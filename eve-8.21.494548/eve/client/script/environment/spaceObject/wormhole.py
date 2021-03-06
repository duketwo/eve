#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/wormhole.py
import spaceObject
import blue
import uthread

class Wormhole(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.Wormhole'
    __notifyevents__ = ['OnSlimItemChange']

    def __init__(self):
        spaceObject.SpaceObject.__init__(self)
        sm.RegisterNotify(self)

    def Release(self, origin = None):
        sm.UnregisterNotify(self)
        spaceObject.SpaceObject.Release(self)

    def OnSlimItemChange(self, oldItem, newItem):
        if oldItem.itemID != self.id:
            return
        if oldItem.wormholeSize != newItem.wormholeSize:
            self.LogInfo('Wormhole size has changed. Updating graphics')
            uthread.pool('wormhole:SetWormholeSize', self.SetWormholeSize, oldItem.wormholeSize, newItem.wormholeSize)
        if oldItem.wormholeAge != newItem.wormholeAge:
            self.SetWobbleSpeed()

    def SetWormholeSize(self, oldSize, newSize):
        self.PlaySound('worldobject_wormhole_shrinking_play')

        def Lerp(min, max, s):
            return min + s * (max - min)

        self.SetWobbleSpeed(10.0)
        self.LogInfo('Setting wormhole size from', oldSize, 'to', newSize)
        blue.pyos.synchro.SleepSim(1000)
        if self.model is None:
            return
        i = 0
        time = 2000.0
        start, ndt = blue.os.GetSimTime(), 0.0
        while ndt < 1.0:
            ndt = max(ndt, min(blue.os.TimeDiffInMs(start, blue.os.GetSimTime()) / time, 1.0))
            val = Lerp(oldSize, newSize, ndt)
            sz = val
            self.model.scaling = (sz, sz, sz)
            blue.pyos.synchro.Yield()
            i += 1
            if self.model is None:
                return

        blue.pyos.synchro.SleepSim(2000)
        self.SetWobbleSpeed()

    def SetWobbleSpeed(self, spd = None):
        if self.model is None:
            return
        curve = self.FindCurveSet('Wobble')
        slimItem = sm.StartService('michelle').GetItem(self.id)
        if curve is None or slimItem is None:
            return
        defaultWobble = 1.0
        if slimItem.wormholeAge == 2:
            defaultWobble += 4.0
        elif slimItem.wormholeAge == 1:
            defaultWobble += 1.0
        spd = spd or defaultWobble
        self.LogInfo('Setting Wobble speed to', spd)
        curve.scale = spd

    def Assemble(self):
        sceneManager = sm.StartService('sceneManager')
        slimItem = sm.StartService('michelle').GetItem(self.id)
        sz = slimItem.wormholeSize
        self.LogInfo('Wormhole - Assemble : Setting wormhole size to', sz)
        scene = cfg.graphics.Get(slimItem.nebulaType).graphicFile
        texturePath = sceneManager.DeriveTextureFromSceneName(scene)
        self.LogInfo('Wormhole - Assemble : wormholeSize =', slimItem.wormholeSize, ', nebulaType =', slimItem.nebulaType, ',wormholeAge =', slimItem.wormholeAge)
        self.LogInfo('I will hand this wormhole the following texture:', texturePath)
        otherSide = self.model.Find('trinity.TriTextureCubeParameter')[0]
        otherSide.resourcePath = texturePath
        self.model.scaling = (sz, sz, sz)
        self.SetWobbleSpeed()
        self.model.boundingSphereRadius = self.radius
        isCloseToCollapse = sz < 1.0
        if isCloseToCollapse:
            ambient = 'worldobject_wormhole_unstable_play'
        else:
            ambient = 'worldobject_wormhole_ambience_play'
        self.SetupAmbientAudio(unicode(ambient))

    def FindCurveSet(self, name):
        if self.model is None:
            return
        for b in self.model.Find('trinity.TriCurveSet'):
            if b.name == name:
                return b

    def Explode(self):
        if self.exploded:
            return False
        self.exploded = True
        if self.model is None:
            return False
        uthread.worker('wormhole:PlayDeath', self.PlayDeath)
        return 2000

    def PlayDeath(self):
        self.PlaySound('worldobject_wormhole_collapse_play')
        self.SetWobbleSpeed(20.0)
        blue.pyos.synchro.SleepSim(1000)
        coll = self.FindCurveSet('Collapse')
        if coll:
            coll.Play()

    def LoadModel(self, fileName = None, loadedModel = None):
        slimItem = sm.StartService('michelle').GetItem(self.id)
        self.LogInfo('Wormhole - LoadModel', slimItem.nebulaType)
        fileName = cfg.invtypes.Get(slimItem.typeID).GraphicFile()
        spaceObject.SpaceObject.LoadModel(self, fileName)

    def PlaySound(self, event):
        if self.model is None:
            return
        if hasattr(self.model, 'observers'):
            for obs in self.model.observers:
                obs.observer.SendEvent(unicode(event))
                return

        self.LogError("Wormhole can't play sound. Sound observer not found")


exports = {'spaceObject.Wormhole': Wormhole}