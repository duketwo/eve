#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/view/spaceView.py
from viewstate import View
import uicls
import service
import uiconst
import blue

class SpaceView(View):
    __guid__ = 'viewstate.SpaceView'
    __notifyevents__ = []
    __dependencies__ = ['standing',
     'tactical',
     'pathfinder',
     'map',
     'wallet',
     'space',
     'state',
     'bracket',
     'target',
     'fleet',
     'surveyScan',
     'autoPilot',
     'neocom',
     'corp',
     'alliance',
     'skillqueue',
     'dungeonTracking',
     'transmission',
     'clonejump',
     'assets',
     'charactersheet',
     'trigger',
     'contracts',
     'certificates',
     'billboard',
     'sov',
     'turret',
     'camera',
     'posAnchor',
     'michelle',
     'sceneManager']
    __layerClass__ = uicls.InflightLayer
    __subLayers__ = [('l_spaceTutorial', None, None), ('l_bracket', None, None), ('l_tactical', None, None)]
    __overlays__ = {'shipui', 'sidePanels', 'target'}

    def __init__(self):
        View.__init__(self)
        self.solarSystemID = None
        self.keyDownEvent = None

    def LoadView(self, change = None, **kwargs):
        self.solarSystemID = session.solarsystemid
        if eve.session.role & service.ROLE_CONTENT:
            sm.StartService('scenario')
        self.bracket.Reload()
        self.cachedPlayerPos = None
        self.cachedPlayerRot = None

    def UnloadView(self):
        self.LogInfo('unloading: removed ballpark and cleared effects')
        uicore.layer.main.state = uiconst.UI_PICKCHILDREN
        self.sceneManager.UnregisterScene('default')
        self.sceneManager.UnregisterCamera('default')
        sm.GetService('camera').ClearCameraParent('default')
        blue.recycler.Clear()

    def ShowView(self, **kwargs):
        View.ShowView(self, **kwargs)
        self.keyDownEvent = uicore.event.RegisterForTriuiEvents([uiconst.UI_KEYDOWN], self.CheckKeyDown)

    def HideView(self):
        if self.keyDownEvent:
            uicore.event.UnregisterForTriuiEvents(self.keyDownEvent)
        View.HideView(self)
        sm.GetService('gameui').CacheCameraTranslation()

    def CheckShouldReopen(self, newKwargs, cachedKwargs):
        reopen = False
        changes = newKwargs.get('changes')
        if newKwargs == cachedKwargs or 'changes' in newKwargs and 'solarsystemid' in newKwargs['changes']:
            reopen = True
        return reopen

    def CheckKeyDown(self, *args):
        ctrl = uicore.uilib.Key(uiconst.VK_CONTROL)
        alt = uicore.uilib.Key(uiconst.VK_MENU)
        shift = uicore.uilib.Key(uiconst.VK_SHIFT)
        if not ctrl and alt and not shift and session.solarsystemid:
            self.bracket.ShowAllHidden()
        return 1