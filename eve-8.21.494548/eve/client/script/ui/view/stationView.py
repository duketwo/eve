#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/view/stationView.py
import viewstate
import sys
import log
import util
import uthread
import blue

class StationView(viewstate.View):
    __guid__ = 'viewstate.StationView'
    __notifyevents__ = ['OnDogmaItemChange', 'ProcessActiveShipChanged']
    __dependencies__ = ['godma',
     'loading',
     'station',
     'invCache',
     't3ShipSvc',
     'sceneManager',
     'clientDogmaIM']
    __overlays__ = {'sidePanels'}

    def ShowShip(self, shipID):
        self.WaitForShip(shipID)
        hangarInv = self.invCache.GetInventory(const.containerHangar)
        hangarItems = hangarInv.List()
        for each in hangarItems:
            if each.itemID == shipID:
                self.activeShipItem = each
                try:
                    uthread.new(self.ShowActiveShip)
                except Exception as e:
                    log.LogException('Failed to show ship')
                    sys.exc_clear()

                break

    def HideView(self):
        interiorScene = sm.GetService('sceneManager').GetActiveScene()
        if interiorScene:
            for cs in interiorScene.curveSets:
                for binding in cs.bindings:
                    binding.copyValueCallable = None

                del cs.bindings[:]
                del cs.curves[:]

        viewstate.View.HideView(self)

    def WaitForShip(self, shipID):
        maximumWait = 10000
        sleepUnit = 100
        iterations = maximumWait / sleepUnit
        while util.GetActiveShip() != shipID and iterations:
            iterations -= 1
            blue.pyos.synchro.SleepWallclock(sleepUnit)

        if util.GetActiveShip() != shipID:
            raise RuntimeError('Ship never came :(')
        self.LogInfo('Waited for ship for %d iterations.' % (maximumWait / sleepUnit - iterations))

    def OnDogmaItemChange(self, item, change):
        if item.locationID == change.get(const.ixLocationID, None) and item.flagID == change.get(const.ixFlag):
            return
        activeShipID = util.GetActiveShip()
        if item.locationID == activeShipID and cfg.IsShipFittingFlag(item.flagID) and item.categoryID == const.categorySubSystem:
            self.ShowShip(activeShipID)

    def ProcessActiveShipChanged(self, shipID, oldShipID):
        if oldShipID != shipID:
            self.ShowShip(shipID)