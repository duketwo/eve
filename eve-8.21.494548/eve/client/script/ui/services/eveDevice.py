#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/services/eveDevice.py
import blue
import trinity
import svc
from util import ReadYamlFile
import localization
import uicls
import uthread
import log
NVIDIA_VENDORID = 4318

class EveDeviceMgr(svc.device):
    __guid__ = 'svc.eveDevice'
    __replaceservice__ = 'device'
    __notifyevents__ = ['OnSessionChanged']

    def AppRun(self):
        if not settings.public.generic.Get('resourceUnloading', 1):
            trinity.SetEveSpaceObjectResourceUnloadingEnabled(0)
        self.defaultPresentationInterval = trinity.PRESENT_INTERVAL.ONE
        self.deviceCategories = ReadYamlFile('res:/videoCardCategories.yaml')
        if settings.public.device.Get('depthEffectsEnabled', self.GetDefaultDepthEffectsEnabled()) and not self.SupportsDepthEffects():
            settings.public.device.Set('depthEffectsEnabled', False)
        if prefs.HasKey('shadowsEnabled'):
            shadowsEnabled = prefs.GetValue('shadowsEnabled')
            if not settings.public.HasKey('device', 'shadowQuality'):
                if not shadowsEnabled:
                    settings.public.device.Set('shadowQuality', 0)
                else:
                    settings.public.device.Set('shadowQuality', self.GetDefaultShadowQuality())
            prefs.DeleteValue('shadowsEnabled')
        if prefs.HasKey('bloomType'):
            bloomType = prefs.GetValue('bloomType')
            if not settings.public.HasKey('device', 'postProcessingQuality'):
                if bloomType == 0 or bloomType == 1:
                    settings.public.device.Set('postProcessingQuality', bloomType)
                else:
                    settings.public.device.Set('postProcessingQuality', 2)
                settings.public.device.Set('bloomType', bloomType)
            prefs.DeleteValue('bloomType')
        if not settings.public.HasKey('device', 'antiAliasing'):
            set = settings.public.device.Get('DeviceSettings', {}).copy()
            msType = set.get('MultiSampleType', 0)
            set['MultiSampleType'] = 0
            set['MultiSampleQuality'] = 0
            settings.public.device.Set('DeviceSettings', set)
            self.settings.SaveSettings()
            antiAliasing = 0
            if msType >= 8:
                antiAliasing = 3
            elif msType >= 4:
                antiAliasing = 2
            elif msType >= 2:
                antiAliasing = 1
            settings.public.device.Set('antiAliasing', antiAliasing)
        if not settings.public.HasKey('device', 'interiorShaderQuality'):
            settings.public.device.Set('interiorShaderQuality', self.GetDefaultInteriorShaderQuality())
        if settings.public.device.Get('interiorShaderQuality', self.GetDefaultInteriorShaderQuality()) != 0:
            trinity.AddGlobalSituationFlags(['OPT_INTERIOR_SM_HIGH'])
        else:
            trinity.RemoveGlobalSituationFlags(['OPT_INTERIOR_SM_HIGH'])
        self.deviceCreated = False
        if blue.win32.IsTransgaming():
            self.cider = sm.GetService('cider')
            self.ciderFullscreenLast = False
            self.ciderFullscreenBackup = False

    def Initialize(self):
        self.CheckDx11FeatureLevel()
        svc.device.Initialize(self)
        aaQuality = settings.public.device.Get('antiAliasing', 0)
        if aaQuality > 0 and self.GetMSAATypeFromQuality(aaQuality) == 0:
            settings.public.device.Set('antiAliasing', 0)
        shaderQuality = settings.public.device.Get('shaderQuality', self.GetDefaultShaderQuality())
        if shaderQuality == 3 and not self.SupportsDepthEffects():
            settings.public.device.Set('shaderQuality', 2)
        hdrEnabled = settings.public.device.Get('hdrEnabled', 0)
        if not self.IsHDRSupported():
            settings.public.device.Set('hdrEnabled', 0)

    def CreateDevice(self):
        svc.device.CreateDevice(self)
        if blue.win32.IsTransgaming():
            tgToggleEventHandler = blue.BlueEventToPython()
            tgToggleEventHandler.handler = self.ToggleWindowedTransGaming
            trinity.app.tgToggleEventListener = tgToggleEventHandler

    def CheckDx11FeatureLevel(self):
        log.LogInfo('trying to detect DX11 feature level...')
        featureLevel = trinity.device.GetDx11FeatureLevel()
        log.LogInfo(featureLevel)

    def GetMSAATypeFromQuality(self, quality):
        if quality == 0:
            return 0
        if not hasattr(self, 'msaaTypes'):
            set = self.GetSettings()
            formats = [(set.BackBufferFormat, True), (set.AutoDepthStencilFormat, False), (trinity.PIXEL_FORMAT.R16G16B16A16_FLOAT, True)]
            self.GetMultiSampleQualityOptions(set, formats)
        if quality >= len(self.msaaTypes):
            quality = len(self.msaaTypes) - 1
        return self.msaaTypes[quality]

    def GetShaderModel(self, val):
        if val == 3:
            if not trinity.renderJobUtils.DeviceSupportsIntZ():
                return 'SM_3_0_HI'
            else:
                return 'SM_3_0_DEPTH'
        elif val == 2:
            return 'SM_3_0_HI'
        return 'SM_3_0_LO'

    def GetWindowModes(self):
        self.LogInfo('GetWindowModes')
        adapter = self.CurrentAdapter()
        if adapter.format not in self.validFormats:
            return [(localization.GetByLabel('/Carbon/UI/Service/Device/FullScreen'), 0)]
        elif blue.win32.IsTransgaming():
            return [(localization.GetByLabel('/Carbon/UI/Service/Device/WindowMode'), 1), (localization.GetByLabel('/Carbon/UI/Service/Device/FullScreen'), 0)]
        else:
            return [(localization.GetByLabel('/Carbon/UI/Service/Device/WindowMode'), 1), (localization.GetByLabel('/Carbon/UI/Service/Device/FullScreen'), 0), (localization.GetByLabel('/Carbon/UI/Service/Device/FixedWindowMode'), 2)]

    def GetAppShaderModel(self):
        shaderQuality = settings.public.device.Get('shaderQuality', self.GetDefaultShaderQuality())
        return self.GetShaderModel(shaderQuality)

    def GetDefaultShaderQuality(self):
        quality = svc.device.GetDefaultShaderQuality(self)
        if quality == 3 and not self.SupportsDepthEffects():
            quality = 2
        return quality

    def GetAppSettings(self):
        appSettings = {}
        lodQuality = settings.public.device.Get('lodQuality', self.GetDefaultLodQuality())
        if lodQuality == 1:
            appSettings = {'eveSpaceSceneVisibilityThreshold': 15.0,
             'eveSpaceSceneLowDetailThreshold': 140.0,
             'eveSpaceSceneMediumDetailThreshold': 480.0}
        elif lodQuality == 2:
            appSettings = {'eveSpaceSceneVisibilityThreshold': 6,
             'eveSpaceSceneLowDetailThreshold': 70,
             'eveSpaceSceneMediumDetailThreshold': 240}
        elif lodQuality == 3:
            appSettings = {'eveSpaceSceneVisibilityThreshold': 3.0,
             'eveSpaceSceneLowDetailThreshold': 35.0,
             'eveSpaceSceneMediumDetailThreshold': 120.0}
        return appSettings

    def GetAppMipLevelSkipExclusionDirectories(self):
        return ['res:/Texture/IntroScene', 'res:/UI/Texture']

    def IsWindowed(self, settings = None):
        if settings is None:
            settings = self.GetSettings()
        if blue.win32.IsTransgaming():
            return not self.cider.GetFullscreen()
        return settings.Windowed

    def SetToSafeMode(self):
        settings.public.device.Set('textureQuality', 2)
        settings.public.device.Set('shaderQuality', 1)
        settings.public.device.Set('hdrEnabled', 0)
        settings.public.device.Set('postProcessingQuality', 0)
        settings.public.device.Set('shadowQuality', 0)
        settings.public.device.Set('resourceCacheEnabled', 0)

    def SetDeviceCiderStartup(self, *args, **kwds):
        devSettings = args[0]
        settingsCopy = devSettings.copy()
        devSettings.BackBufferWidth, devSettings.BackBufferHeight = self.GetPreferedResolution(False)
        self.cider.SetFullscreen(True)
        svc.device.SetDevice(self, devSettings, **kwds)
        self.cider.SetFullscreen(False)
        self.ciderFullscreenLast = False
        svc.device.SetDevice(self, settingsCopy, **kwds)

    def SetDeviceCiderFullscreen(self, *args, **kwds):
        svc.device.SetDevice(self, *args, **kwds)
        self.cider.SetFullscreen(True)

    def SetDeviceCiderWindowed(self, *args, **kwds):
        self.cider.SetFullscreen(False)
        svc.device.SetDevice(self, *args, **kwds)

    def SetDevice(self, *args, **kwds):
        if blue.win32.IsTransgaming():
            ciderFullscreen = self.cider.GetFullscreen()
            self.ciderFullscreenLast = self.cider.GetFullscreen(apiCheck=True)
            if not self.deviceCreated and not ciderFullscreen:
                self.SetDeviceCiderStartup(*args, **kwds)
            elif ciderFullscreen:
                self.SetDeviceCiderFullscreen(*args, **kwds)
            else:
                self.SetDeviceCiderWindowed(*args, **kwds)
            self.deviceCreated = True
        else:
            svc.device.SetDevice(self, *args, **kwds)

    def BackupSettings(self):
        svc.device.BackupSettings(self)
        if blue.win32.IsTransgaming():
            self.ciderFullscreenBackup = self.ciderFullscreenLast

    def DiscardChanges(self, *args):
        if self.settingsBackup:
            if blue.win32.IsTransgaming():
                self.cider.SetFullscreen(self.ciderFullscreenBackup, setAPI=False)
            self.SetDevice(self.settingsBackup)

    def ToggleWindowedTransGaming(self, *args):
        self.LogInfo('ToggleWindowedTransGaming')
        windowed = not self.cider.GetFullscreen(apiCheck=True)
        self.cider.SetFullscreen(not windowed)
        if windowed:
            wr = trinity.app.GetWindowRect()
            self.preFullScreenPosition = (wr.left, wr.top)
        devSettings = self.GetSettings()
        devSettings.BackBufferWidth, devSettings.BackBufferHeight = self.GetPreferedResolution(windowed)
        uthread.new(self.SetDevice, devSettings, hideTitle=True)

    def GetMultiSampleQualityOptions(self, deviceSettings = None, formats = None):
        self.LogInfo('GetMultiSampleQualityOptions')
        if deviceSettings is None:
            deviceSettings = self.GetSettings()
        if formats is None:
            formats = [(deviceSettings.BackBufferFormat, True), (deviceSettings.AutoDepthStencilFormat, False)]
        vID, dID = self.GetVendorIDAndDeviceID()
        self.msaaOptions = [(localization.GetByLabel('/Carbon/UI/Common/Disabled'), 0)]
        self.msaaTypes = [0]

        def Supported(msType):
            supported = True
            for format in formats:
                if format[1]:
                    qualityLevels = trinity.adapters.GetRenderTargetMsaaSupport(deviceSettings.Adapter, format[0], deviceSettings.Windowed, msType)
                else:
                    qualityLevels = trinity.adapters.GetDepthStencilMsaaSupport(deviceSettings.Adapter, format[0], deviceSettings.Windowed, msType)
                supported = supported and qualityLevels

            return supported

        if Supported(2):
            self.msaaOptions.append((localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/LowQuality'), 1))
            self.msaaTypes.append(2)
        if Supported(4):
            self.msaaOptions.append((localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/MediumQuality'), 2))
            self.msaaTypes.append(4)
        if Supported(8):
            self.msaaOptions.append((localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/HighQuality'), 3))
            self.msaaTypes.append(8)
        elif Supported(6):
            self.msaaOptions.append((localization.GetByLabel('UI/SystemMenu/DisplayAndGraphics/Common/HighQuality'), 3))
            self.msaaTypes.append(6)
        return self.msaaOptions

    def GetDefaultFastCharacterCreation(self):
        return 0

    def GetDefaultClothSimEnabled(self):
        shaderModel = trinity.GetShaderModel()
        if shaderModel.startswith('SM_3'):
            return 1
        else:
            return 0

    def GetDefaultCharTextureQuality(self):
        return 1

    def GetDefaultInteriorGraphicsQuality(self):
        return self.GetDeviceCategory()

    def GetDefaultInteriorShaderQuality(self):
        if self.GetDeviceCategory() > 1:
            return 1
        return 0

    def EnforceDeviceSettings(self, devSettings):
        devSettings.BackBufferFormat = self.GetBackbufferFormats()[0]
        devSettings.AutoDepthStencilFormat = self.GetStencilFormats()[0]
        devSettings.MultiSampleType = 0
        devSettings.MultiSampleQuality = 0
        return devSettings

    def SupportsDepthEffects(self):
        return trinity.renderJobUtils.DeviceSupportsIntZ()

    def GetDefaultDepthEffectsEnabled(self):
        return trinity.renderJobUtils.DeviceSupportsIntZ() and not trinity.GetMaxShaderModelSupported().startswith('SM_2')

    def GetDefaultShadowQuality(self):
        return self.GetDeviceCategory()

    def GetDefaultPostProcessingQuality(self):
        if not self.IsBloomSupported():
            return 0
        return self.GetDeviceCategory()

    def GetAdapterResolutionsAndRefreshRates(self, set = None):
        options, resoptions = svc.device.GetAdapterResolutionsAndRefreshRates(self, set)
        if set.Windowed:
            maxWidth = trinity.app.GetVirtualScreenWidth()
            maxHeight = trinity.app.GetVirtualScreenHeight()
            maxLabel = localization.GetByLabel('/Carbon/UI/Service/Device/ScreenSize', width=maxWidth, height=maxHeight)
            maxOp = (maxLabel, (maxWidth, maxHeight))
            if maxOp not in options:
                options.append(maxOp)
        elif blue.win32.IsTransgaming() and self.IsWindowed(set):
            width = trinity.app.GetVirtualScreenWidth()
            height = trinity.app.GetVirtualScreenHeight() - 44
            if height < trinity.app.minimumHeight:
                height = trinity.app.minimumHeight
            label = localization.GetByLabel('/Carbon/UI/Service/Device/ScreenSize', width=width, height=height)
            op = (label, (width, height))
            if op not in options:
                options.append(op)
            width = width / 2
            if width < trinity.app.minimumWidth:
                width = trinity.app.minimumWidth
            label = localization.GetByLabel('/Carbon/UI/Service/Device/ScreenSize', width=width, height=height)
            op = (label, (width, height))
            if op not in options:
                options.append(op)
        return (options, resoptions)

    def GetDeviceCategory(self):
        if self.CheckIfHighEndGraphicsDevice():
            return 2
        if self.CheckIfMediumGraphicsDevice():
            return 1
        if self.CheckIfLowEndGraphicsDevice():
            return 0
        return 2

    def CheckIfHighEndGraphicsDevice(self):
        identifier = self.cachedAdapterIdentifiers[0]
        if identifier is None:
            return False
        deviceID = identifier.vendorID
        vendorID = identifier.deviceID
        return (vendorID, deviceID) in self.deviceCategories['high']

    def CheckIfMediumGraphicsDevice(self):
        identifier = self.cachedAdapterIdentifiers[0]
        if identifier is None:
            return False
        deviceID = identifier.vendorID
        vendorID = identifier.deviceID
        return (vendorID, deviceID) in self.deviceCategories['medium']

    def CheckIfLowEndGraphicsDevice(self):
        identifier = self.cachedAdapterIdentifiers[0]
        if identifier is None:
            return False
        deviceID = identifier.vendorID
        vendorID = identifier.deviceID
        return (vendorID, deviceID) in self.deviceCategories['low']

    def GetAppFeatureState(self, featureName, featureDefaultState):
        defaultInteriorGraphicsQuality = self.GetDefaultInteriorGraphicsQuality()
        interiorGraphicsQuality = settings.public.device.Get('interiorGraphicsQuality', defaultInteriorGraphicsQuality)
        postProcessingQuality = settings.public.device.Get('postProcessingQuality', self.GetDefaultPostProcessingQuality())
        shaderQuality = settings.public.device.Get('shaderQuality', self.GetDefaultShaderQuality())
        shadowQuality = settings.public.device.Get('shadowQuality', self.GetDefaultShadowQuality())
        interiorShaderQuality = settings.public.device.Get('interiorShaderQuality', self.GetDefaultInteriorShaderQuality())
        if featureName == 'Interior.ParticlesEnabled':
            return interiorGraphicsQuality == 2
        elif featureName == 'Interior.LensflaresEnabled':
            return interiorGraphicsQuality >= 1
        elif featureName == 'Interior.lowSpecMaterialsEnabled':
            return interiorGraphicsQuality == 0
        elif featureName == 'Interior.ssaoEnbaled':
            identifier = self.cachedAdapterIdentifiers[0]
            if identifier is not None:
                vendorID = identifier.vendorID
                if vendorID != 4318:
                    return False
            return postProcessingQuality != 0 and shaderQuality > 1
        elif featureName == 'Interior.dynamicShadows':
            return shadowQuality > 1
        elif featureName == 'Interior.lightPerformanceLevel':
            return interiorGraphicsQuality
        elif featureName == 'Interior.clothSimulation':
            identifier = self.cachedAdapterIdentifiers[0]
            if identifier is None:
                return featureDefaultState
            vendorID = identifier.vendorID
            return vendorID == NVIDIA_VENDORID and settings.public.device.Get('charClothSimulation', featureDefaultState) and interiorGraphicsQuality == 2 and not blue.win32.IsTransgaming()
        elif featureName == 'CharacterCreation.clothSimulation':
            return settings.public.device.Get('charClothSimulation', featureDefaultState)
        elif featureName == 'Interior.useSHLighting':
            return interiorShaderQuality > 0
        else:
            return featureDefaultState

    def GetUIScalingOptions(self, height = None):
        if height:
            desktopHeight = height
        else:
            desktopHeight = uicore.desktop.height
        options = [(localization.GetByLabel('UI/Common/Formatting/Percentage', percentage=90), 0.9), (localization.GetByLabel('UI/Common/Formatting/Percentage', percentage=100), 1.0)]
        if desktopHeight >= 900:
            options.append((localization.GetByLabel('UI/Common/Formatting/Percentage', percentage=110), 1.1))
        if desktopHeight >= 960:
            options.append((localization.GetByLabel('UI/Common/Formatting/Percentage', percentage=125), 1.25))
        if desktopHeight >= 1200:
            options.append((localization.GetByLabel('UI/Common/Formatting/Percentage', percentage=150), 1.5))
        return options

    def GetChange(self, scaleValue):
        oldHeight = int(trinity.device.height / uicore.desktop.dpiScaling)
        oldWidth = int(trinity.device.width / uicore.desktop.dpiScaling)
        newHeight = int(trinity.device.height / scaleValue)
        newWidth = int(trinity.device.width / scaleValue)
        changeDict = {}
        changeDict['ScalingWidth'] = (oldWidth, newWidth)
        changeDict['ScalingHeight'] = (oldHeight, newHeight)
        return changeDict

    def CapUIScaleValue(self, checkValue):
        desktopHeight = trinity.device.height
        minScale = 0.9
        if desktopHeight < 900:
            maxScale = 1.0
        elif desktopHeight < 960:
            maxScale = 1.1
        elif desktopHeight < 1200:
            maxScale = 1.25
        else:
            maxScale = 1.5
        return max(minScale, min(maxScale, checkValue))

    def SetupUIScaling(self):
        if not uicore.desktop:
            return
        windowed = self.IsWindowed()
        self.SetUIScaleValue(self.GetUIScaleValue(windowed), windowed)

    def SetUIScaleValue(self, scaleValue, windowed):
        self.LogInfo('SetUIScaleValue', scaleValue, 'windowed', windowed)
        capValue = self.CapUIScaleValue(scaleValue)
        if windowed:
            settings.public.device.Set('UIScaleWindowed', capValue)
        else:
            settings.public.device.Set('UIScaleFullscreen', capValue)
        if capValue != uicore.desktop.dpiScaling:
            PreUIScaleChange_DesktopLayout = uicls.Window.GetDesktopWindowLayout()
            oldValue = uicore.desktop.dpiScaling
            uicore.desktop.dpiScaling = capValue
            uicore.desktop.UpdateSize()
            self.LogInfo('SetUIScaleValue capValue', capValue)
            sm.ScatterEvent('OnUIScalingChange', (oldValue, capValue))
            uicls.Window.LoadDesktopWindowLayout(PreUIScaleChange_DesktopLayout)
        else:
            self.LogInfo('SetUIScaleValue No Change')

    def GetUIScaleValue(self, windowed):
        if windowed:
            scaleValue = settings.public.device.Get('UIScaleWindowed', 1.0)
        else:
            scaleValue = settings.public.device.Get('UIScaleFullscreen', 1.0)
        return scaleValue

    def OnSessionChanged(self, isRemote, session, change):
        if 'userid' in change:
            trinity.settings.SetValue('eveSpaceObjectTrailsEnabled', settings.user.ui.Get('trailsEnabled', settings.user.ui.Get('effectsEnabled', 1)))
            trinity.settings.SetValue('gpuParticlesEnabled', settings.user.ui.Get('gpuParticlesEnabled', settings.user.ui.Get('effectsEnabled', 1)))