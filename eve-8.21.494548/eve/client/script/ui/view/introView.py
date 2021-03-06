#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/view/introView.py
from viewstate import View
import form
import trinity

class IntroView(View):
    __guid__ = 'viewstate.IntroView'
    __notifyevents__ = []
    __dependencies__ = []
    __layerClass__ = form.Intro

    def __init__(self):
        View.__init__(self)

    def LoadView(self, **kwargs):
        self.SetLiteMode(True)

    def UnloadView(self):
        self.SetLiteMode(False)

    def SetLiteMode(self, enable = True):
        if enable:
            if not hasattr(self, 'preIntroductionHdr'):
                setattr(self, 'preIntroductionHdr', trinity.device.hdrEnable)
            trinity.device.hdrEnable = False
            if not hasattr(self, 'preIntroductionAsyncLoad'):
                setattr(self, 'preIntroductionAsyncLoad', trinity.device.disableAsyncLoad)
            trinity.device.disableAsyncLoad = True
        else:
            if hasattr(self, 'preIntroductionHdr'):
                trinity.device.hdrEnable = getattr(self, 'preIntroductionHdr', False)
            if hasattr(self, 'preIntroductionAsyncLoad'):
                trinity.device.disableAsyncLoad = getattr(self, 'preIntroductionAsyncLoad', False)