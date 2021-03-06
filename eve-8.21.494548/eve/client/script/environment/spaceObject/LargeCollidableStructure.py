#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/spaceObject/LargeCollidableStructure.py
import spaceObject
import trinity
import blue
import timecurves
import uthread
from string import split
import sys

class LargeCollidableStructure(spaceObject.SpaceObject):
    __guid__ = 'spaceObject.LargeCollidableStructure'

    def Assemble(self):
        if self.model is not None:
            self.model.rotationCurve = None
        self.SetStaticRotation()
        if hasattr(self.model, 'ChainAnimationEx'):
            self.model.ChainAnimationEx('NormalLoop', 0, 0, 1.0)

    def Explode(self):
        if self.exploded:
            return False
        if self.model is None:
            self.LogWarn('Explode - No model')
            return
        self.exploded = True
        if not settings.user.ui.Get('explosionEffectsEnabled', 1):
            return False
        exlosionBasePath = 'res:/Emitter/tracerexplosion/'
        if self.radius > 3000.0:
            extraPath = 'StructureDeathRadius1500.blue'
        elif self.radius > 1500.0:
            extraPath = 'StructureDeathRadius1000.blue'
        elif self.radius > 900.0:
            extraPath = 'StructureDeathRadius500.blue'
        elif self.radius > 500.0:
            extraPath = 'StructureDeathRadius350.blue'
        else:
            extraPath = 'StructureDeathRadius200.blue'
        explosionURL = exlosionBasePath + extraPath
        gfx = trinity.Load(explosionURL.replace('.blue', '.red'))
        if gfx is None:
            return
        explodingObjectDisplay = [ x for x in gfx.curveSets if x.name == 'ExplodingObjectDisplay' ]
        if gfx.__bluetype__ != 'trinity.EveRootTransform':
            root = trinity.EveRootTransform()
            root.children.append(gfx)
            root.name = explosionURL
            gfx = root
        gfx.translationCurve = self
        self.explosionModel = gfx
        scene = sm.StartService('sceneManager').GetRegisteredScene('default')
        scene.objects.append(gfx)
        if len(explodingObjectDisplay):
            explodingObjectDisplay = explodingObjectDisplay[0]
            explodingObjectDisplay.bindings[0].destinationObject = self.model
            self.explosionDisplayBinding = explodingObjectDisplay.bindings[0]
        return True


exports = {'spaceObject.LargeCollidableStructure': LargeCollidableStructure}