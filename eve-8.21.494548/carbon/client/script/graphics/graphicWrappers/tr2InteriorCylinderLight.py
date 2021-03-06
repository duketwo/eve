#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/graphics/graphicWrappers/tr2InteriorCylinderLight.py
import util
import weakref
import geo2

class Tr2InteriorCylinderLight(util.BlueClassNotifyWrap('trinity.Tr2InteriorCylinderLight')):
    __guid__ = 'graphicWrappers.Tr2InteriorCylinderLight'

    @staticmethod
    def Wrap(triObject, resPath):
        Tr2InteriorCylinderLight(triObject)
        triObject.scene = None
        return triObject

    def AddToScene(self, scene):
        if self.scene and self.scene():
            scene.RemoveLight(self.scene())
        scene.AddLight(self)
        self.scene = weakref.ref(scene)

    def RemoveFromScene(self, scene):
        scene.RemoveLight(self)
        self.scene = None

    def _TransformChange(self, transform):
        self.OnTransformChange()

    def OnTransformChange(self):
        pass

    def SetPosition(self, position):
        self.position = position

    def GetPosition(self):
        return self.position

    def GetRotationYawPitchRoll(self):
        return geo2.QuaternionRotationGetYawPitchRoll(self.rotation)

    def SetRotationYawPitchRoll(self, ypr):
        self.rotation = geo2.QuaternionRotationSetYawPitchRoll(*ypr)

    def GetRadius(self):
        return self.radius

    def SetRadius(self, radius):
        self.radius = radius

    def GetLength(self):
        return self.length

    def SetLength(self, length):
        self.length = length

    def GetColor(self):
        return self.color[:3]

    def SetColor(self, color):
        self.color = (color[0],
         color[1],
         color[2],
         1)

    def GetFalloff(self):
        return self.falloff

    def SetFalloff(self, falloff):
        self.falloff = falloff