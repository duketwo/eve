#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/environment/effects/Warp.py
import blue
import effects
import uthread
import destiny
import trinity
import log
from math import cos, pow, sqrt
from foo import Vector3
import geo2

class Warping(effects.ShipEffect):
    __guid__ = 'effects.Warping'

    def Prepare(self):
        shipID = self.GetEffectShipID()
        self.debugStopRequested = False
        if shipID != session.shipid:
            self.debugStopRequested = True
            sm.StartService('FxSequencer').OnSpecialFX(shipID, None, None, None, None, [], 'effects.Warping', 0, 0, 0)
            return
        effects.ShipEffect.Prepare(self)
        self.AlignToDirection()
        self.debugPrepared = True

    def Start(self, duration):
        if self.gfx is None:
            return
        self.gfx.display = False
        self.hasExploded = False
        self.hasWind = False
        self.hasMoreCollisions = True
        self.findNext = True
        effects.ShipEffect.Start(self, duration)
        bp = sm.StartService('michelle').GetBallpark()
        shipID = self.GetEffectShipID()
        shipBall = bp.GetBall(shipID)
        self.shipBall = shipBall
        self.shipModel = getattr(shipBall, 'model', None)
        slimItem = bp.GetInvItem(shipID)
        self.warpSpeedModifier = sm.StartService('godma').GetTypeAttribute(slimItem.typeID, const.attributeWarpSpeedMultiplier)
        if self.warpSpeedModifier is None:
            self.warpSpeedModifier = 1.0
        space = sm.GetService('space')
        self.SetupTunnelBindings()
        self.nextCollision = None
        self.insideSolid = False
        self.destination = space.warpDestinationCache[3]
        self.collisions = []
        self.collisions = self.GetWarpCollisions(shipBall)
        self.ControlFlow('NextCollision')
        uthread.worker('FxSequencer::WarpEffectLoop', self.WarpLoop, shipBall)
        self.debugStarted = True

    def AddToScene(self, effect):
        scene = self.fxSequencer.GetScene()
        scene.warpTunnel = effect

    def RemoveFromScene(self, effect):
        scene = self.fxSequencer.GetScene()
        scene.warpTunnel = None

    def RecycleOrLoad(self, resPath):
        return blue.resMan.GetObject(resPath)

    def ControlFlow(self, event):
        if event == 'ExitPlanet':
            scene = self.fxSequencer.GetScene()
            for each in scene.lensflares:
                each.display = True

            self.nextCollision[0].display = True
            self.exitPlanetBinding.scale = 0
            self.exitPlanetEventCurve.Stop()
            if self.hasMoreCollisions:
                self.nextPlanetBinding.scale = 1
                self.nextPlanetEventCurve.Play()
                self.nextPlanetBinding.sourceObject.expr = '-input1 / input2'
        elif event == 'NextCollision':
            self.nextPlanetBinding.scale = 0
            self.nextPlanetEventCurve.Stop()
            res = self.SetupNextCollision()
            if res == False:
                self.nextPlanetBinding.scale = 1
                self.nextPlanetEventCurve.Play()
                self.nextPlanetBinding.sourceObject.expr = 'input2 / input1'
            else:
                self.enterPlanetBinding.scale = 1
                self.enterPlanetEventCurve.Play()
        elif event == 'EnterPlanet':
            scene = self.fxSequencer.GetScene()
            for each in scene.lensflares:
                each.display = False

            self.nextCollision[0].display = False
            if self.nextCollision[0].radius < 450000:
                delta = 1
                self.nextCollision = (self.nextCollision[0], delta)
                self.collisionCurve.input1 = 1.1 * delta / 10000.0
            self.enterPlanetBinding.scale = 0
            self.enterPlanetEventCurve.Stop()
            self.exitPlanetBinding.scale = 1
            self.exitPlanetEventCurve.Play()

    def SetupTunnelBindings(self):
        self.curveSet = [ x for x in self.gfx.curveSets if x.name == 'SpeedBinding' ][0]
        for binding in self.curveSet.bindings:
            self.speedBinding = binding
            binding.sourceObject = self.shipModel.speed
            binding.scale *= 1.0 / (3.0 * const.AU * self.warpSpeedModifier)

        self.curveSet.Play()
        setup = [ x for x in self.gfx.curveSets if x.name == '_Setup_' ][0]
        self.setup = setup
        self.collisionCurve = [ x for x in setup.curves if x.name == '_global' ][0]
        self.xout = [ x for x in setup.curves if x.name == '_xPointOut' ][0]
        extra = [ x for x in self.gfx.curveSets if getattr(x, 'name', None) == '_Extra_' ][0]
        first = [ x for x in self.gfx.curveSets if getattr(x, 'name', None) == '_First_' ][0]
        self.distanceTracker = first.curves.Find('trinity.Tr2DistanceTracker')[0]
        self.distanceTraveled = [ x for x in extra.curves if getattr(x, 'name', None) == '_mov' ][0]
        self.fadeInLength = [ x for x in extra.curves if getattr(x, 'name', None) == '_fadeLength' ][0]
        self.eventb = [ x for x in self.gfx.curveSets if x.name == 'EventBindings' ][0]
        eventBindings = [ x for x in self.gfx.curveSets if x.name == 'EventBindings' ][0].bindings
        for binding in eventBindings:
            if binding.name == 'enterPlanetBinding':
                self.enterPlanetBinding = binding
            elif binding.name == 'exitPlanetBinding':
                self.exitPlanetBinding = binding
            elif binding.name == 'nextPlanetBinding':
                self.nextPlanetBinding = binding

        self.enterPlanetEventCurve = [ x for x in self.gfx.curveSets if x.name == 'enterPlanet' ][0]
        self.exitPlanetEventCurve = [ x for x in self.gfx.curveSets if x.name == 'exitPlanet' ][0]
        self.nextPlanetEventCurve = [ x for x in self.gfx.curveSets if x.name == 'nextCollision' ][0]
        self.enterPlanetBinding.scale = 0
        self.exitPlanetBinding.scale = 0
        self.nextPlanetBinding.scale = 0
        self.enterPlanetEventCurve.Stop()
        self.exitPlanetEventCurve.Stop()
        self.nextPlanetEventCurve.Stop()
        self.exitPlanetEventCurve.curves[0].AddKey(0.0, u'Start')
        self.exitPlanetEventCurve.curves[0].AddCallableKey(1.0, self.ControlFlow, ('ExitPlanet',))
        self.enterPlanetEventCurve.curves[0].AddKey(0.0, u'Start')
        self.enterPlanetEventCurve.curves[0].AddCallableKey(1.0, self.ControlFlow, ('EnterPlanet',))
        self.nextPlanetEventCurve.curves[0].AddKey(0.0, u'Start')
        self.nextPlanetEventCurve.curves[0].AddCallableKey(1.0, self.ControlFlow, ('NextCollision',))

    def TeardownTunnelBindings(self):
        if getattr(self, 'speedBinding', None) is not None:
            self.speedBinding.sourceObject = self.shipModel.speed
        if getattr(self, 'distanceTracker', None) is not None:
            self.distanceTracker.targetObject = None
            self.distanceTracker = None
        if getattr(self, 'exitPlanetEventCurve', None) is not None:
            del self.exitPlanetEventCurve.curves[0]
            del self.enterPlanetEventCurve.curves[0]
            del self.nextPlanetEventCurve.curves[0]

    def CalcEffectiveRadius(self, direction, planetPosition, planetRadius):
        distToMiddle = planetPosition * direction
        if distToMiddle < 0:
            return None
        midPoint = direction * distToMiddle
        distToCenter = Vector3(planetPosition - midPoint).Length()
        if distToCenter > planetRadius:
            return None
        return sqrt(planetRadius * planetRadius - distToCenter * distToCenter)

    def GetDistanceToTarget(self, direction, planetPosition):
        return planetPosition * direction

    def GetWarpCollisions(self, ball):
        space = sm.GetService('space')
        planets = space.planetManager.planets
        destination = Vector3(self.destination)
        source = Vector3(ball.x, ball.y, ball.z)
        self.direction = destination - source
        direction = self.direction
        warpDistance = direction.Length()
        normDirection = Vector3(direction).Normalize()
        self.normDirection = normDirection
        ballpark = sm.GetService('michelle').GetBallpark()
        collisions = []
        for planet in planets:
            planetBall = ballpark.GetBall(planet.id)
            if planetBall is None:
                log.LogWarn('Warping got a None planet ball.')
                continue
            planetRadius = planetBall.radius
            planetPosition = Vector3(planetBall.x, planetBall.y, planetBall.z)
            planetDir = planetPosition - source
            if self.direction.Length2() < planetDir.Length2():
                continue
            effectiveRadius = self.CalcEffectiveRadius(normDirection, planetDir, planetRadius)
            if effectiveRadius is None:
                continue
            collisions.append((planetBall, effectiveRadius))
            blue.pyos.BeNice()

        return collisions

    def FindNextCollision(self, destination, candidates, popCollision = True):
        minDist = None
        time = blue.os.GetSimTime()
        position = self.shipBall.GetVectorAt(blue.os.GetSimTime())
        position = (position.x, position.y, position.z)
        nextCollision = None
        for each in candidates:
            collisionBall = each[0]
            collisionCenter = collisionBall.GetVectorAt(time)
            collisionCenter = Vector3(collisionCenter.x, collisionCenter.y, collisionCenter.z)
            projection = collisionCenter * self.normDirection
            if minDist is None or projection < minDist:
                minDist = projection
                nextCollision = each

        if nextCollision is not None and popCollision:
            candidates.remove(nextCollision)
        return nextCollision

    def SetupNextCollision(self):
        self.hasMoreCollisions = False
        self.distanceTracker.direction = self.normDirection
        time = blue.os.GetSimTime()
        if self.findNext:
            lastCollision = self.nextCollision
            self.nextCollision = self.FindNextCollision(self.destination, self.collisions)
            if self.nextCollision is None:
                self.nextCollision = lastCollision
            if self.nextCollision is None:
                self.collisionCurve.input1 = 1.0
                self.fadeInLength.input1 = 0.0
                self.collisionCurve.input3 = 100000000
                self.collisionCurve.input3 = 100000000
                self.distanceTracker.targetObject = None
                self.distanceTraveled.input1 = 100000000
                self.distanceTracker.targetPosition = (0, 0, 100000000)
                self.distanceTracker.direction = (0, 0, -1)
                return True
            targetPosition = self.nextCollision[0].GetVectorAt(time)
            targetPosition = Vector3(targetPosition.x, targetPosition.y, targetPosition.z)
            furtherCollision = self.FindNextCollision(self.destination, self.collisions, False)
            if furtherCollision is not None:
                self.hasMoreCollisions = True
                furtherPosition = furtherCollision[0].GetVectorAt(time)
                furtherPosition = Vector3(furtherPosition.x, furtherPosition.y, furtherPosition.z)
                length = Vector3(targetPosition - furtherPosition).Length()
                self.nextPlanetBinding.sourceObject.input2 = length / 2
        else:
            targetPosition = self.nextCollision[0].GetVectorAt(time)
            targetPosition = Vector3(targetPosition.x, targetPosition.y, targetPosition.z)
        distanceToCollision = self.GetDistanceToTarget(self.normDirection, targetPosition)
        returnValue = True
        if distanceToCollision > self.warpSpeedModifier * 3 * const.AU:
            self.findNext = False
            returnValue = False
            self.nextPlanetBinding.sourceObject.input2 = self.warpSpeedModifier * 3 * const.AU
        else:
            self.findNext = True
        planetRadius = self.nextCollision[0].radius
        delta = self.CalcEffectiveRadius(self.normDirection, targetPosition, planetRadius)
        if delta is None:
            delta = planetRadius
        self.nextCollision = (self.nextCollision[0], delta)
        self.collisionCurve.input1 = 1.1 * delta / 10000.0
        self.fadeInLength.input1 = 80000 * self.warpSpeedModifier * 3
        self.collisionCurve.input3 = abs(distanceToCollision) / 10000.0
        self.distanceTracker.targetObject = self.nextCollision[0]
        self.distanceTraveled.input1 = abs(distanceToCollision) / 10000.0
        return returnValue

    def WarpLoop(self, ball):
        space = sm.GetService('space')
        space.StartWarpIndication()
        sm.ScatterEvent('OnWarpStarted')
        self.shipBall = ball
        while ball.mode == destiny.DSTBALL_WARP:
            sm.GetService('space').IndicateWarp()
            self.ShakeCamera(ball)
            if not self.hasExploded or self.hasWind:
                speedFraction = self.shipModel.speed.value * self.curveSet.bindings[0].scale
                if not self.hasExploded and speedFraction > 0.05:
                    sm.StartService('audio').SendUIEvent('wise:/ship_warp_explosion_play')
                    sm.StartService('audio').SendUIEvent('wise:/ship_warp_wind_play')
                    self.hasExploded = True
                    self.hasWind = True
                    sm.ScatterEvent('OnWarpStarted2')
                elif self.hasWind and speedFraction < 0.001:
                    sm.StartService('audio').SendUIEvent('wise:/ship_warp_wind_stop')
                    self.hasWind = False
            blue.synchro.SleepSim(1000)
            if hasattr(self.gfx, 'display'):
                self.gfx.display = True

        sm.StartService('audio').SendUIEvent('wise:/ship_warp_wind_stop')
        self.debugStopRequested = True
        sm.StartService('FxSequencer').OnSpecialFX(ball.id, None, None, None, None, [], 'effects.Warping', 0, 0, 0)
        sm.ScatterEvent('OnWarpFinished')
        sm.StartService('space').StopWarpIndication()

    def Stop(self):
        shipID = self.GetEffectShipID()
        if shipID != session.shipid:
            return
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        camera.noise = 0
        if not getattr(self, 'debugStopRequested', False):
            raise RuntimeError('WarpEffect: got a stop event before effect finished (prepared %s/started %s)' % (self.debugPrepared, self.debugStarted))
        self.TeardownTunnelBindings()
        self.shipBall = None
        self.shipModel = None
        effects.ShipEffect.Stop(self)

    def ShakeCamera(self, ball):
        shakeEnabled = settings.user.ui.Get('cameraShakeEnabled', 1)
        camera = sm.GetService('sceneManager').GetRegisteredCamera('default')
        if camera is None:
            return
        if not shakeEnabled:
            camera.noise = 0
            return
        ballpark = sm.GetService('michelle').GetBallpark()
        if ballpark is None:
            return
        speedVector = trinity.TriVector(ball.vx, ball.vy, ball.vz)
        speed = speedVector.Length()
        maxSpeed = ballpark.warpSpeed * const.AU - ball.maxVelocity
        speed = (speed - ball.maxVelocity) / maxSpeed
        speed = max(0.0, speed)
        rumbleFactor = 0.5 - 0.5 * cos(6.28 * pow(speed, 0.1))
        rumbleFactor = (rumbleFactor - 0.2) / 0.8
        rumbleFactor = max(rumbleFactor, 0.0)
        rumbleFactor = pow(rumbleFactor, 0.8)
        shakeFactor = 0.7 * rumbleFactor
        if camera.noiseScaleCurve is None:
            noiseScale = 0.0
        else:
            noiseScale = camera.noiseScale
        noisescaleCurve = trinity.TriScalarCurve()
        noisescaleCurve.extrapolation = trinity.TRIEXT_CONSTANT
        noisescaleCurve.AddKey(0.0, noiseScale, 0.0, 0.0, trinity.TRIINT_LINEAR)
        noisescaleCurve.AddKey(0.5, shakeFactor * 2.0, 0.0, 0.0, trinity.TRIINT_LINEAR)
        noisescaleCurve.AddKey(5.0, 0.0, 0.0, 0.0, trinity.TRIINT_LINEAR)
        noisescaleCurve.Sort()
        camera.noiseScaleCurve = noisescaleCurve
        now = blue.os.GetSimTime()
        camera.noiseScaleCurve.start = now
        camera.noise = 1

    def AlignToDirection(self):
        destination = sm.StartService('space').warpDestinationCache[3]
        ballPark = sm.StartService('michelle').GetBallpark()
        egoball = ballPark.GetBall(ballPark.ego)
        direction = [egoball.x - destination[0], egoball.y - destination[1], egoball.z - destination[2]]
        zaxis = Vector3(direction)
        if zaxis.Length2() > 0.0:
            Up = Vector3([0.0, 1.0, 0.0])
            zaxis.Normalize()
            xaxis = Up ^ zaxis
            if xaxis.Length2() == 0.0:
                zaxis += Vector3().Randomize(0.0001)
                zaxis.Normalize()
                xaxis = Up ^ zaxis
            xaxis.Normalize()
            yaxis = zaxis ^ xaxis
        else:
            self.transformFlags = effects.FX_TF_POSITION_BALL | effects.FX_TF_ROTATION_BALL
            self.Prepare()
            return
        mat = ((xaxis[0],
          xaxis[1],
          xaxis[2],
          0.0),
         (yaxis[0],
          yaxis[1],
          yaxis[2],
          0.0),
         (zaxis[0],
          zaxis[1],
          zaxis[2],
          0.0),
         (0.0, 0.0, 0.0, 1.0))
        quat = geo2.QuaternionRotationMatrix(mat)
        self.gfxModel.rotationCurve = None
        if self.gfxModel and hasattr(self.gfxModel, 'modelRotationCurve'):
            self.gfxModel.modelRotationCurve = trinity.TriRotationCurve(0.0, 0.0, 0.0, 1.0)
            self.gfxModel.modelRotationCurve.value = quat
        self.debugAligned = True

    def Repeat(self, duration):
        if self.gfx is None:
            return
        effects.ShipEffect.Repeat(self)