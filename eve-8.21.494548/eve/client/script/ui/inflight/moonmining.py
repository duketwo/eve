#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/inflight/moonmining.py
import blue
import uthread
import uix
import xtriui
import listentry
import util
import base
import math
import service
import sys
import state
import uiutil
import uicls
import uiconst
import entities
import log
import localization
import localizationUtil
import fontConst
structProgressMap = {const.pwnStructureStateAnchoring: const.pwnStructureStateAnchored,
 const.pwnStructureStateOnlining: const.pwnStructureStateOnline,
 const.pwnStructureStateUnanchoring: const.pwnStructureStateUnanchored,
 const.pwnStructureStateReinforced: const.pwnStructureStateOnline,
 const.pwnStructureStateOperating: const.pwnStructureStateOnline}
MINWNDWIDTH = 496

class MoonMining(uicls.Window):
    __guid__ = 'form.MoonMining'
    __notifyevents__ = ['OnSlimItemChange',
     'DoBallsAdded',
     'DoBallRemove',
     'DoBallClear',
     'OnMoonProcessChange',
     'OnBallparkCall']
    default_windowID = 'moon'

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.SetHeaderIcon()
        settingsIcon = self.sr.headerIcon
        settingsIcon.state = uiconst.UI_NORMAL
        settingsIcon.GetMenu = self.TowerMenu
        settingsIcon.expandOnLeft = 1
        settingsIcon.hint = localization.GetByLabel('UI/Inflight/MoonMining/Actions')
        slimItem = attributes.slimItem
        self.notifySettings = None
        try:
            self.SetWndIcon()
            self.SetTopparentHeight(0)
            self.connectionsChanged = 0
            self.godma = sm.GetService('godma')
            self.scope = 'all'
            self.sr.main = uiutil.GetChild(self, 'main')
            self.moon = None
            if slimItem:
                if slimItem.ownerID != eve.session.corpid:
                    self.CloseByUser()
                    return
                self.slimItem = slimItem
                self.sr.name = uix.GetSlimItemName(self.slimItem)
                self.SetCaption(localization.GetByLabel('UI/Inflight/MoonMining/ControlTowerManager'))
                self.capacity = self.godma.GetType(self.slimItem.typeID).capacity
                self.capacitySecondary = self.godma.GetType(self.slimItem.typeID).capacitySecondary
                self.tower = self.GetShell(self.slimItem.itemID)
                cfg.eveowners.Prime([self.slimItem.ownerID])
                self.sr.owner = cfg.eveowners.Get(self.slimItem.ownerID).name
                self.posMgr = util.Moniker('posMgr', eve.session.solarsystemid)
                self.pwn = sm.GetService('pwn')
                self.GetMoon()
            else:
                self.sr.name = 'testing'
                self.sr.owner = cfg.eveowners.Get(eve.session.charid).name
            self.sr.powerSupply = 0
            self.sr.cpuSupply = 0
            self.sr.powerConsumption = 0
            self.sr.cpuConsumption = 0
            self.doClear = True
            self.sr.top = uicls.Container(name='top', align=uiconst.TOTOP, parent=self.sr.main, padLeft=const.defaultPadding, clipChildren=1)
            self.sr.picParent = uicls.Container(name='picpar', parent=self.sr.top, align=uiconst.TOPLEFT, width=64, height=64, left=const.defaultPadding, top=const.defaultPadding)
            self.sr.icon = uicls.Icon(parent=self.sr.picParent, align=uiconst.TOALL, padding=(1, 1, 1, 1))
            uicls.Frame(parent=self.sr.picParent)
            if slimItem:
                self.sr.icon.LoadIconByTypeID(self.slimItem.typeID, ignoreSize=True)
            uicls.Container(name='push', align=uiconst.TOLEFT, width=83, parent=self.sr.top)
            uicls.Container(name='push', align=uiconst.TOTOP, height=2, parent=self.sr.top)
            r = uicls.Container(name='rightstats', parent=self.sr.top, align=uiconst.TORIGHT, width=100)
            h = uicls.Container(name='info', parent=self.sr.top, align=uiconst.TOALL, pos=(0, 0, 0, 0))
            self.sr.status = uicls.EveLabelSmall(text='', parent=r, top=20, left=8, width=100, state=uiconst.UI_NORMAL, align=uiconst.TOPRIGHT)
            title = uicls.EveLabelMediumBold(text=self.sr.name, parent=h, maxLines=1, state=uiconst.UI_NORMAL, bold=True)
            top = title.textheight
            towerLocationLabel = localization.GetByLabel('UI/Inflight/MoonMining/TowerLocation')
            self.sr.locationtext = uicls.EveLabelSmallBold(text=towerLocationLabel, parent=h, top=top, state=uiconst.UI_NORMAL)
            top += self.sr.locationtext.textheight - 2
            towerOwnerLabel = localization.GetByLabel('UI/Inflight/MoonMining/TowerOwner')
            t = uicls.EveLabelSmallBold(text=towerOwnerLabel, parent=h, top=top, state=uiconst.UI_NORMAL)
            t = uicls.EveLabelSmall(text=self.sr.owner, parent=h, left=55, top=top, state=uiconst.UI_NORMAL, bold=True)
            top += t.textheight + 2
            icontop = top
            gaugeLeft = 70
            textLeft = 140
            t = uicls.EveLabelSmallBold(text=localization.GetByLabel('UI/Inflight/MoonMining/TowerShield'), parent=h, left=0, top=top)
            self.sr.shieldgauge = self.GetGauge(h, gaugeLeft, top + 1, (0.8, 0.8, 1.0, 0.5))
            self.sr.shieldtext = uicls.EveLabelSmall(text='', parent=h, left=textLeft, top=top)
            top += t.textheight - 2
            t = uicls.EveLabelSmallBold(text=localization.GetByLabel('UI/Inflight/MoonMining/TowerArmor'), parent=h, left=0, top=top)
            self.sr.armorgauge = self.GetGauge(h, gaugeLeft, top + 1, (0.6, 0.6, 1.0, 0.5))
            self.sr.armortext = uicls.EveLabelSmall(text='', parent=h, left=textLeft, top=top)
            top += t.textheight - 2
            t = uicls.EveLabelSmallBold(text=localization.GetByLabel('UI/Inflight/MoonMining/TowerStructure'), parent=h, left=0, top=top)
            self.sr.structuregauge = self.GetGauge(h, gaugeLeft, top + 1, (0.4, 0.4, 1.0, 0.5))
            self.sr.structuretext = uicls.EveLabelSmall(text='', parent=h, left=textLeft, top=top)
            top += t.textheight - 2
            t = uicls.EveLabelSmallBold(text=localization.GetByLabel('UI/Inflight/MoonMining/TowerPower'), parent=h, left=0, top=top)
            self.sr.powergauge = self.GetGauge(h, gaugeLeft, top + 1, (1.0, 1.0, 0.0, 0.5))
            self.sr.powertext = uicls.EveLabelSmall(text='', parent=h, left=textLeft, top=top)
            top += t.textheight - 2
            t = uicls.EveLabelSmallBold(text=localization.GetByLabel('UI/Inflight/MoonMining/TowerCPU'), parent=h, left=0, top=top)
            self.sr.cpugauge = self.GetGauge(h, gaugeLeft, top + 1, (0.0, 0.0, 1.0, 0.5))
            self.sr.cputext = uicls.EveLabelSmall(text='', parent=h, left=textLeft, top=top)
            top += t.textheight
            self.sr.top.height = top
            iconsize = 24
            uicls.Icon(icon='ui_22_32_20', parent=r, pos=(0,
             icontop - 5,
             iconsize,
             iconsize), hint=cfg.dgmattribs.Get(const.attributeShieldEmDamageResonance).displayName, ignoreSize=True)
            uicls.Icon(icon='ui_22_32_19', parent=r, pos=(0,
             icontop + 15,
             iconsize,
             iconsize), hint=cfg.dgmattribs.Get(const.attributeShieldExplosiveDamageResonance).displayName, ignoreSize=True)
            uicls.Icon(icon='ui_22_32_17', parent=r, pos=(50,
             icontop - 5,
             iconsize,
             iconsize), hint=cfg.dgmattribs.Get(const.attributeShieldKineticDamageResonance).displayName, ignoreSize=True)
            uicls.Icon(icon='ui_22_32_18', parent=r, pos=(50,
             icontop + 15,
             iconsize,
             iconsize), hint=cfg.dgmattribs.Get(const.attributeShieldThermalDamageResonance).displayName, ignoreSize=True)
            self.sr.emkinText = uicls.EveLabelSmall(text='', parent=r, left=20, top=icontop, width=100, tabs=[50], state=uiconst.UI_DISABLED)
            self.sr.emkinText._tabMargin = 0
            self.sr.expthermText = uicls.EveLabelSmall(text='', parent=r, left=20, top=icontop + 20, width=100, tabs=[50], state=uiconst.UI_DISABLED)
            self.sr.expthermText._tabMargin = 0
            blue.pyos.synchro.Yield()
            btns = [(localization.GetByLabel('UI/Inflight/POS/AnchorObject'),
              self.Anchor,
              (),
              84),
             (localization.GetByLabel('UI/Inflight/MoonMining/Structures/Unanchor'),
              self.Unanchor,
              (),
              84),
             (localization.GetByLabel('UI/Inflight/MoonMining/PutOnline'),
              self.Online,
              (),
              84),
             (localization.GetByLabel('UI/Inflight/MoonMining/PutOffline'),
              self.Offline,
              (),
              84)]
            self.sr.structuresbuttons = uicls.ButtonGroup(btns=btns, parent=self.sr.main)
            self.sr.structuresbuttons.state = uiconst.UI_HIDDEN
            btns = [(localization.GetByLabel('UI/Common/Buttons/Apply'),
              self.ProdApply,
              (),
              84), (localization.GetByLabel('UI/Inflight/MoonMining/Processes/Reload'),
              self.ProdReload,
              (),
              84), (localization.GetByLabel('UI/Inflight/MoonMining/Processes/ClearLinks'),
              self.ProdClearLinks,
              (),
              84)]
            if eve.session.role & service.ROLE_GML:
                btns.append((localization.GetByLabel('UI/Inflight/MoonMining/Processes/RunCycle'),
                 self.RunProcessCycle,
                 (),
                 84))
            self.sr.productionbuttons = uicls.ButtonGroup(btns=btns, parent=self.sr.main)
            self.sr.productionbuttons.state = uiconst.UI_HIDDEN
            btns = [(localization.GetByLabel('UI/Inflight/MoonMining/Processes/Open'),
              self.OpenResources,
              (),
              84)]
            self.sr.fuelbuttons = uicls.ButtonGroup(btns=btns, parent=self.sr.main)
            self.sr.fuelbuttons.state = uiconst.UI_HIDDEN
            btns = [(localization.GetByLabel('UI/Inflight/POS/AssumeStructureControl'),
              self.AssumeControl,
              (),
              84), (localization.GetByLabel('UI/Inflight/POS/RelinquishPOSControl'),
              self.RelinquishControl,
              (),
              84)]
            self.sr.controlbuttons = uicls.ButtonGroup(btns=btns, parent=self.sr.main, unisize=0)
            self.sr.controlbuttons.state = uiconst.UI_HIDDEN
            self.sr.accesspanel = uicls.Container(name='access', align=uiconst.TOBOTTOM, state=uiconst.UI_HIDDEN, height=56, parent=self.sr.main)
            self.sr.scroll = uicls.Scroll(name='structures', align=uiconst.TOALL, parent=self.sr.main, padding=(const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding))
            self.sr.scroll.sr.id = 'moonmining'
            self.sr.scroll.selectionScrolling = False
            content = self.sr.scroll.sr.content
            content.OnDropData = self.OnTowerDropData
            self.sr.standingspanel = uicls.Container(name='standings', align=uiconst.TOALL, state=uiconst.UI_HIDDEN, parent=self.sr.main, pos=(0, 0, 0, 0))
            self.sr.forcefieldpanel = uicls.Container(name='forcefield', align=uiconst.TOALL, state=uiconst.UI_HIDDEN, parent=self.sr.main, pos=(0, 0, 0, 0))
            self.sr.structurepanel = uicls.Container(name='structure', align=uiconst.TOALL, state=uiconst.UI_HIDDEN, parent=self.sr.main, pos=(0, 0, 0, 0))
            self.sr.processpanel = uicls.Container(name='structure', align=uiconst.TOALL, state=uiconst.UI_HIDDEN, parent=self.sr.main, pos=(0, 0, 0, 0))
            tabs = []
            structuretabs = []
            processtabs = []
            if eve.session.corprole & const.corpRoleStarbaseConfig:
                forceFieldLabel = localization.GetByLabel('UI/Generic/General')
                defenseLabel = localization.GetByLabel('UI/Inflight/MoonMining/Defense/Defense')
                tabs = [[forceFieldLabel,
                  self.sr.forcefieldpanel,
                  self,
                  ('force', None)], [defenseLabel,
                  self.sr.standingspanel,
                  self,
                  ('standings', None)]]
            if (const.corpRoleStarbaseConfig | const.corpRoleStarbaseCaretaker | const.corpRoleInfrastructureTacticalOfficer) & eve.session.corprole:
                structuresLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/Structures')
                tabs.extend([[structuresLabel,
                  self.sr.structurepanel,
                  self,
                  ('structures', None)]])
                if (const.corpRoleStarbaseConfig | const.corpRoleStarbaseCaretaker) & eve.session.corprole:
                    processesLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/Processes')
                    tabs.extend([[processesLabel,
                      self.sr.processpanel,
                      self,
                      ('process', None)]])
                    jumpBridgesLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/JumpBridges')
                    structuretabs.extend([[structuresLabel,
                      self.sr.scroll,
                      self,
                      ('structures_structures', 'structures'),
                      self.sr.structuresbuttons], [jumpBridgesLabel,
                      self.sr.scroll,
                      self,
                      ('structures_jumpbridges', 'jumpbridges')]])
                    if const.corpRoleStarbaseConfig & eve.session.corprole:
                        controlTowersLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/ControlTowers')
                        noOtherStructuresLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/NoOtherNamedStructures')
                        cachedFor5MinLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/CachedFor5Min')
                        structuretabs.extend([[controlTowersLabel,
                          self.sr.scroll,
                          self,
                          ('structures_othertowers', 'othertowers'),
                          None,
                          noOtherStructuresLabel + '<br><br>' + cachedFor5MinLabel]])
                    fuelLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/Fuel')
                    productionLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/Production')
                    processtabs.extend([[fuelLabel,
                      self.sr.scroll,
                      self,
                      ('process_fuel', 'fuel'),
                      self.sr.fuelbuttons], [productionLabel,
                      self.sr.scroll,
                      self,
                      ('process_production', 'production'),
                      self.sr.productionbuttons]])
                if eve.session.corprole & const.corpRoleStarbaseConfig:
                    accessLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/Access')
                    structuretabs.insert(1, [accessLabel,
                     self.sr.scroll,
                     self,
                     ('structures_access', 'access'),
                     self.sr.accesspanel])
                if eve.session.corprole & const.corpRoleInfrastructureTacticalOfficer:
                    label = localization.GetByLabel('UI/Inflight/MoonMining/Structures/Control')
                    structuretabs.insert(2, [label,
                     self.sr.scroll,
                     self,
                     ('structures_control', 'control'),
                     self.sr.controlbuttons])
            self.SetMinSize([MINWNDWIDTH, 378])
            self.sr.structuretabs = uicls.TabGroup(name='structuretabs', parent=self.sr.main, idx=1)
            self.sr.processtabs = uicls.TabGroup(name='processtabs', parent=self.sr.main, idx=1)
            self.sr.maintabs = uicls.TabGroup(name='tabparent', parent=self.sr.main, idx=1)
            self.sr.maintabs.Startup(tabs, 'pospanel', autoselecttab=0)
            self.sr.structuretabs.Startup(structuretabs, 'moonminingstructuretabs', autoselecttab=0)
            self.sr.processtabs.Startup(processtabs, 'moonminingprocesstabs', autoselecttab=0)
            self.sr.maintabs.AutoSelect()
            self.invReady = 1
            if slimItem:
                self.sr.updateTimer = base.AutoTimer(1000, self.UpdateDamage)
                self.UpdateStructures()
        except UserError:
            raise 
        except:
            log.LogWarn('Initializing moonmining window failed ... closed before complete ?')

    def _OnClose(self, *args):
        self.godma = None
        self.posMgr = None
        self.slimItem = None
        self.capacity = None
        self.tower = None

    def OnTabDeselect(self):
        if self.connectionsChanged:
            if eve.Message('ApplyStructureConnections', {}, uiconst.YESNO) == uiconst.ID_YES:
                self.ProdApply()
            self.connectionsChanged = 0

    def Load(self, args):
        key, flag = args
        if self.sr.Get('cookie', None) is not None:
            sm.GetService('inv').Unregister(self.sr.cookie)
            self.sr.cookie = None
        if key in ('standings', 'force'):
            self.sr.fuelbuttons.state = uiconst.UI_HIDDEN
            self.sr.productionbuttons.state = uiconst.UI_HIDDEN
            self.sr.structuresbuttons.state = uiconst.UI_HIDDEN
            self.sr.accesspanel.state = uiconst.UI_HIDDEN
            self.sr.controlbuttons.state = uiconst.UI_HIDDEN
        if key == 'structures':
            self.sr.structuretabs.state = uiconst.UI_NORMAL
            self.sr.processtabs.state = uiconst.UI_HIDDEN
            self.sr.structuretabs.AutoSelect()
            self.sr.fuelbuttons.state = uiconst.UI_HIDDEN
            self.sr.productionbuttons.state = uiconst.UI_HIDDEN
        elif key[:11] == 'structures_':
            self.ShowStructureTab(flag)
        elif key == 'process':
            self.sr.structuretabs.state = uiconst.UI_HIDDEN
            self.sr.processtabs.state = uiconst.UI_NORMAL
            self.sr.processtabs.AutoSelect()
            self.sr.structuresbuttons.state = uiconst.UI_HIDDEN
            self.sr.accesspanel.state = uiconst.UI_HIDDEN
            self.sr.controlbuttons.state = uiconst.UI_HIDDEN
        elif key[:8] == 'process_':
            self.ShowProcessTab(flag)
        elif key == 'standings':
            self.sr.structuretabs.state = uiconst.UI_HIDDEN
            self.sr.processtabs.state = uiconst.UI_HIDDEN
            self.sr.scroll.state = uiconst.UI_HIDDEN
            self.ShowStandings()
        elif key == 'force':
            self.sr.structuretabs.state = uiconst.UI_HIDDEN
            self.sr.processtabs.state = uiconst.UI_HIDDEN
            self.sr.scroll.state = uiconst.UI_HIDDEN
            self.ShowForce()

    def ShowStructureTab(self, flag):
        self.sr.scroll.ShowHint('')
        self.sr.scroll.multiSelect = 0
        if flag == 'access':
            self.ShowAccess()
        elif flag == 'control':
            self.sr.scroll.multiSelect = 1
            self.ShowControl()
        elif flag == 'structures':
            self.ShowStructures()
        elif flag == 'othertowers':
            self.ShowOtherTowers()
        elif flag == 'jumpbridges':
            self.sr.scroll.state = uiconst.UI_HIDDEN
            self.ShowJumpBridges()

    def ShowProcessTab(self, flag):
        if flag == 'production':
            self.ShowProduction()
        elif flag == 'fuel':
            self.ShowFuel()

    def ShowJumpBridges(self):
        jb = sm.RemoteSvc('posMgr').GetJumpArrays()
        aconnect = []
        uconnect = []
        structureConnections = {}
        if self.sr.Get('showing', '') != 'jumpbridges' or len(jb) != len(self.sr.scroll.GetNodes()):
            scrolllist = []
            for data in jb:
                solarSystemID, subData = data
                if subData:
                    aconnect.append(data)
                    ssid = subData.keys()[0]
                    tsid = subData.values()[0][1]
                    if ssid not in structureConnections and tsid not in structureConnections:
                        structureConnections[ssid] = tsid
                else:
                    uconnect.append(data)

            scrolllist = self.GetJumpbridgeEntries(aconnect, uconnect, structureConnections)
            if not len(scrolllist):
                self.sr.scroll.ShowHint(localization.GetByLabel('UI/Inflight/MoonMining/Structures/NoJumpBridges'))
            self.sr.scroll.state = uiconst.UI_NORMAL
            self.sr.scroll.sr.id = 'moonmining_jumpbridges'
            self.sr.scroll.Load(contentList=scrolllist)
        self.sr.showing = 'jumpbridges'

    def GetJumpbridgeEntries(self, aconnect, uconnect, structureConnections):
        myShip = sm.services['godma'].GetItem(eve.session.shipid)
        ul = [localization.GetByLabel('UI/Inflight/MoonMining/Structures/Linked'), localization.GetByLabel('UI/Inflight/MoonMining/Structures/Unlinked')]
        gid = ['ui_22_32_57', 'ui_22_32_58']
        scrolllist = []
        i = 0
        if aconnect or uconnect:
            cachedFor5MinLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/CachedFor5Min')
            scrolllist.append(listentry.Get('Text', {'text': cachedFor5MinLabel,
             'line': 1}))
            scrolllist.append(listentry.Get('Divider'))
        for entrylist in (aconnect, uconnect):
            if entrylist:
                scrolllist.append(listentry.Get('Header', {'label': ul[i]}))
                for fromSystem, solarSystemData in entrylist:
                    fromSystem = cfg.evelocations.Get(fromSystem)
                    fromStructure = toSystem = toStructure = None
                    data = util.KeyVal()
                    data.icon = gid[i]
                    data.line = 1
                    hint = ''
                    if solarSystemData:
                        fromStructure = solarSystemData.keys()[0]
                        toSystem = cfg.evelocations.Get(solarSystemData.values()[0][0])
                        toStructure = solarSystemData.values()[0][1]
                        toStructureType = solarSystemData.values()[0][2]
                    if solarSystemData and fromStructure not in structureConnections:
                        continue
                    if solarSystemData:
                        label = localization.GetByLabel('UI/Inflight/MoonMining/Structures/JumpBridgeLinkedState', source=fromSystem.name, destination=toSystem.name)
                        requiredQty = 0
                        if eve.session.shipid and toStructureType:
                            requiredQty, requiredType = sm.GetService('menu').GetFuelConsumptionOfJumpBridgeForMyShip(fromSystem, toSystem, toStructureType)
                        text = localization.GetByLabel('UI/Inflight/MoonMining/Structures/JumpBridgeDistanceConsumption', distance=uix.GetLightYearDistance(fromSystem, toSystem, False), amount=int(requiredQty), fuelTypeID=int(requiredType))
                        hint = localization.GetByLabel('UI/Inflight/MoonMining/Structures/JumpBridgeConsumptionForShip', distanceConsumption=text, shipTypeID=myShip.typeID)
                    else:
                        label = fromSystem.name
                        distance = uix.GetLightYearDistance(cfg.evelocations.Get(eve.session.solarsystemid), fromSystem)
                        if distance is None:
                            text = localization.GetByLabel('UI/Inflight/MoonMining/Structures/JumpBridgeUnlinkedStateUnknownDistance')
                        else:
                            text = localization.GetByLabel('UI/Inflight/MoonMining/Structures/JumpBridgeUnlinkedState', distance=distance)
                    data.itemID = fromSystem.locationID
                    data.typeID = const.typeSolarSystem
                    data.label = label
                    data.text = text
                    if hint:
                        data.hint = hint
                    data.fromSystem = fromSystem
                    data.toSystem = toSystem
                    scrolllist.append(listentry.Get('LabelTextTop', data=data))

            i = i + 1

        return scrolllist

    def ShowOtherTowers(self):
        ct = sm.RemoteSvc('posMgr').GetControlTowers()
        if self.sr.Get('showing', '') != 'othertowers' or len(ct) != len(self.sr.scroll.GetNodes()):
            scrolllist = []
            sollist = {}
            primeloc = []
            if ct:
                for row in ct:
                    typeID, structureID, solarSystemID = row[0:3]
                    if structureID == self.slimItem.itemID:
                        continue
                    primeloc.append(structureID)
                    if not sollist.has_key(solarSystemID):
                        sollist[solarSystemID] = [(typeID, structureID)]
                    else:
                        sollist[solarSystemID].append((typeID, structureID))

                cfg.evelocations.Prime(primeloc)
            if sollist:
                for solarSystemID, structureIDs in sollist.iteritems():
                    jumps = int(sm.GetService('pathfinder').GetJumpCountFromCurrent(solarSystemID))
                    label = localization.GetByLabel('UI/Inflight/MoonMining/Structures/SolarSystemNameAndJumps', solarsystemID=solarSystemID, structureQuantity=len(structureIDs), jumps=jumps)
                    data = {'GetSubContent': self.GetTowerGroupSubContent,
                     'label': label,
                     'id': ('TowerSel', solarSystemID),
                     'groupItems': structureIDs,
                     'toSystem': solarSystemID,
                     'iconMargin': 2,
                     'showlen': 0,
                     'sublevel': 0,
                     'state': 'locked'}
                    scrolllist.append(listentry.Get('Group', data))

                scrolllist = localizationUtil.Sort(scrolllist, key=lambda x: x.label)
            headers = [localization.GetByLabel('UI/Common/Name'), localization.GetByLabel('UI/Common/Type'), localization.GetByLabel('UI/Common/Distance')]
            if not len(scrolllist):
                self.sr.scroll.ShowHint(localization.GetByLabel('UI/Inflight/MoonMining/Structures/NoOtherControlTowers'))
                headers = []
            self.sr.scroll.state = uiconst.UI_NORMAL
            self.sr.scroll.sr.id = 'moonmining_othertowers'
            self.sr.scroll.Load(contentList=scrolllist, headers=headers)
        self.sr.showing = 'othertowers'

    def GetTowerGroupSubContent(self, nodedata, newitems = 0):
        scrolllist = []
        fromSystem = cfg.evelocations.Get(eve.session.solarsystemid)
        for typeID, itemID in nodedata.groupItems:
            toSystem = cfg.evelocations.Get(nodedata.toSystem)
            dist = uix.GetLightYearDistance(fromSystem, toSystem)
            if dist is None:
                distanceInLightYearsLabel = localization.GetByLabel('UI/Standings/Unknown')
            else:
                distanceInLightYearsLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/DistanceInLightYears', distance=dist)
            invType = cfg.invtypes.Get(typeID)
            locName = cfg.evelocations.Get(itemID).name
            lbl = invType.name
            data = util.KeyVal()
            data.label = '%s<t>%s<t>%s' % (locName or lbl, lbl, distanceInLightYearsLabel)
            data.listvalue = typeID
            data.id = ('TowerSel', itemID)
            data.typeID = const.typeSolarSystem
            data.itemID = nodedata.toSystem
            data.sublevel = 1
            data.Set('sort_%s' % localization.GetByLabel('UI/Common/Name'), locName or lbl)
            data.Set('sort_%s' % localization.GetByLabel('UI/Common/Type'), lbl)
            data.Set('sort_%s' % localization.GetByLabel('UI/Common/Distance'), dist)
            scrolllist.append(listentry.Get('Generic', data=data))

        return localizationUtil.Sort(scrolllist, key=lambda x: x.label)

    def ShowControl(self):
        bp = sm.GetService('michelle').GetBallpark()
        if bp:
            structures = [ rec for itemID, rec in bp.slimItems.iteritems() if rec.categoryID == const.categoryStructure and rec.groupID != const.groupControlTower and rec.ownerID == self.slimItem.ownerID ]
        scrolllist = []
        for structure in structures:
            controllable = [ each for each in cfg.dgmtypeattribs.get(structure.typeID, []) if each.attributeID == const.attributePosPlayerControlStructure ]
            if controllable:
                controllerID, controllerName = sm.GetService('pwn').GetControllerIDName(structure.itemID)
                state = sm.GetService('pwn').GetStructureState(structure)
                data = {'label': [uix.GetSlimItemName(structure),
                           '<t>',
                           entities.POS_STRUCTURE_STATE[state[0]],
                           '<t>',
                           controllerName],
                 'rec': structure,
                 'state': state[0],
                 'GetMenu': self.GetStructureMenu,
                 'StructureProgress': self.StructureProgress,
                 'args': (None,)}
                scrolllist.append(listentry.Get('StructureControl', data))

        if not len(scrolllist):
            self.sr.scroll.ShowHint(localization.GetByLabel('UI/Inflight/MoonMining/Structures/NoOtherStructuresInRange'))
        self.sr.scroll.sr.ignoreTabTrimming = False
        self.sr.scroll.sr.id = 'moonmining_control'
        nameLabel = localization.GetByLabel('UI/Common/Name')
        structureStateLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/StructureState')
        controlLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/Control')
        self.sr.scroll.Load(contentList=scrolllist, headers=[nameLabel, structureStateLabel, controlLabel])
        self.sr.showing = 'control'

    def ShowStructures(self):
        import listentry
        bp = sm.GetService('michelle').GetBallpark()
        if bp:
            structures = [ rec for itemID, rec in bp.slimItems.iteritems() if rec.categoryID == const.categoryStructure and rec.groupID != const.groupControlTower and rec.ownerID == self.slimItem.ownerID ]
        if self.sr.Get('showing', '') != 'structures' or len(structures) != len(self.sr.scroll.GetNodes()):
            scrolllist = []
            for structure in structures:
                state = sm.GetService('pwn').GetStructureState(structure)
                cpu = self.godma.GetType(structure.typeID).cpu
                power = self.godma.GetType(structure.typeID).power
                data = util.KeyVal()
                data.label = '%s<t>%s<t><right>%s<t><right>%s' % (uix.GetSlimItemName(structure),
                 entities.POS_STRUCTURE_STATE[state[0]],
                 localization.GetByLabel('UI/Inflight/MoonMining/Structures/DisplayPowerUsage', powerUsage=power),
                 localization.GetByLabel('UI/Inflight/MoonMining/Structures/DisplayCPUUsage', cpuUsage=cpu))
                data.rec = structure
                data.state = state[0]
                data.GetMenu = self.GetStructureMenu
                data.StructureProgress = self.StructureProgress
                data.power = power
                data.cpu = cpu
                data.Set('sort_%s' % localization.GetByLabel('UI/Inflight/MoonMining/Structures/StructureState'), entities.POS_STRUCTURE_STATE[state[0]])
                data.Set('sort_%s' % localization.GetByLabel('UI/Common/Power'), power)
                data.Set('sort_%s' % localization.GetByLabel('UI/Common/Cpu'), cpu)
                scrolllist.append(listentry.Get('Structure', data=data))

            if not len(scrolllist):
                self.sr.scroll.ShowHint(localization.GetByLabel('UI/Inflight/MoonMining/Structures/NoOtherStructuresInRange'))
            self.sr.scroll.sr.ignoreTabTrimming = False
            self.sr.scroll.sr.id = 'moonmining_structures'
            nameLabel = localization.GetByLabel('UI/Common/Name')
            structureStateLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/StructureState')
            powerLabel = localization.GetByLabel('UI/Common/Power')
            cpuLabel = localization.GetByLabel('UI/Common/Cpu')
            self.sr.scroll.Load(contentList=scrolllist, headers=[nameLabel,
             structureStateLabel,
             powerLabel,
             cpuLabel])
        for entry in self.sr.scroll.GetNodes():
            for rec in structures:
                if rec.itemID == entry.rec.itemID and rec != entry.rec:
                    entry.rec = rec
                    if entry.panel:
                        entry.panel.UpdateState()
                    break

        self.sr.showing = 'structures'

    def ShowProduction(self, force = 0):
        cycle = self.godma.GetType(self.slimItem.typeID).posControlTowerPeriod
        scrolllist = []
        scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Inflight/MoonMining/Processes/MoonProduces')}))
        for typeID, quantity in self.res.iteritems():
            label = localization.GetByLabel('UI/Inflight/MoonMining/Processes/MoonProduct', itemTypeID=typeID, quantity=quantity, unitsProduced=self.godma.GetType(typeID).moonMiningAmount, cycleTime=cycle / 60000)
            data = {'label': label,
             'typeID': typeID,
             'GetMenu': self.GetTypeMenu}
            scrolllist.append(listentry.Get('Generic', data))

        if len(scrolllist) == 1:
            if sm.GetService('pwn').GetStructureState(self.slimItem)[0].startswith('online'):
                noHarvestableResourcesLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/NoHarvestableResources')
                scrolllist.append(listentry.Get('Generic', {'label': noHarvestableResourcesLabel,
                 'height': 24}))
            else:
                mineralScanImpossibleLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/MineralScanImpossible')
                scrolllist.append(listentry.Get('Generic', {'label': mineralScanImpossibleLabel,
                 'height': 24}))
        scrolllist.append(listentry.Get('Header', {'label': localization.GetByLabel('UI/Inflight/MoonMining/Processes/ProcessControl')}))
        structures = self.GetProductionStructures(force)
        self.EvalStructureConnections()
        keys = structures.keys()
        s = {const.groupMoonMining: 1,
         const.groupMobileReactor: 2,
         const.groupSilo: 3}
        keys.sort(lambda x, y: s[structures[x].rec.groupID] - s[structures[y].rec.groupID])
        if not len(keys):
            noAnchoredStructuresFoundLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/NoAnchoredStructuresFound')
            scrolllist.append(listentry.Get('Generic', {'label': noAnchoredStructuresFoundLabel}))
        for itemID in keys:
            structure = structures[itemID]
            r = {}
            p = {}
            connected = 1
            for typeID, q in structure.demands.items():
                pItemID = None
                demands = self.GetMaxDemands(itemID)
                if typeID not in demands:
                    continue
                quantity = demands[typeID]
                for k in self.sr.structureConnections:
                    if self.sr.structureConnections[k] == itemID and k[0] == typeID and k[1] in keys:
                        pItemID = k[1]
                        break

                if pItemID is not None:
                    if self.sr.resEval.has_key(itemID) and self.sr.resEval[itemID].has_key(typeID):
                        r[typeID] = (quantity,
                         self.sr.resEval[itemID][typeID][0],
                         self.sr.resEval[itemID][typeID][1],
                         structures[pItemID].color,
                         pItemID)
                    else:
                        connected = 0
                        r[typeID] = (quantity,
                         -1,
                         -1,
                         structures[pItemID].color,
                         pItemID)
                else:
                    connected = 0
                    r[typeID] = (quantity,
                     -1,
                     -1,
                     (1.0, 1.0, 1.0, 0.25),
                     None)

            for typeID, q in structure.supplies.items():
                supplies = self.GetMaxSupplies(itemID)
                if typeID not in supplies:
                    continue
                quantity = supplies[typeID]
                if self.sr.structureConnections.has_key((typeID, itemID)):
                    pItemID = self.sr.structureConnections[typeID, itemID]
                    if self.sr.resEval.has_key(pItemID) and self.sr.resEval[pItemID].has_key(typeID):
                        p[typeID] = (quantity,
                         self.sr.resEval[pItemID][typeID][0],
                         self.sr.resEval[pItemID][typeID][1],
                         structure.color,
                         pItemID)
                    else:
                        connected = 0
                        p[typeID] = (quantity,
                         -1,
                         -1,
                         structure.color,
                         pItemID)
                else:
                    connected = 0
                    p[typeID] = (quantity,
                     -1,
                     -1,
                     structure.color,
                     None)

            state = sm.GetService('pwn').GetStructureState(structure.rec)[0]
            if state == 'online' and connected:
                state = '%s - %s' % (state, ['starting up', 'active'][structure.active])
            data = {'label': '',
             'label2': uix.GetSlimItemName(structure.rec),
             'color': structure.color,
             'resources': r,
             'products': p,
             'slimitem': structure.rec,
             'state': state,
             'structurecallback': self.StructureCallback,
             'settype': self.SetStructureType,
             'connected': connected,
             'cycle': cycle,
             'scrollObject': self.sr.scroll}
            if structure.rec.groupID == const.groupMoonMining:
                if len(p) and state.startswith('anchored'):
                    for key in p:
                        v = p[key]
                        if self.res.has_key(key):
                            p[key] = (min(self.godma.GetType(structure.rec.typeID).harvesterQuality, self.res[key]),
                             v[1],
                             v[2],
                             v[3],
                             v[4])

                scrolllist.append(listentry.Get('Harvester', data))
            elif structure.rec.groupID == const.groupSilo:
                data['reaction'] = structure.reaction
                scrolllist.append(listentry.Get('Silo', data))
            elif structure.rec.groupID == const.groupMobileReactor:
                data['reaction'] = structure.reaction
                data['ReactionChanged'] = self.ReactionChanged
                scrolllist.append(listentry.Get('Reactor', data))

        self.sr.scroll.ShowHint()
        self.sr.scroll.sr.id = 'moonmining_production'
        self.sr.scroll.Load(contentList=scrolllist, scrollTo=self.sr.scroll.GetScrollProportion())
        self.sr.showing = 'production'

    def ShowStandings(self):
        if not self.sr.Get('standingsinited', 0):
            self.InitStandingsPanel()
        standing, status, statusDrop, war, standingOwnerID = self.sentrySettings = self.posMgr.GetTowerSentrySettings(self.slimItem.itemID)
        self.sentrySettings = self.sentrySettings['line']
        if session.allianceid is not None and standingOwnerID == session.allianceid:
            self.sr.alliancestandingcheckbox.SetChecked(1, 0)
        else:
            self.sr.alliancestandingcheckbox.SetChecked(0, 0)
        if standing is not None:
            self.sr.standingcheckbox1.SetChecked(1, 0)
            self.sr.standingedit1.SetValue(standing)
        else:
            self.sr.standingcheckbox1.SetChecked(0, 0)
            self.sr.standingedit1.SetValue(0.0)
        if status is not None:
            self.sr.standingcheckbox2.SetChecked(1, 0)
            self.sr.standingedit2.SetValue(status)
        else:
            self.sr.standingcheckbox2.SetChecked(0, 0)
            self.sr.standingedit2.SetValue(0.0)
        self.sr.standingcheckbox4.SetChecked(statusDrop, 0)
        self.sr.standingcheckbox6.SetChecked(war, 0)
        self.sr.showing = 'standings'

    def ShowForce(self):
        if not self.sr.Get('forcefieldinited', 0):
            self.InitForcefieldPanel()
        if not eve.session.allianceid:
            self.sr.forcefieldcheckbox2.state = uiconst.UI_HIDDEN
        forcefield = self.GetForcefield()
        bp = sm.GetService('michelle').GetBallpark()
        ball = bp.GetBall(forcefield.itemID)
        log.LogInfo('Forcefield harmonic', ball.harmonic)
        if ball.harmonic not in (0, -1):
            self.sr.forcefieldtext1.text = localization.GetByLabel('UI/Inflight/MoonMining/ForceField/ForceFieldActive')
        else:
            self.sr.forcefieldtext1.text = localization.GetByLabel('UI/Inflight/MoonMining/ForceField/ForceFieldInactive')
        self.sr.forcefieldcheckbox1.SetChecked([0, 1][ball.corporationID != -1], 0)
        self.sr.forcefieldcheckbox2.SetChecked([0, 1][ball.allianceID != -1], 0)
        notifySettings = self.posMgr.GetTowerNotificationSettings(self.slimItem.itemID)
        self.fuelNotifyCheckbox.SetChecked(notifySettings.sendFuelNotifications, 0)
        self.calendarCheckbox.SetChecked(notifySettings.showInCalendar, 0)
        self.notifySettings = notifySettings

    def ShowFuel(self):
        if self.sr.Get('cookie', None) is None:
            self.sr.cookie = sm.GetService('inv').Register(self)
        if self.sr.Get('restypes', None) is None:
            self.sr.restypes = {}
        consumefactor = 1.0
        sovInfo = sm.RemoteSvc('sovMgr').GetSystemSovereigntyInfo(session.solarsystemid2)
        ssAllianceID = sovInfo.allianceID if sovInfo else None
        if eve.session.allianceid and eve.session.allianceid == ssAllianceID:
            consumefactor = 0.75
        securityRating = 0.0
        systemItem = sm.GetService('map').GetItem(session.solarsystemid2)
        factionID = None
        wormholeClassID = cfg.GetLocationWormholeClass(session.solarsystemid2, session.constellationid, session.regionid)
        if systemItem is not None:
            factionID = systemItem.factionID
            securityRating = systemItem.security
        scrolllist = []
        try:
            container = self.tower.List()
            cycle = self.godma.GetType(self.slimItem.typeID).posControlTowerPeriod
            res = {}
            for row in container:
                if res.has_key(row.typeID):
                    res[row.typeID] += row.stacksize
                else:
                    res[row.typeID] = row.stacksize

            state = sm.GetService('pwn').GetStructureState(self.slimItem)[0]
            l = [(1, localization.GetByLabel('Entities/States/Online')),
             (2, localization.GetByLabel('UI/Common/Power')),
             (3, localization.GetByLabel('UI/Common/Cpu')),
             (4, localization.GetByLabel('Entities/States/Reinforced'))]
            rs = sm.RemoteSvc('posMgr').GetControlTowerFuelRequirements()
            controlTowerResourcesByTypePurpose = {}
            for entry in rs:
                if not controlTowerResourcesByTypePurpose.has_key(entry.controlTowerTypeID):
                    controlTowerResourcesByTypePurpose[entry.controlTowerTypeID] = {entry.purpose: [entry]}
                elif not controlTowerResourcesByTypePurpose[entry.controlTowerTypeID].has_key(entry.purpose):
                    controlTowerResourcesByTypePurpose[entry.controlTowerTypeID][entry.purpose] = [entry]
                else:
                    controlTowerResourcesByTypePurpose[entry.controlTowerTypeID][entry.purpose].append(entry)

            for purposeID, caption in l:
                if controlTowerResourcesByTypePurpose.has_key(self.slimItem.typeID):
                    if controlTowerResourcesByTypePurpose[self.slimItem.typeID].has_key(purposeID):
                        tempList = []
                        for each in controlTowerResourcesByTypePurpose[self.slimItem.typeID][purposeID]:
                            tempList.append(each)

                        tempList = localizationUtil.Sort(tempList, key=lambda x: cfg.invtypes.Get(x.resourceTypeID).name)
                        for row in tempList:
                            typeID = row.resourceTypeID
                            if row.factionID is not None and row.factionID != factionID:
                                continue
                            if row.minSecurityLevel is not None and row.minSecurityLevel > securityRating:
                                continue
                            if row.wormholeClassID is not None and row.wormholeClassID != wormholeClassID:
                                continue
                            if not self.sr.restypes.has_key(typeID):
                                self.sr.restypes[typeID] = {'label': cfg.invtypes.Get(row.resourceTypeID).name,
                                 'volume': self.godma.GetType(row.resourceTypeID).volume}
                            factor = 0.0
                            if caption == localization.GetByLabel('Entities/States/Online'):
                                factor = 1.0
                            if caption == localization.GetByLabel('Entities/States/Reinforced'):
                                factor = 1.0
                                capacityToUse = self.capacitySecondary
                            else:
                                capacityToUse = self.capacity
                            if caption == localization.GetByLabel('UI/Common/Power') and self.sr.powerSupply != 0:
                                factor = 1.0 * self.sr.powerConsumption / self.sr.powerSupply
                            elif caption == localization.GetByLabel('UI/Common/Cpu') and self.sr.cpuSupply != 0:
                                factor = 1.0 * self.sr.cpuConsumption / self.sr.cpuSupply
                            label = self.sr.restypes[typeID]['label']
                            text = int(math.ceil(row.quantity * factor * consumefactor))
                            capacity = capacityToUse
                            quantity = res.get(row.resourceTypeID, 0)
                            size = self.sr.restypes[typeID]['volume']
                            typeid = row.resourceTypeID
                            data = util.KeyVal()
                            quantity2 = max(text, 1.0)
                            if factor == 0.0:
                                cyclestext = localization.GetByLabel('UI/Inflight/MoonMining/Processes/UnusedFuel')
                            else:
                                cyclestext = long(int(quantity / quantity2) * cycle * 10000L)
                                data.Set('sort_%s' % localization.GetByLabel('UI/Inflight/MoonMining/Processes/TimeLeft'), cyclestext)
                                cyclestext = util.FmtDate(cyclestext, 'ss')
                            label = '%s<t>%s<t><right>%s<t><right>%s<t><right>%s' % (caption,
                             label,
                             text,
                             quantity,
                             cyclestext)
                            data.label = data.name = label
                            data.showinfo = 1
                            data.typeID = typeid
                            data.OnDropData = self.OnTowerDropData
                            le = listentry.Get('Generic', data=data)
                            fuelPurposeLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/FuelPurpose')
                            nameLabel = localization.GetByLabel('UI/Common/Name')
                            quantityPerCycleLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/QuantityPerCycle')
                            quantityPresentLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/QuantityPresent')
                            timeLeftLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/TimeLeft')
                            headers = [fuelPurposeLabel,
                             nameLabel,
                             quantityPerCycleLabel,
                             quantityPresentLabel,
                             timeLeftLabel]
                            headers = [ each.replace('(', '<br>(') for each in headers ]
                            scrolllist.append(le)

        except Exception as e:
            sys.exc_clear()

        self.sr.scroll.ShowHint()
        if not len(scrolllist):
            self.sr.scroll.ShowHint(localization.GetByLabel('UI/Inflight/MoonMining/Processes/TooFarAwayFromControlTower'))
            headers = []
        self.sr.scroll.sr.id = 'moonmining_fuel'
        self.sr.scroll.Load(contentList=scrolllist, headers=headers)
        self.sr.showing = 'fuel'

    def ShowAccess(self):
        if not len(self.sr.accesspanel.children):
            options = [(localization.GetByLabel('UI/Inflight/MoonMining/Structures/RoleConfigStarbaseEquipment'), 0),
             (localization.GetByLabel('UI/Inflight/MoonMining/Structures/RoleStarbaseFuelTechnician'), 3),
             (localization.GetByLabel('UI/Common/Corporation'), 1),
             (localization.GetByLabel('UI/Common/Alliance'), 2)]
            self.sr.accessconfig = {}
            i = 5
            for config in ['anchor',
             'unanchor',
             'online',
             'offline']:
                self.sr.accessconfig[config] = uicls.Combo(label=entities.POS_STRUCTURE_STATE[config], parent=self.sr.accesspanel, options=options, name=config, pos=(i + 5,
                 10,
                 0,
                 0), align=uiconst.TOPLEFT)
                self.sr.accessconfig[config].width = 110
                i += 120

            btns = [(localization.GetByLabel('UI/Common/Buttons/Apply'),
              self.SaveAccess,
              (),
              84)]
            uicls.ButtonGroup(btns=btns, parent=self.sr.accesspanel)
        deployFlags, usageFlagsList = self.posMgr.GetStarbasePermissions(self.slimItem.itemID)
        self.sr.deployFlags = deployFlags
        self.sr.usageFlagsList = usageFlagsList
        self.sr.usageFlags = usageFlagsList.Index('structureID')
        for key in ['anchor',
         'unanchor',
         'online',
         'offline']:
            self.sr.accessconfig[key].SelectItemByValue(deployFlags[key])

        viewAccessLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/ViewAccess')
        takeAccessLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/TakeAccess')
        useAccessLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/UseAccess')
        self.sr.scroll.sr.fixedColumns = {viewAccessLabel: 105,
         takeAccessLabel: 105,
         useAccessLabel: 105}
        self.sr.scroll.OnColumnChanged = self.OnAccessColumnChanged
        if self.sr.Get('showing', '') != 'access':
            bp = sm.GetService('michelle').GetBallpark()
            scrolllist = []
            if bp:
                for structureID in self.sr.usageFlags:
                    data = {'label': uix.GetSlimItemName(bp.slimItems[structureID]),
                     'rec': bp.slimItems[structureID],
                     'flags': self.sr.usageFlags[structureID]}
                    scrolllist.append(listentry.Get('StructureAccess', data))

            if not len(scrolllist):
                self.sr.scroll.ShowHint(localization.GetByLabel('UI/Inflight/MoonMining/Structures/NoOtherStructuresInRange'))
            self.sr.scroll.sr.ignoreTabTrimming = False
            self.sr.scroll.sr.id = 'moonmining_access'
            nameLabel = localization.GetByLabel('UI/Common/Name')
            viewAccessLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/ViewAccess')
            takeAccessLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/TakeAccess')
            useAccessLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/UseAccess')
            self.sr.scroll.Load(contentList=scrolllist, headers=[nameLabel,
             viewAccessLabel,
             takeAccessLabel,
             useAccessLabel])
            self.OnAccessColumnChanged()
        self.sr.showing = 'access'

    def SaveAccess(self, *args):
        for config in ['anchor',
         'unanchor',
         'online',
         'offline']:
            self.sr.deployFlags[config] = self.sr.accessconfig[config].GetValue() or 0

        self.posMgr.SetStarbasePermissions(self.slimItem.itemID, self.sr.deployFlags, self.sr.usageFlagsList)

    def OnAccessColumnChanged(self, *args):
        for entry in self.sr.scroll.GetNodes():
            if entry.panel and getattr(entry.panel, 'OnColumnChanged', None):
                entry.panel.OnColumnChanged()

    def StructureProgress(self, where, label, stateTimestamp, stateDelay, parenttext = None, xoffset = 2, top = 3):
        sub = uicls.Container(name='progresscontainer', parent=where, align=uiconst.TOPRIGHT, width=88, height=12, left=xoffset, top=top)
        uicls.Frame(parent=sub, color=(1.0, 1.0, 1.0, 0.5))
        te = uicls.EveLabelSmall(text='xxx', parent=sub, width=86, left=2, top=0)
        p = uicls.Fill(parent=sub, align=uiconst.TOPLEFT, width=86, height=10, left=0, top=1, color=(1.0, 1.0, 1.0, 0.25))
        startTime = blue.os.GetWallclockTime()
        if stateDelay:
            stateDelay = float(stateDelay * 10000L)
        endTime = 0
        if stateDelay:
            endTime = stateTimestamp + stateDelay
        while 1 and endTime:
            timeLeft = endTime - blue.os.GetWallclockTime()
            portion = timeLeft / stateDelay
            timeLeftSec = timeLeft / 1000.0
            if timeLeft <= 0:
                parenttext.text = label
                break
            te.text = util.FmtDate(long(timeLeft), 'ss')
            p.width = int(86 * portion)
            blue.pyos.synchro.Yield()
            if parenttext.destroyed:
                return

        blue.pyos.synchro.SleepWallclock(250)
        uix.Flush(sub)
        del where.children[-1]
        if parenttext.destroyed:
            return
        parenttext.text = ''
        blue.pyos.synchro.SleepWallclock(250)
        if parenttext.destroyed:
            return
        parenttext.text = label
        blue.pyos.synchro.SleepWallclock(250)
        if parenttext.destroyed:
            return
        parenttext.text = ''
        blue.pyos.synchro.SleepWallclock(250)
        if parenttext.destroyed:
            return
        parenttext.text = label

    def AssumeControl(self):
        selected = self.sr.scroll.GetSelected()
        if not len(selected) > 0:
            return
        if sm.GetService('viewState').IsViewActive('planet'):
            raise UserError('StructureNotControllablePlanetMode')
        structures = []
        for sel in selected:
            slimItem = sel.rec
            uthread.pool('MoonMining::_AssumeControl', self._AssumeControl, slimItem)

    def _AssumeControl(self, itemID, silent = False):
        self.pwn.AssumeStructureControl(itemID, silent)

    def RelinquishControl(self):
        selected = self.sr.scroll.GetSelected()
        if not len(selected) > 0:
            return
        structures = []
        for sel in selected:
            slimItem = sel.rec
            uthread.pool('MoonMining::_RelinquishControl', self._RelinquishControl, slimItem)

    def _RelinquishControl(self, itemID):
        self.pwn.RelinquishStructureControl(itemID)

    def GetGauge(self, where = None, left = 0, top = 0, color = (1.0,
 1.0,
 1.0,
 0.25)):
        g = uicls.Container(name='gauge', align=uiconst.TOPLEFT, width=64, height=9, left=left, top=top, parent=where)
        uicls.Container(name='push', parent=g, align=uiconst.TOBOTTOM, height=2)
        g.name = ''
        uicls.Line(parent=g, align=uiconst.TOTOP, color=(1.0, 1.0, 1.0, 0.5))
        uicls.Line(parent=g, align=uiconst.TOBOTTOM, color=(1.0, 1.0, 1.0, 0.5))
        uicls.Line(parent=g, align=uiconst.TOLEFT, color=(1.0, 1.0, 1.0, 0.5))
        uicls.Line(parent=g, align=uiconst.TORIGHT, color=(1.0, 1.0, 1.0, 0.5))
        g.sr.bar = uicls.Fill(parent=g, align=uiconst.TOLEFT, color=color)
        uicls.Fill(parent=g, color=(1.0, 1.0, 1.0, 0.25))
        return g

    def UpdateHeader(self):
        if not self or self.destroyed or not self.slimItem:
            return
        state = self.pwn.GetStructureState(self.slimItem)
        statusText = entities.POS_STRUCTURE_STATE[state[0]]
        color = ''
        if statusText == localization.GetByLabel('Entities/States/Online'):
            color = '<color=0xff65c212>'
        elif statusText == localization.GetByLabel('UI/Inflight/MoonMining/Offline'):
            color = '<color=0xffd0371d>'
        self.sr.status.text = localization.GetByLabel('UI/Inflight/MoonMining/TowerStatus', colorCode=color, currentStatus=statusText)
        if self.moonID is not None:
            moonstr = cfg.evelocations.Get(self.moonID).name
        else:
            moonstr = localization.GetByLabel('UI/Inflight/MoonMining/NotAttachedToMoon', locationID=eve.session.locationid)
        self.sr.locationtext.text = localization.GetByLabel('UI/Inflight/MoonMining/TowerLocated', moonLocation=moonstr)
        if state[0] == 'online' and len(self.res) == 0:
            self.GetMoon()
        allowedState = (const.pwnStructureStateAnchoring,
         const.pwnStructureStateOnlining,
         const.pwnStructureStateUnanchoring,
         const.pwnStructureStateReinforced)
        if state[0] in allowedState:
            displayState = structProgressMap.get(state[0], None)
            if displayState:
                labelMap = {const.pwnStructureStateAnchored: localization.GetByLabel('Entities/States/StatusCaptionAnchored'),
                 const.pwnStructureStateUnanchored: localization.GetByLabel('Entities/States/StatusCaptionUnanchored'),
                 const.pwnStructureStateOnline: localization.GetByLabel('Entities/States/StatusCaptionOnline')}
                label = labelMap[displayState]
            else:
                label = localization.GetByLabel('Entities/States/StatusCaptionDone')
            uthread.new(self.StructureProgress, self.sr.locationtext.parent, label, state[1], state[2], self.sr.status, -78, self.sr.status.top - 12)
        self.UpdateDamage()
        bp = sm.GetService('michelle').GetBallpark()
        t = self.godma.GetType(self.slimItem.typeID)
        emRes = getattr(t, 'shieldEmDamageResonance', 1.0)
        exRes = getattr(t, 'shieldExplosiveDamageResonance', 1.0)
        kiRes = getattr(t, 'shieldKineticDamageResonance', 1.0)
        thRes = getattr(t, 'shieldThermalDamageResonance', 1.0)
        structures = [ rec for itemID, rec in bp.slimItems.iteritems() if rec.categoryID == const.categoryStructure and rec.groupID == const.groupShieldHardeningArray and rec.ownerID == self.slimItem.ownerID and self.pwn.GetStructureState(rec)[0] == 'online' ]
        for structure in structures:
            s = self.godma.GetType(structure.typeID)
            emRes *= getattr(s, 'emDamageResonanceMultiplier', 1.0)
            exRes *= getattr(s, 'explosiveDamageResonanceMultiplier', 1.0)
            kiRes *= getattr(s, 'kineticDamageResonanceMultiplier', 1.0)
            thRes *= getattr(s, 'thermalDamageResonanceMultiplier', 1.0)

        emPercentageLabel = localization.GetByLabel('UI/Inflight/MoonMining/DisplayPercentage', percent=int(100 * (1.0 - emRes)))
        kiPercentageLabel = localization.GetByLabel('UI/Inflight/MoonMining/DisplayPercentage', percent=int(100 * (1.0 - kiRes)))
        exPercentageLabel = localization.GetByLabel('UI/Inflight/MoonMining/DisplayPercentage', percent=int(100 * (1.0 - exRes)))
        thPercentageLabel = localization.GetByLabel('UI/Inflight/MoonMining/DisplayPercentage', percent=int(100 * (1.0 - thRes)))
        self.sr.emkinText.text = '%s<t>%s' % (emPercentageLabel, kiPercentageLabel)
        self.sr.expthermText.text = '%s<t>%s' % (exPercentageLabel, thPercentageLabel)
        powerSupply = 0
        cpuSupply = 0
        powerConsumption = 0
        cpuConsumption = 0
        for itemID, ball in bp.slimItems.iteritems():
            if ball.categoryID == const.categoryStructure and self.pwn.GetStructureState(ball)[0] in ('online', 'operating'):
                powerSupply += getattr(self.godma.GetType(ball.typeID), 'powerOutput', 0)
                cpuSupply += getattr(self.godma.GetType(ball.typeID), 'cpuOutput', 0)
                powerConsumption += getattr(self.godma.GetType(ball.typeID), 'power', 0)
                cpuConsumption += getattr(self.godma.GetType(ball.typeID), 'cpu', 0)

        if powerSupply == 0:
            self.sr.powergauge.sr.bar.width = 0
        else:
            self.sr.powergauge.sr.bar.width = int((self.sr.powergauge.width - 2) * powerConsumption / powerSupply)
        if cpuSupply == 0:
            self.sr.cpugauge.sr.bar.width = 0
        else:
            self.sr.cpugauge.sr.bar.width = int((self.sr.cpugauge.width - 2) * cpuConsumption / cpuSupply)
        self.sr.powertext.text = localization.GetByLabel('UI/Inflight/MoonMining/TowerPowerUsage', currentValue=powerConsumption, totalPower=powerSupply)
        self.sr.cputext.text = localization.GetByLabel('UI/Inflight/MoonMining/TowerCPUUsage', currentValue=cpuConsumption, totalCPU=cpuSupply)
        self.sr.powerSupply = powerSupply
        self.sr.cpuSupply = cpuSupply
        self.sr.powerConsumption = powerConsumption
        self.sr.cpuConsumption = cpuConsumption

    def UpdateDamage(self):
        if self.destroyed:
            return
        bp = sm.GetService('michelle').GetBallpark()
        damage = bp.GetDamageState(self.slimItem.itemID)
        if damage is None:
            return
        shield = min(damage[0], 1.0)
        armor = min(damage[1], 1.0)
        structure = min(damage[2], 1.0)
        barcolor = self.sr.shieldgauge.sr.bar.color
        if shield is None:
            barcolor.r, barcolor.g, barcolor.b = (1.0, 1.0, 0.1)
            self.sr.shieldgauge.sr.bar.width = int(self.sr.powergauge.width - 2)
            self.sr.shieldtext.text = '<color=0xffff0000>' + localization.GetByLabel('UI/Inflight/MoonMining/Reinforced') + '</color>'
        else:
            barcolor.r, barcolor.g, barcolor.b = (0.8, 0.8, 1.0)
            self.sr.shieldgauge.sr.bar.width = int(round((self.sr.powergauge.width - 2) * (shield or 0.0)))
            self.sr.shieldtext.text = localization.GetByLabel('UI/Inflight/MoonMining/DisplayPercentage', percent=int(shield * 100))
        self.sr.armorgauge.sr.bar.width = int(round((self.sr.powergauge.width - 2) * armor))
        self.sr.armortext.text = localization.GetByLabel('UI/Inflight/MoonMining/DisplayPercentage', percent=int(armor * 100))
        self.sr.structuregauge.sr.bar.width = int(round((self.sr.powergauge.width - 2) * structure))
        self.sr.structuretext.text = localization.GetByLabel('UI/Inflight/MoonMining/DisplayPercentage', percent=structure * 100)

    def UpdateStructures(self, rec = None):
        if not self or self.destroyed:
            return
        self.UpdateHeader()
        if rec and rec.groupID in (const.groupMoonMining, const.groupSilo, const.groupMobileReactor) and self.pwn.GetStructureState(rec)[0] in ('anchoring', 'unanchored'):
            self.GetProductionStructures(force=1)
        if self.sr.maintabs and self.sr.maintabs.GetSelectedArgs()[0] == 'structures':
            if self.sr.structuretabs and self.sr.structuretabs.GetSelectedArgs()[1] == 'structures':
                self.ShowStructures()
            if self.sr.structuretabs and self.sr.structuretabs.GetSelectedArgs()[1] == 'control':
                self.ShowControl()
        if self.sr.maintabs and self.sr.maintabs.GetSelectedArgs()[0] == 'process':
            if self.sr.processtabs and self.sr.processtabs.GetSelectedArgs()[1] == 'production':
                self.ShowProduction()
            if self.sr.processtabs and self.sr.processtabs.GetSelectedArgs()[1] == 'fuel':
                self.ShowFuel()

    def GetStructureMenu(self, entry):
        data = entry.sr.node
        return sm.GetService('menu').CelestialMenu(data.rec.itemID, slimItem=data.rec)

    def GetTypeMenu(self, entry):
        data = entry.sr.node
        return [(localization.GetByLabel('UI/Commands/ShowInfo'), self.ShowInfo, (data.typeID,))]

    def TowerMenu(self):
        m = sm.GetService('menu').GetMenuFormItemIDTypeID(self.slimItem.itemID, self.slimItem.typeID)
        return m

    def ShowInfo(self, typeID):
        sm.GetService('info').ShowInfo(typeID)

    def OpenResources(self):
        sm.GetService('menu').OpenPOSFuelBay(self.slimItem.itemID, localization.GetByLabel('UI/Inflight/MoonMining/Processes/Fuel'))

    def Anchor(self):
        sel = self.sr.scroll.GetSelected()
        if len(sel) < 0:
            return
        itemID = None
        if len(sel) > 0:
            itemID = sel[0].rec.itemID
        elif len(self.sr.scroll.GetNodes()) == 0:
            itemID = self.slimItem.itemID
        if itemID and sm.GetService('pwn').CanAnchorStructure(itemID):
            sm.GetService('posAnchor').StartAnchorPosSelect(itemID)

    def Unanchor(self):
        sel = self.sr.scroll.GetSelected()
        structures = [ each.rec for each in sel ]
        for rec in structures:
            if sm.GetService('pwn').CanUnanchorStructure(rec.itemID):
                sm.GetService('menu').AnchorStructure(rec.itemID, 0)

        if len(self.sr.scroll.GetNodes()) == 0:
            if sm.GetService('pwn').CanUnanchorStructure(self.slimItem.itemID):
                sm.GetService('menu').AnchorStructure(self.slimItem.itemID, 0)

    def Online(self):
        sel = self.sr.scroll.GetSelected()
        if len(sel) > 0:
            sm.GetService('menu').ToggleObjectOnline(sel[0].rec.itemID, 1)
        if len(self.sr.scroll.GetNodes()) == 0:
            sm.GetService('menu').ToggleObjectOnline(self.slimItem.itemID, 1)

    def Offline(self):
        sel = self.sr.scroll.GetSelected()
        structures = [ each.rec for each in sel ]
        dogmaLM = self.godma.GetDogmaLM()
        for rec in structures:
            sm.GetService('menu').ToggleObjectOnline(rec.itemID, 0)

        if len(self.sr.scroll.GetNodes()) == 0:
            sm.GetService('menu').ToggleObjectOnline(self.slimItem.itemID, 0)

    def IsItemHere(self, rec):
        return rec.locationID == self.slimItem.itemID

    def OnTowerDropData(self, dragObject, nodes):
        for node in nodes:
            self.TowerDropNode(node)

    def TowerDropNode(self, node):
        if node.__guid__ not in ('xtriui.InvItem', 'xtriui.FittingSlot', 'listentry.InvItem'):
            return
        try:
            if not getattr(node.rec, 'typeID', None):
                eve.Message('error')
                return
            quantity = getattr(node.rec, 'quantity', 1)
            return self.tower.Add(node.rec.itemID, node.rec.locationID, qty=quantity)
        except UserError as what:
            if what.args[0] == 'NotEnoughChargeSpace':
                if what.dict['capacity'] < 0:
                    raise UserError('DestinationOverloaded')
                sys.exc_clear()
            else:
                raise 

    def InitStandingsPanel(self):
        parent = self.sr.standingspanel
        cont = uicls.Container(name='standingspanelcont', align=uiconst.TOALL, parent=parent, pos=(const.defaultPadding + 2,
         const.defaultPadding + 2,
         const.defaultPadding + 2,
         const.defaultPadding + 2))
        uicls.Frame(parent=cont, idx=0)
        uix.GetContainerHeader(localization.GetByLabel('UI/Inflight/MoonMining/Defense/SentryGunSettings'), cont, 0)
        uicls.Container(name='push', align=uiconst.TOLEFT, width=6, parent=cont)
        uicls.Container(name='push', align=uiconst.TOLEFT, width=6, parent=cont)
        s3a = uicls.Container(parent=cont, align=uiconst.TOTOP)
        useAllianceStandingsLabel = localization.GetByLabel('UI/Inflight/MoonMining/Defense/UseAllianceStandings')
        self.sr.alliancestandingcheckbox = uicls.Checkbox(text=useAllianceStandingsLabel, parent=s3a, configName='', retval='chkusealliancecontroltower')
        s3a.height = self.sr.alliancestandingcheckbox.height
        if not session.allianceid:
            s3a.state = uiconst.UI_HIDDEN
        s1 = uicls.Container(parent=cont, align=uiconst.TOTOP, top=const.defaultPadding)
        attackIfStandingLowerThanLabel = localization.GetByLabel('UI/Inflight/MoonMining/Defense/AttackIfStandingLowerThan')
        self.sr.standingcheckbox1 = uicls.Checkbox(text=attackIfStandingLowerThanLabel, parent=s1, configName='', retval='chkstanding', align=uiconst.TOPLEFT, pos=(0, 0, 250, 0))
        self.sr.standingedit1 = uicls.SinglelineEdit(name='standing', parent=s1, setvalue=None, pos=(255, 0, 80, 0), floats=(-10, 10))
        s1.height = max(self.sr.standingcheckbox1.height, self.sr.standingedit1.height)
        s2 = uicls.Container(parent=cont, align=uiconst.TOTOP, top=const.defaultPadding)
        securityStatusBelowLabel = localization.GetByLabel('UI/Inflight/MoonMining/Defense/AttackIfSecurityStatusBelow')
        self.sr.standingcheckbox2 = uicls.Checkbox(text=securityStatusBelowLabel, parent=s2, configName='', retval='chkstatus', align=uiconst.TOPLEFT, pos=(0, 0, 250, 0))
        self.sr.standingedit2 = uicls.SinglelineEdit(name='status', parent=s2, setvalue=None, pos=(255, 0, 80, 0), floats=(-10, 10))
        s2.height = max(self.sr.standingcheckbox2.height, self.sr.standingedit2.height)
        checkboxes = [(localization.GetByLabel('UI/Inflight/MoonMining/Defense/AttackIfSecurityStatusIsDropping'), 4, 'chkourstatus'), (localization.GetByLabel('UI/Inflight/MoonMining/Defense/AttackIfAtWar'), 6, 'chkwar')]
        for label, key, name in checkboxes:
            s = uicls.Container(parent=cont, align=uiconst.TOTOP, top=const.defaultPadding)
            cb = uicls.Checkbox(text=label, parent=s, configName='', retval=name)
            setattr(self.sr, 'standingcheckbox%s' % key, cb)
            s.height = cb.height

        self.sr.standingsinited = 1
        applyLabel = localization.GetByLabel('UI/Common/Buttons/Apply')
        b = uicls.Button(parent=cont, label=applyLabel, align=uiconst.BOTTOMRIGHT, pos=(5, 5, 0, 0), func=self.SaveStandings)
        if sm.GetService('map').GetSecurityClass(eve.session.solarsystemid2) == const.securityClassHighSec:
            s1.state = uiconst.UI_HIDDEN
            s2.state = uiconst.UI_HIDDEN

    def SaveStandings(self, *args):
        standing = [None, self.sr.standingedit1.GetValue()][self.sr.standingcheckbox1.GetValue()]
        status = [None, self.sr.standingedit2.GetValue()][self.sr.standingcheckbox2.GetValue()]
        statusDrop = [False, True][self.sr.standingcheckbox4.GetValue()]
        war = [False, True][self.sr.standingcheckbox6.GetValue()]
        settings = [standing,
         status,
         statusDrop,
         war]
        useAllianceStandings = self.sr.alliancestandingcheckbox.GetValue()
        if settings != getattr(self, 'sentrySettings', None):
            self.posMgr.SetTowerSentrySettings(self.slimItem.itemID, standing, status, statusDrop, war, useAllianceStandings)
            self.sentrySettings = settings

    def InitForcefieldPanel(self):
        parent = self.sr.forcefieldpanel
        cont = uicls.Container(name='forcefieldpanelcont', align=uiconst.TOALL, parent=parent, padding=const.defaultPadding)
        uicls.Frame(parent=cont, idx=0)
        uix.GetContainerHeader(localization.GetByLabel('UI/Inflight/MoonMining/ForceField/ForceFieldHarmonicSettings'), cont, 0)
        uicls.Container(name='push', align=uiconst.TOLEFT, width=6, parent=cont)
        uicls.Container(name='push', align=uiconst.TORIGHT, width=6, parent=cont)
        s0 = uicls.Container(parent=cont, align=uiconst.TOTOP)
        forceFieldStatusLabel = localization.GetByLabel('UI/Inflight/MoonMining/ForceField/ForceFieldStatus')
        statusText = uicls.EveLabelSmall(text=forceFieldStatusLabel, parent=s0, align=uiconst.CENTERLEFT)
        noPasswordSetLabel = localization.GetByLabel('UI/Inflight/MoonMining/ForceField/NoPasswordSet')
        self.sr.forcefieldtext1 = uicls.EveLabelMedium(text=noPasswordSetLabel, parent=s0, left=80, top=3, width=350, height=32)
        s0.height = max(statusText.textheight, self.sr.forcefieldtext1.textheight)
        s1 = uicls.Container(parent=cont, align=uiconst.TOTOP, padTop=6)
        passwordLabel = localization.GetByLabel('UI/Inflight/MoonMining/ForceField/PasswordLabel')
        passwordText = uicls.EveLabelSmall(text=passwordLabel, parent=s1, align=uiconst.CENTERLEFT)
        self.sr.forcefieldedit1 = uicls.SinglelineEdit(name='password', parent=s1, setvalue=None, align=uiconst.TOTOP)
        self.sr.forcefieldedit1.SetPasswordChar(u'\u2022')
        s1.height = max(passwordText.textheight, self.sr.forcefieldedit1.height) + 4
        s2 = uicls.Container(parent=cont, align=uiconst.TOTOP)
        confirmPasswordLabel = localization.GetByLabel('UI/Inflight/MoonMining/ForceField/ConfirmPassword')
        confirmText = uicls.EveLabelSmall(text=confirmPasswordLabel, parent=s2, align=uiconst.CENTERLEFT)
        self.sr.forcefieldedit2 = uicls.SinglelineEdit(name='confirm', parent=s2, setvalue=None, align=uiconst.TOTOP)
        self.sr.forcefieldedit2.SetPasswordChar(u'\u2022')
        s2.height = max(confirmText.textheight, self.sr.forcefieldedit2.height) + 4
        self.sr.forcefieldedit1.padLeft = self.sr.forcefieldedit2.padLeft = max(70, statusText.width, passwordText.width, confirmText.width) + 10
        self.sr.forcefieldtext1.left = self.sr.forcefieldedit1.padLeft
        s3 = uicls.Container(parent=cont, align=uiconst.TOTOP)
        corporationMemberUsageLabel = localization.GetByLabel('UI/Inflight/MoonMining/ForceField/AllowCorporationMemberUsage')
        self.sr.forcefieldcheckbox1 = uicls.Checkbox(text=corporationMemberUsageLabel, parent=s3, configName='', retval='chkcorpentrance')
        s3.height = self.sr.forcefieldcheckbox1.height + 4
        s4 = uicls.Container(parent=cont, align=uiconst.TOTOP)
        allianceMemberUsageLabel = localization.GetByLabel('UI/Inflight/MoonMining/ForceField/AllowAllianceMemberUsage')
        self.sr.forcefieldcheckbox2 = uicls.Checkbox(text=allianceMemberUsageLabel, parent=s4, configName='', retval='chkallianceentrance')
        if session.allianceid is None:
            s4.height = 0
        else:
            s4.height = self.sr.forcefieldcheckbox2.height + 4
        uicls.Container(name='push', align=uiconst.TOTOP, height=6, parent=cont)
        uix.GetContainerHeader(localization.GetByLabel('UI/Inflight/MoonMining/Notifications'), cont, xmargin=-6)
        s5 = uicls.Container(parent=cont, align=uiconst.TOTOP, padTop=6)
        enableFuelNotificationLabel = localization.GetByLabel('UI/Inflight/MoonMining/SendFuelNotifications')
        self.fuelNotifyCheckbox = uicls.Checkbox(text=enableFuelNotificationLabel, parent=s5, configName='', retval='chkfuelnotifications')
        s5.height = self.fuelNotifyCheckbox.height + 4
        s6 = uicls.Container(parent=cont, align=uiconst.TOTOP)
        enableCalendarEntryLabel = localization.GetByLabel('UI/Inflight/MoonMining/ShowInCalendar')
        self.calendarCheckbox = uicls.Checkbox(text=enableCalendarEntryLabel, parent=s6, configName='', retval='chkfuelcalendarentry')
        s6.height = self.calendarCheckbox.height + 4
        uicls.Line(parent=cont, align=uiconst.TOTOP, padLeft=-5, padRight=-5)
        applyLabel = localization.GetByLabel('UI/Common/Buttons/Apply')
        buttonCont = uicls.Container(parent=cont, align=uiconst.TOBOTTOM, height=26, bottomPadding=6, padLeft=-5, padRight=-5)
        b = uicls.Button(parent=buttonCont, label=applyLabel, func=self.SaveForcefield, align=uiconst.CENTER)
        buttonCont.height = max(26, b.height + 8)
        totalHeight = sum([ each.height + each.padTop + each.padBottom for each in cont.children ]) + self.GetHeaderHeight() + self.sr.top.height + self.sr.maintabs.height
        self.SetMinSize([MINWNDWIDTH, totalHeight + const.defaultPadding * 2])
        self.sr.forcefieldinited = 1

    def SaveForcefield(self, *args):
        password = self.sr.forcefieldedit1.GetValue() or ''
        confirm = self.sr.forcefieldedit2.GetValue() or ''
        forceField = self.GetForcefield()
        allowCorp = True if self.sr.forcefieldcheckbox1.GetValue() else False
        allowAlliance = True if self.sr.forcefieldcheckbox2.GetValue() else False
        showInCalendar = True if self.calendarCheckbox.GetValue() else False
        sendFuelNotifications = True if self.fuelNotifyCheckbox.GetValue() else False
        if self.notifySettings is not None:
            if self.notifySettings.showInCalendar != showInCalendar or self.notifySettings.sendFuelNotifications != sendFuelNotifications:
                self.posMgr.SetTowerNotifications(self.slimItem.itemID, showInCalendar, sendFuelNotifications)
                self.notifySettings.showInCalendar = showInCalendar
                self.notifySettings.sendFuelNotifications = sendFuelNotifications
        else:
            self.posMgr.SetTowerNotifications(self.slimItem.itemID, showInCalendar, sendFuelNotifications)
            self.notifySettings = util.KeyVal(showInCalendar=showInCalendar, sendFuelNotifications=sendFuelNotifications)
        if password == confirm:
            if not len(password):
                if not forceField or forceField == self.slimItem:
                    raise UserError('NoPasswordEntered')
                else:
                    password = False
            self.posMgr.SetTowerPassword(self.slimItem.itemID, password, allowCorp, allowAlliance)
        else:
            self.sr.forcefieldtext1.text = localization.GetByLabel('UI/Inflight/MoonMining/ForceField/PasswordAndConfirmMismatch')

    def GetShell(self, itemID):
        tower = sm.GetService('invCache').GetInventoryFromId(itemID)
        return tower

    def GetMoon(self):
        self.res = {}
        if self.moon is None:
            try:
                self.moon = self.posMgr.GetMoonForTower(self.slimItem.itemID)
            except UserError as e:
                self.CloseByUser()
                raise 

        self.moonID = self.moon[0]
        if self.moon[1] is not None:
            for typeID, quantity in self.moon[1]:
                self.res[typeID] = quantity

    def GetForcefield(self):
        bp = sm.GetService('michelle').GetBallpark()
        forcefield = [ rec for itemID, rec in bp.slimItems.iteritems() if rec.groupID == const.groupForceField and rec.ownerID == self.slimItem.ownerID ]
        if len(forcefield):
            return forcefield[0]
        else:
            return self.slimItem

    def GetProductionStructures(self, force = 0, useStructures = None):
        if not force and self.sr.Get('structures'):
            return self.sr.structures
        structures = {}
        bp = sm.GetService('michelle').GetBallpark()
        info = useStructures
        if info is None:
            info = self.posMgr.GetMoonProcessInfoForTower(self.slimItem.itemID)
        self.sr.structureConnections = {}
        if info and bp:
            for itemID, active, reaction, connections, demands, supplies in info:
                if not bp.slimItems.has_key(itemID):
                    continue
                structure = util.KeyVal()
                rec = bp.slimItems[itemID]
                if reaction and rec.groupID == const.groupMobileReactor and not demands and not supplies:
                    demands = [ (row.typeID, row.quantity) for row in cfg.invtypereactions[reaction[1]] if row.input == 1 ]
                    supplies = [ (row.typeID, row.quantity) for row in cfg.invtypereactions[reaction[1]] if row.input == 0 ]
                demand = {}
                demands = demands or []
                for tID, quant in demands:
                    demand[tID] = quant

                supply = {}
                supplies = supplies or []
                for tID, quant in supplies:
                    supply[tID] = quant

                color = (0.0, 0.0, 0.0, 0.0)
                c1 = rec.typeID / 16 % 16
                c2 = rec.typeID % 16
                if rec.groupID == const.groupMoonMining:
                    color = (c1 / 17.0,
                     1.0,
                     c2 / 17.0,
                     0.3)
                elif rec.groupID == const.groupSilo:
                    color = (1.0,
                     c1 / 17.0,
                     c1 / 24.0,
                     0.3)
                elif rec.groupID == const.groupMobileReactor:
                    color = (c1 / 17.0,
                     c2 / 17.0,
                     1.0,
                     0.3)
                structure.rec = rec
                structure.demands = demand
                structure.supplies = supply
                structure.reaction = reaction
                structure.color = color
                structure.active = active
                structures[rec.itemID] = structure
                for sourceID, tID in connections:
                    self.sr.structureConnections[tID, sourceID] = itemID

        self.sr.structures = structures
        return structures

    def GetMaxDemands(self, itemID):
        if itemID in self.sr.structures:
            structure = self.sr.structures[itemID]
            if structure.rec.groupID == const.groupSilo:
                return {structure.demands.keys()[0]: -1}
            if structure.rec.groupID == const.groupMobileReactor and structure.reaction:
                demands = [ (row.typeID, row.quantity) for row in cfg.invtypereactions[structure.reaction[1]] if row.input == 1 ]
                d = {}
                for tID, quant in demands or []:
                    d[tID] = quant

                return d
        return {}

    def GetMaxSupplies(self, itemID):
        if self.sr.structures.has_key(itemID):
            structure = self.sr.structures[itemID]
            if structure.rec.groupID == const.groupSilo:
                return {structure.supplies.keys()[0]: -1}
            if structure.rec.groupID == const.groupMobileReactor and structure.reaction:
                demands = [ (row.typeID, row.quantity) for row in cfg.invtypereactions[structure.reaction[1]] if row.input == 0 ]
                d = {}
                for tID, quant in demands or []:
                    d[tID] = quant

                return d
            if structure.rec.groupID == const.groupMoonMining and len(structure.supplies):
                return {structure.supplies.keys()[0]: self.godma.GetType(structure.rec.typeID).harvesterQuality}
        return {}

    def GetStructureConnections(self):
        if not self.sr.Get('structureConnections'):
            self.sr.structureConnections = {}

    def EvalStructureConnections(self):
        self.GetStructureConnections()
        self.sr.resEval = {}
        resEval = self.sr.resEval
        l = self.sr.structures.copy()
        b = 1
        while b:
            b = 0
            for itemID in l.keys():
                unevals = [ x for x, v in self.sr.structures[itemID].demands.iteritems() if not (resEval.has_key(itemID) and resEval[itemID].has_key(x) or self.sr.structures[itemID].rec.groupID in (const.groupMoonMining, const.groupSilo)) ]
                if not len(unevals):
                    b = 1
                    cycle = 1
                    if resEval.has_key(itemID):
                        for typeID in resEval[itemID]:
                            if resEval[itemID][typeID][0] == 0:
                                cycle = -1
                            else:
                                cycle = max(cycle, [math.ceil(1.0 * self.GetMaxDemands(itemID)[typeID] / resEval[itemID][typeID][0]) * resEval[itemID][typeID][1], -1][self.sr.structures[itemID].demands[typeID] == -1])

                    for typeID in self.sr.structures[itemID].supplies:
                        dItemID = self.sr.structureConnections.get((typeID, itemID), None)
                        if dItemID:
                            if not resEval.has_key(dItemID):
                                resEval[dItemID] = {}
                            if not self.sr.structures[dItemID].demands.has_key(typeID):
                                continue
                            sQuant, dQuant = self.GetMaxSupplies(itemID)[typeID], self.GetMaxDemands(dItemID)[typeID]
                            if sQuant == -1:
                                using = dQuant
                            elif dQuant == -1:
                                using = sQuant
                            else:
                                using = min(sQuant, dQuant)
                            resEval[dItemID][typeID] = (using, cycle)

                    del l[itemID]

    def StructureCallback(self, typeID, fromItemID, toItemID, connect):
        self.connectionsChanged = 1
        if self.sr.structureConnections.has_key((typeID, fromItemID)):
            if not connect:
                del self.sr.structureConnections[typeID, fromItemID]
                self.ShowProduction()
                return
        if not self.sr.structures.has_key(fromItemID) or not self.sr.structures.has_key(toItemID):
            return
        if self.sr.structures[fromItemID].supplies.has_key(typeID) and self.sr.structures[toItemID].demands.has_key(typeID) and connect:
            self.sr.structureConnections[typeID, fromItemID] = toItemID
        self.ShowProduction()

    def ReactionChanged(self, reactorItemID, reaction):
        res = {}
        prod = {}
        if reaction:
            tres = [ (row.typeID, row.quantity) for row in cfg.invtypereactions[reaction[1]] if row.input == 1 ]
            tprod = [ (row.typeID, row.quantity) for row in cfg.invtypereactions[reaction[1]] if row.input == 0 ]
            tres = tres or []
            for tID, quant in tres:
                res[tID] = quant

            tprod = tprod or []
            for tID, quant in tprod:
                prod[tID] = quant

        self.sr.structures[reactorItemID].demands = res
        self.sr.structures[reactorItemID].supplies = prod
        self.sr.structures[reactorItemID].reaction = reaction
        if self.sr.maintabs and self.sr.maintabs.GetSelectedArgs()[0] == 'process':
            if self.sr.processtabs and self.sr.processtabs.GetSelectedArgs()[1] == 'production':
                self.ShowProduction()

    def ProdApply(self, *args):
        if self.sr.Get('structures', None) is not None and self.sr.Get('structureConnections', None) is not None:
            if not self.posMgr.LinkResourceForTower(self.slimItem.itemID, [ (k[1], v, k[0]) for k, v in self.sr.structureConnections.iteritems() ]):
                self.ShowProduction(force=1)
            self.connectionsChanged = 0

    def SetStructureType(self, itemID, groupID, *args):
        if groupID == const.groupSilo:
            rec = sm.GetService('michelle').GetBallpark().slimItems[itemID]
            temp = self.godma.GetTypeAttribute(rec.typeID, const.attributeCargoGroup)
            if temp:
                tmp = {temp: []}
                cargoGroup2 = self.godma.GetTypeAttribute(rec.typeID, const.attributeCargoGroup2)
                if cargoGroup2:
                    tmp[cargoGroup2] = []
            else:
                tmp = {const.groupMoonMaterials: [],
                 const.groupComposite: [],
                 const.groupIntermediateMaterials: [],
                 const.groupGasIsotopes: [],
                 const.groupMineral: []}
            for t in cfg.invtypes:
                if t.groupID in tmp:
                    tmp[t.groupID].append(t.typeID)

            import form
            wnd = form.SelectSiloType.Open(list=tmp)
            if wnd.ShowModal() == uiconst.ID_OK:
                chosen = wnd.result
            else:
                chosen = None
        elif groupID == const.groupMoonMining:
            rec = sm.GetService('michelle').GetBallpark().slimItems[itemID]
            quality = self.godma.GetType(rec.typeID).harvesterQuality
            used = [ structure.supplies.keys()[0] for structure in self.sr.structures.values() if len(structure.supplies) and structure.rec.groupID == const.groupMoonMining ]
            tmplist = [(localization.GetByLabel('UI/Inflight/MoonMining/Processes/HarvestNone'), 0, 0)]
            for t, q in self.res.iteritems():
                if t not in used:
                    harvestType = localization.GetByLabel('UI/Inflight/MoonMining/Processes/HarvestType', mineralID=t, amount=min(quality, q))
                    tmplist.append((harvestType, t, t))

            selectMoonMaterialLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/SelectMoonMaterial')
            chosen = uix.ListWnd(tmplist, None, selectMoonMaterialLabel, None, 1, minChoices=1, isModal=1)
            if chosen is not None:
                chosen = chosen[1]
        if chosen is not None:
            if chosen == 0:
                chosen = None
            self.posMgr.ChangeStructureProvisionType(self.slimItem.itemID, itemID, chosen)
            if len(self.sr.structures[itemID].supplies) and self.sr.structureConnections.has_key((self.sr.structures[itemID].supplies.keys()[0], itemID)):
                del self.sr.structureConnections[self.sr.structures[itemID].supplies.keys()[0], itemID]
            for k, v in self.sr.structureConnections.items():
                if v == itemID:
                    del self.sr.structureConnections[k]

            if groupID == const.groupSilo:
                self.sr.structures[itemID].demands = {chosen: -1}
                self.sr.structures[itemID].supplies = {chosen: -1}
            elif groupID == const.groupMoonMining:
                self.sr.structures[itemID].supplies = {chosen: -1}
            self.ShowProduction()

    def ProdReload(self):
        self.ShowProduction(force=1)

    def ProdClearLinks(self):
        if len(self.sr.structureConnections) == 0 or eve.Message('ProdClearLinks', {}, uiconst.YESNO) == uiconst.ID_YES:
            self.sr.structureConnections = {}
            self.ProdApply()
            self.ShowProduction(force=1)

    def RunProcessCycle(self):
        self.posMgr.RunMoonProcessCycleforTower(self.slimItem.itemID)
        if uicore.uilib.Key(uiconst.VK_SHIFT):
            resp = self.posMgr.GetMoonProcessInfoForTower(self.slimItem.itemID)
            txt = ''
            for entry in resp:
                txt += '%s, %s, %s, %s, %s, %s<br>' % entry

            eve.Message('RunProcessCycle', {'info': txt})

    def OnMoonProcessChange(self, towerID, structures):
        if towerID == self.slimItem.itemID:
            self.GetProductionStructures(force=1, useStructures=structures)
            if self.sr.Get('showing', None) == 'production':
                self.ShowProduction()

    def OnSlimItemChange(self, oldItem, newItem):
        if not self or self.destroyed:
            return
        if newItem.categoryID != const.categoryStructure:
            return
        if newItem.posState == oldItem.posState and newItem.posTimestamp == oldItem.posTimestamp and newItem.controllerID == oldItem.controllerID and newItem.incapacitated == oldItem.incapacitated:
            return
        if newItem.itemID == self.slimItem.itemID:
            self.slimItem = newItem
            self.GetMoon()
        if self.sr.Get('structures') and newItem.itemID in self.sr.structures:
            self.sr.structures[newItem.itemID].rec = newItem
        self.UpdateStructures(newItem)
        state = self.pwn.GetStructureState(newItem)
        if state[0] in ('anchoring', 'onlining', 'unanchoring', 'reinforced'):
            uthread.pool('moonmining::StateChangeFinished', self.StateChangeFinished, newItem, state)

    def StateChangeFinished(self, rec, state):
        blue.pyos.synchro.SleepWallclock(state[2])
        if self and not self.destroyed:
            self.UpdateStructures(rec)

    def OnInvChange(self, item = None, change = None):
        if not self or self.destroyed:
            return
        if self.sr.maintabs and self.sr.maintabs.GetSelectedArgs()[0] == 'process':
            if self.sr.processtabs and self.sr.processtabs.GetSelectedArgs()[1] == 'fuel':
                self.ShowFuel()

    def DoBallsAdded(self, *args, **kw):
        import stackless
        import blue
        t = stackless.getcurrent()
        timer = t.PushTimer(blue.pyos.taskletTimer.GetCurrent() + '::moonmining')
        try:
            return self.DoBallsAdded_(*args, **kw)
        finally:
            t.PopTimer(timer)

    def DoBallsAdded_(self, lst, ignoreMoons = 1, ignoreAsteroids = 1):
        if not self or self.destroyed:
            return
        for ball, slimItem in lst:
            if slimItem.categoryID == const.categoryStructure:
                uthread.pool('moonmining::UpdateStructures', self.UpdateStructures)
                break
            if slimItem.groupID == const.groupForceField:
                if self.sr.maintabs.GetSelectedArgs()[0] == 'force':
                    uthread.pool('moonmining::UpdateStructures', self.ShowForce)
                    break

    def DoBallRemove(self, ball, slimItem, terminal):
        if not self or self.destroyed:
            return
        if slimItem is None:
            log.LogWarn('DoBallRemove::moonmining slimItem is None')
            return
        if ball:
            log.LogInfo('DoBallRemove::moonmining', ball.id)
        if slimItem.itemID == self.slimItem.itemID:
            self.CloseByUser()
            return
        if slimItem.categoryID == const.categoryStructure:
            uthread.new(self.UpdateStructures)

    def DoBallClear(self, solitem):
        if not self or self.destroyed:
            return
        self.CloseByUser()

    def OnBallparkCall(self, *args):
        forcefield = self.GetForcefield()
        if args[1][0] == forcefield.itemID:
            if self.sr.maintabs.GetSelectedArgs()[0] == 'force':
                self.ShowForce()


class SelectSiloType(uicls.Window):
    __guid__ = 'form.SelectSiloType'

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        list = attributes.list
        self.SetCaption(localization.GetByLabel('UI/Inflight/MoonMining/Processes/SelectSiloType'))
        self.SetMinSize([256, 256])
        self.DefineButtons(uiconst.OKCANCEL)
        self.SetWndIcon()
        self.SetTopparentHeight(0)
        self.MakeUnMinimizable()
        self.scroll = uicls.Scroll(parent=self.sr.main, padding=(const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding,
         const.defaultPadding))
        scrolllist = []
        for group in list:
            label = cfg.invgroups.Get(group).name
            data = {'GetSubContent': self.GetGroupSubContent,
             'label': label,
             'id': ('TypeSel', group),
             'groupItems': list[group],
             'iconMargin': 18,
             'showlen': 1,
             'sublevel': 1,
             'state': 'locked'}
            scrolllist.append(listentry.Get('Group', data))

        scrolllist = localizationUtil.Sort(scrolllist, key=lambda x: x.label)
        self.scroll.state = uiconst.UI_NORMAL
        self.scroll.Load(contentList=scrolllist)

    def GetGroupSubContent(self, nodedata, newitems = 0):
        scrolllist = []
        for typeID in nodedata.groupItems:
            label = cfg.invtypes.Get(typeID).name
            data = util.KeyVal()
            data.confirmOnDblClick = 1
            data.label = label
            data.listvalue = typeID
            data.id = ('TypeSel', typeID)
            data.OnDblClick = self.DblClickEntry
            scrolllist.append(listentry.Get('Generic', data=data))

        return localizationUtil.Sort(scrolllist, key=lambda x: x.label)

    def Cancel(self, *etc):
        self.SetModalResult(uiconst.ID_CANCEL)

    def ClickOK(self, *args):
        self.Confirm()

    def Confirm(self, *etc):
        self.result = [ entry.listvalue for entry in self.scroll.GetSelected() ]
        if not self.result:
            info = localization.GetByLabel('UI/Inflight/MoonMining/Processes/MustSelectOne')
            raise UserError('CustomInfo', {'info': info})
        self.result = self.result[0]
        self.SetModalResult(uiconst.ID_OK)

    def DblClickEntry(self, entry, *args):
        if entry.confirmOnDblClick:
            self.scroll.SelectNode(entry.sr.node)
            self.Confirm()


class BaseStructure(uicls.SE_BaseClassCore):
    __guid__ = 'listentry.BaseStructure'
    __params__ = []

    def init(self):
        self.sr.resources = []
        self.sr.products = []

    def Startup(self, *args):
        sub = uicls.Container(name='sub', parent=self)
        uicls.Line(parent=sub, align=uiconst.TOBOTTOM, color=(1.0, 1.0, 1.0, 0.5))
        self.sr.resourcescont = uicls.Container(name='resources', align=uiconst.TOLEFT, width=32, parent=sub)
        uicls.Line(parent=sub, align=uiconst.TOLEFT, color=(1.0, 1.0, 1.0, 0.5))
        self.sr.productscont = uicls.Container(name='products', align=uiconst.TORIGHT, width=32, parent=sub)
        uicls.Line(parent=sub, align=uiconst.TORIGHT, color=(1.0, 1.0, 1.0, 0.5))
        self.sr.textcont = uicls.Container(name='textcol2', align=uiconst.TOALL, parent=sub, pos=(0, 0, 0, 0))
        self.sr.textcontsub = uicls.Container(name='textcol2', align=uiconst.TOALL, parent=sub, pos=(0, 0, 0, 0))
        self.sr.colorfill = uicls.Fill(parent=self.sr.textcontsub, color=(0.0, 1.0, 0.0, 0.0))
        self.sr.textcol1 = uicls.Container(name='textcol1', align=uiconst.TOLEFT, width=150, parent=self.sr.textcont)
        self.sr.textcol3 = uicls.Container(name='textcol3', align=uiconst.TORIGHT, width=75, parent=self.sr.textcont)
        self.sr.textcol2 = uicls.Container(name='textcol2', align=uiconst.TOALL, parent=self.sr.textcont, clipChildren=1, pos=(0, 0, 0, 0))
        self.sr.label = uicls.EveLabelMedium(text='', parent=self.sr.textcol1, left=4, top=4, state=uiconst.UI_DISABLED)
        self.sr.label2 = uicls.EveLabelMedium(text='', parent=self.sr.textcol1, left=4, top=4, state=uiconst.UI_DISABLED)
        self.sr.cycles = uicls.EveLabelSmall(text='1 cycle', parent=self.sr.textcol1, left=5, top=18, width=128, state=uiconst.UI_DISABLED)
        self.sr.actionparent = uicls.Container(name='actionparent', align=uiconst.TORIGHT, left=2, width=102, parent=self.sr.textcol3)
        self.sr.onlinebutton = uicls.Container(name='onlinebutton', parent=self.sr.actionparent, top=2, left=14, width=85, height=13, align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        self.sr.onlinebuttonText = uicls.EveLabelSmall(text='', parent=self.sr.onlinebutton, align=uiconst.TOALL, state=uiconst.UI_NORMAL)
        self.sr.onlinebuttonText.OnClick = self.Online
        uicls.Frame(parent=self.sr.onlinebutton)
        self.sr.changebutton = uicls.Container(name='changebutton', parent=self.sr.actionparent, left=14, top=17, width=85, height=13, align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL)
        self.sr.changebuttonText = uicls.EveLabelSmall(text='<center>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/ChangeType'), parent=self.sr.changebutton, align=uiconst.TOALL, state=uiconst.UI_NORMAL)
        uicls.Frame(parent=self.sr.changebutton)

    def Load(self, node):
        self.sr.node = node
        self.sr.colorfill.color.SetRGB(*self.sr.node.color)
        cycle = -2
        for res in self.sr.node.resources.values():
            if res[1] == 0:
                cycle = 0
            else:
                cycle = [max(0, cycle, [int(math.ceil(float(res[0]) / res[1]) * res[2]), -1][res[2] == -1]), 0][cycle == 0]

        if cycle == -2:
            cycle = 1
        color = [(1.0, 1.0, 1.0, 1.0), (1.0, 0.0, 0.0, 1.0)][self.sr.node.Get('connected', 0)]
        self.sr.cycles.color.SetRGB(color[0], color[1], color[2])
        self.sr.cycles.text = entities.POS_STRUCTURE_STATE[self.sr.node.state]
        if self.sr.node.state.startswith('reinforced'):
            self.sr.onlinebutton.state = uiconst.UI_HIDDEN
        else:
            if self.sr.node.state.startswith('onl'):
                self.sr.onlinebuttonText.text = '<center>' + localization.GetByLabel('UI/Inflight/MoonMining/PutOffline')
            else:
                self.sr.onlinebuttonText.text = '<center>' + localization.GetByLabel('UI/Inflight/MoonMining/PutOnline')
            self.sr.onlinebutton.state = uiconst.UI_NORMAL
        self.cycles = cycle
        self.LoadResourceIcons()
        self.LoadProductIcons()

    def LoadResourceIcons(self):
        resources = self.sr.node.resources.items()
        for i in xrange(5):
            if i < len(resources):
                if len(self.sr.resources) <= i:
                    icon = xtriui.TypeIcon(parent=self.sr.resourcescont, align=uiconst.TOTOP, height=32)
                    icon.Startup()
                    self.sr.resources.append(icon)
                self.sr.resources[i].SetType(resources[i], 0)
                self.sr.resources[i].SetSide('resource')
                self.sr.resources[i].SetItemID(self.sr.node.slimitem.itemID)
                self.sr.resources[i].SetCallback(self.sr.node.structurecallback)
                self.sr.resources[i].SetScrollObject(self.sr.node.scrollObject)
                if i != 0:
                    self.sr.resources[i].Line(1)
                else:
                    self.sr.resources[i].Line(0)
            elif len(self.sr.resources) > i:
                self.sr.resources[i].state = uiconst.UI_HIDDEN

        if len(resources) and len(resources) < len(self.sr.node.products):
            if self.sr.Get('resline', None) is None:
                self.sr.resline = uicls.Line(parent=self.sr.resourcescont, align=uiconst.TOTOP)
            else:
                self.sr.resline.state = uiconst.UI_DISABLED
        elif self.sr.Get('resline', None) is not None:
            self.sr.resline.state = uiconst.UI_HIDDEN

    def LoadProductIcons(self):
        products = self.sr.node.products.items()
        for i in xrange(5):
            if i < len(products):
                if len(self.sr.products) <= i:
                    icon = xtriui.TypeIcon(parent=self.sr.productscont, align=uiconst.TOTOP, height=32)
                    icon.Startup()
                    self.sr.products.append(icon)
                self.sr.products[i].SetColor(self.sr.node.color)
                self.sr.products[i].SetType(products[i], 1)
                self.sr.products[i].SetSide('product')
                self.sr.products[i].SetItemID(self.sr.node.slimitem.itemID)
                self.sr.products[i].SetCallback(self.sr.node.structurecallback)
                self.sr.products[i].SetScrollObject(self.sr.node.scrollObject)
                if i != 0:
                    self.sr.products[i].Line(1)
                else:
                    self.sr.products[i].Line(0)
            elif len(self.sr.products) > i:
                self.sr.products[i].state = uiconst.UI_HIDDEN

        if len(products) and len(products) < len(self.sr.node.resources):
            if self.sr.Get('prodline', None) is None:
                self.sr.prodline = uicls.Line(parent=self.sr.productscont, align=uiconst.TOTOP)
            else:
                self.sr.prodline.state = uiconst.UI_DISABLED
        elif self.sr.Get('prodline', None) is not None:
            self.sr.prodline.state = uiconst.UI_HIDDEN

    def GetMenu(self):
        m = sm.GetService('menu').GetMenuFormItemIDTypeID(self.sr.node.slimitem.itemID, self.sr.node.slimitem.typeID)
        return m

    def OnMouseEnter(self, *args):
        if self is None or self.destroyed or self.parent is None or self.parent.destroyed:
            return

    def OnMouseExit(self, *args):
        if self is None or self.destroyed or self.parent is None or self.parent.destroyed:
            return

    def Online(self, *args):
        toggleTo = [1, 0][self.sr.node.state.startswith('onl')]
        sm.GetService('menu').ToggleObjectOnline(self.sr.node.slimitem.itemID, toggleTo)

    def GetHeight(self, *args):
        node, width = args
        icons = max(len(node.Get('resources', [None])), len(node.Get('products', [None])))
        node.height = max(33, icons * 32 + 1)
        return node.height


class Harvester(BaseStructure):
    __guid__ = 'listentry.Harvester'

    def Startup(self, *args):
        BaseStructure.Startup(self, args)
        self.sr.typetext = uicls.EveLabelSmall(text='', parent=self.sr.textcol2, left=4, top=19, state=uiconst.UI_DISABLED, idx=0)

    def Load(self, node):
        BaseStructure.Load(self, node)
        self.sr.label2.text = self.sr.node.Get('label2', None) or localization.GetByLabel('UI/Inflight/MoonMining/Processes/Harvester')
        currentStatusLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/CurrentStatus', status=entities.POS_STRUCTURE_STATE[self.sr.node.state])
        self.sr.hint = self.sr.label2.text + '<br>%s' % currentStatusLabel
        mat = None
        if len(self.sr.node.products):
            k, v = self.sr.node.products.items()[0]
            mat = (k, v[0], v[1])
            if k is not None:
                self.sr.typetext.text = cfg.invtypes.Get(k).name
            else:
                self.sr.typetext.text = localization.GetByLabel('UI/Inflight/MoonMining/Processes/NoMaterialSet')
        if self.sr.node.connected:
            linktext = '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/HarvesterCorrectlyLinked')
        else:
            linktext = '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/HarvesterNotLinked')
        if not self.sr.node.state.startswith('online'):
            if not mat:
                self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/HarvesterNoMaterial')
            else:
                harvesterOfflineLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/HarvesterOffline', cycleTime=self.sr.node.cycle / 60000)
                if len(self.sr.node.products) and mat[0]:
                    self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/HarvesterCycleInformation', amount=mat[1] * sm.GetService('godma').GetType(mat[0]).moonMiningAmount, mineralID=mat[0], cycleTime=self.sr.node.cycle / 60000, harvesterOffline=harvesterOfflineLabel)
                else:
                    self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/HarvesterNotConfigured', harvesterOffline=harvesterOfflineLabel)
                self.sr.hint += linktext
        elif self.sr.node.state.startswith('online - start'):
            if mat:
                self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/HarvesterStarted', cycleTime=self.sr.node.cycle / 60000, amount=mat[2] * sm.GetService('godma').GetType(mat[0]).moonMiningAmount, mineralID=mat[0])
            else:
                self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/HarvesterMustChangeType')
            self.sr.hint += linktext
        elif self.sr.node.state.startswith('online - active'):
            harvesterActiveLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/HarvesterActive', miningAmount=mat[2] * sm.GetService('godma').GetType(mat[0]).moonMiningAmount, mineralID=mat[0], cycleTime=self.sr.node.cycle / 60000)
            self.sr.hint += '<br><br>' + harvesterActiveLabel
            self.sr.hint += linktext
        self.sr.changebuttonText.OnClick = (self.sr.node.settype, self.sr.node.slimitem.itemID, self.sr.node.slimitem.groupID)
        self.sr.changebutton.state = [uiconst.UI_HIDDEN, uiconst.UI_NORMAL][self.sr.node.state == 'anchored']
        self.sr.onlinebutton.state = [uiconst.UI_NORMAL, uiconst.UI_HIDDEN][self.sr.typetext.text.startswith('<color')]

    def Online(self, *args):
        if not len(self.sr.node.products) and not self.sr.node.state.startswith('onl'):
            eve.Message('HarvestOnline')
        else:
            listentry.BaseStructure.Online(self, *args)

    def GetMenu(self):
        changeHarvestedMaterialLabel = uiutil.MenuLabel('UI/Inflight/MoonMining/Processes/ChangeHarvestedMaterial')
        m = BaseStructure.GetMenu(self)
        m += [(changeHarvestedMaterialLabel, self.sr.node.settype, (self.sr.node.slimitem.itemID, self.sr.node.slimitem.groupID))]
        return m


class Silo(BaseStructure):
    __guid__ = 'listentry.Silo'

    def Startup(self, *args):
        BaseStructure.Startup(self, args)
        g = uicls.Container(name='gauge', align=uiconst.TOPLEFT, width=48, height=7, left=4, top=7, parent=self.sr.textcol2, idx=0)
        uicls.Container(name='push', parent=g, align=uiconst.TOBOTTOM, height=2)
        g.name = ''
        uicls.Line(parent=g, align=uiconst.TOTOP, color=(1.0, 1.0, 1.0, 0.5))
        uicls.Line(parent=g, align=uiconst.TOBOTTOM, color=(1.0, 1.0, 1.0, 0.5))
        uicls.Line(parent=g, align=uiconst.TOLEFT, color=(1.0, 1.0, 1.0, 0.5))
        uicls.Line(parent=g, align=uiconst.TORIGHT, color=(1.0, 1.0, 1.0, 0.5))
        g.sr.bar = uicls.Fill(parent=g, align=uiconst.TOLEFT, color=(1.0, 1.0, 1.0, 0.25))
        uicls.Fill(parent=g, color=(1.0, 1.0, 1.0, 0.0))
        self.sr.gauge = g
        self.sr.gaugetext = uicls.EveLabelSmall(text='', parent=self.sr.textcol2, left=g.left + g.width + 5, top=5, width=300, state=uiconst.UI_DISABLED, idx=0)
        self.sr.typetext = uicls.EveLabelSmall(text='', parent=self.sr.textcol2, left=4, top=19, state=uiconst.UI_DISABLED, idx=0)

    def Load(self, node):
        BaseStructure.Load(self, node)
        self.sr.label2.text = self.sr.node.Get('label2', None) or localization.GetByLabel('UI/Inflight/MoonMining/Processes/Silo')
        currentStatusLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/CurrentStatus', status=entities.POS_STRUCTURE_STATE[self.sr.node.state])
        self.sr.hint = self.sr.label2.text + '<br>%s' % currentStatusLabel
        used2 = used1 = 0
        if len(self.sr.node.resources):
            k, v = self.sr.node.resources.items()[0]
            amount = sm.GetService('godma').GetType(k).moonMiningAmount
            if self.sr.node.Get('reaction', None):
                used1 = self.sr.node.reaction[1]
                used2 = self.sr.node.reaction[0]
            self.sr.gaugetext.text = localization.GetByLabel('UI/Inflight/MoonMining/Processes/CapacityGauge', currentCapacity=max(round(used2, 1), 0), maxCapacity=max(round(used1, 1), 0))
            self.sr.typetext.text = cfg.invtypes.Get(k).name
            self.sr.gauge.sr.bar.width = int((self.sr.gauge.width - 2) * max(used2, 0) / max(used1, 1))
            if not self.sr.node.state.startswith('online'):
                self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/SiloOffline', capacity=max(used1, 0), mineralID=k)
                self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/SiloOfflineAccess')
            else:
                self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/SiloOnline', capacity=max(used1, 0), mineralID=k)
                self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/SiloOnlineAccess')
        else:
            self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/SiloNoStorageSet')
            self.sr.gaugetext.text = ''
            self.sr.typetext.text = ''
        self.sr.changebuttonText.OnClick = (self.sr.node.settype, self.sr.node.slimitem.itemID, self.sr.node.slimitem.groupID)
        self.sr.changebutton.state = [uiconst.UI_HIDDEN, uiconst.UI_NORMAL][self.sr.node.state == 'anchored']

    def GetMenu(self):
        changeSiloTypeLabel = uiutil.MenuLabel('UI/Inflight/MoonMining/Processes/ChangeSiloType')
        m = BaseStructure.GetMenu(self)
        m += [(changeSiloTypeLabel, self.sr.node.settype, (self.sr.node.slimitem.itemID, self.sr.node.slimitem.groupID))]
        return m


class Reactor(BaseStructure):
    __guid__ = 'listentry.Reactor'

    def Startup(self, *args):
        BaseStructure.Startup(self, args)
        self.sr.reaction = xtriui.ReactionView(align=uiconst.TOPLEFT)
        self.sr.reaction.top = 20
        self.sr.reaction.left = 170
        self.sr.reaction.width = 110
        self.sr.reaction.height = 34
        self.sr.reaction.state = uiconst.UI_NORMAL
        self.children.insert(0, self.sr.reaction)
        self.sr.reaction.Startup(const.flagCargo)
        self.fetchingShell = 0

    def SetupReactionShell(self, itemID):
        if self.destroyed:
            return
        self.fetchingShell = 1
        self.sr.reaction.SetShell(sm.GetService('invCache').GetInventoryFromId(itemID))
        if self.destroyed:
            return
        if self.sr.node and self.sr.node.slimitem.itemID != itemID:
            self.SetupReactionShell(self.sr.node.slimitem.itemID)
        else:
            self.fetchingShell = 0

    def Load(self, node):
        BaseStructure.Load(self, node)
        self.sr.label2.text = self.sr.node.Get('label2', None) or localization.GetByLabel('UI/Inflight/MoonMining/Processes/Reactor')
        currentStatusLabel = localization.GetByLabel('UI/Inflight/MoonMining/Processes/CurrentStatus', status=entities.POS_STRUCTURE_STATE[self.sr.node.state])
        self.sr.hint = self.sr.label2.text + '<br>%s' % currentStatusLabel
        if not self.fetchingShell:
            uthread.new(self.SetupReactionShell, self.sr.node.slimitem.itemID)
        self.sr.reaction.SetLocation(self.sr.node.slimitem.itemID)
        self.sr.reaction.OnReactionChanged = self.sr.node.ReactionChanged
        if self.sr.node.Get('reaction', None) is not None:
            rec = util.KeyVal()
            rec.typeID = self.sr.node.reaction[1]
            rec.itemID = self.sr.node.reaction[0]
            self.sr.reaction.SetItem(rec)
        else:
            self.sr.reaction.SetItem(None)
        if len(self.sr.node.products):
            k, v = self.sr.node.products.items()[0]
            mat = (k, v[0], v[1])
        else:
            mat = None
        if self.sr.node.connected:
            linktext = '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/ReactorCorrectlyLinked')
        else:
            linktext = '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/ReactorNotLinked')
        if not self.sr.node.state.startswith('online'):
            self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/ReactorOfflineAccess')
            if not self.sr.node.reaction:
                self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/ReactorNoReactionInstalled')
            else:
                self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/ReactorOfflineWithReaction')
        elif self.sr.node.state.startswith('online - start'):
            self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/ReactorStarted')
            self.sr.hint += linktext
        elif self.sr.node.state.startswith('online - active'):
            if mat is not None:
                self.sr.hint += '<br><br>' + localization.GetByLabel('UI/Inflight/MoonMining/Processes/ReactorActive', reactionAmount=mat[2] * sm.GetService('godma').GetType(mat[0]).moonMiningAmount, reactionID=mat[0], cycleTime=self.sr.node.cycle / 60000)
            self.sr.hint += linktext
        else:
            self.sr.hint += linktext
        self.sr.changebutton.state = uiconst.UI_HIDDEN

    def GetHeight(self, *args):
        node, width = args
        icons = max(len(node.Get('resources', [None])), len(node.Get('products', [None])), 2)
        node.height = max(33, icons * 32 + 1)
        return node.height


class TypeIcon(uicls.Container):
    __guid__ = 'xtriui.TypeIcon'
    isDragObject = True

    def init(self):
        self.rec = None
        self.typeID = None
        self.itemID = None
        self.DisableDrag()
        self.side = 'product'
        self.scroll = None

    def Startup(self):
        self.width = 32
        self.height = 32
        self.sr.icon = uicls.Icon(parent=self, align=uiconst.TOALL, state=uiconst.UI_DISABLED, size=32, ignoreSize=True)
        self.sr.color = uicls.Fill(parent=self, color=(0.0, 0.0, 0.0, 0.0))
        self.sr.highlight = uicls.Fill(parent=self, state=uiconst.UI_HIDDEN)
        countcont = uicls.Container(parent=self, align=uiconst.TOPLEFT, left=16, top=24, width=16, height=8, idx=0)
        self.sr.quantity = uicls.EveLabelSmall(text='', parent=countcont, left=2, width=14, height=8)
        uicls.Line(parent=countcont, align=uiconst.TOLEFT, color=(1.0, 1.0, 1.0, 0.5))
        uicls.Line(parent=countcont, align=uiconst.TOTOP, color=(1.0, 1.0, 1.0, 0.5))
        uicls.Fill(parent=countcont, color=(0.0, 0.0, 0.0, 1.0))

    def SetColor(self, color):
        if color is None:
            color = (1.0, 1.0, 1.0, 0.25)
        self.sr.color.color.SetRGB(*color)
        self.color = color

    def SetSide(self, side):
        self.side = side

    def SetItemID(self, itemID):
        self.itemID = itemID

    def SetType(self, t, drag):
        typeID, v = t
        quantity, used, cycle, color, connectID = v
        self.typeID = typeID
        self.connectID = connectID
        self.drag = drag
        self.UpdateDisplay(used, quantity)
        self.SetColor(color)
        if self.typeID is not None:
            self.sr.icon.LoadIconByTypeID(typeID, ignoreSize=True)
            self.state = uiconst.UI_NORMAL
            self.sr.hint = cfg.invtypes.Get(self.typeID).name
        else:
            self.state = uiconst.UI_HIDDEN
            self.sr.hint = localization.GetByLabel('UI/Inflight/MoonMining/Processes/NotConnected')
        if drag:
            self.EnableDrag()
        else:
            self.DisableDrag()

    def SetCallback(self, callback):
        self.sr.callback = callback

    def SetScrollObject(self, scroll):
        self.scroll = scroll

    def UpdateDisplay(self, used, quantity, typeID = None):
        if typeID and typeID != self.typeID:
            self.SetType(typeID, self.drag)
        quantity = [quantity, -1][quantity > 9]
        used = [used, -1][used > 9]
        self.quantity = quantity
        self.used = used
        self.sr.quantity.text = [unicode(used), '-'][used == -1] + '/' + [unicode(quantity), '-'][quantity == -1]

    def Line(self, state):
        if state:
            if self.sr.Get('line', None) is None:
                self.sr.line = uicls.Line(parent=self, align=uiconst.TOTOP)
        elif self.sr.Get('line', None) is not None:
            self.sr.line.state = uiconst.UI_HIDDEN

    def ShowInfo(self, *args):
        sm.GetService('info').ShowInfo(self.typeID, None)

    def Unfit(self, *args):
        if self.sr.Get('callback', None) is not None:
            if self.side == 'product':
                self.sr.callback(self.typeID, self.itemID, self.connectID, 0)
            else:
                self.sr.callback(self.typeID, self.connectID, self.itemID, 0)

    def GetRemoteItem(self):
        if self.scroll is None:
            return
        entries = [ entry for entry in self.scroll.GetNodes() if entry.panel and entry.slimitem and entry.slimitem.itemID == self.connectID ]
        if not entries or not len(entries):
            return
        entry = entries[0]
        items = None
        if self.side == 'product':
            if entry.panel.sr.resources is not None:
                items = [ item for item in entry.panel.sr.resources if item.typeID == self.typeID ]
        elif entry.panel.sr.products is not None:
            items = [ item for item in entry.panel.sr.products if item.typeID == self.typeID and item.state != uiconst.UI_HIDDEN ]
        if not items or not len(items):
            return
        return items[0]

    GetRemoteItem = uiutil.ParanoidDecoMethod(GetRemoteItem, ('parent',))

    def GetMenu(self):
        m = []
        if self.typeID:
            m += [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo)]
            if self.connectID:
                m += [(uiutil.MenuLabel('UI/Inflight/MoonMining/Processes/RemoveConnection'), self.Unfit)]
        return m

    def OnMouseEnter(self, *args):
        self.sr.highlight.state = uiconst.UI_DISABLED
        item = self.GetRemoteItem()
        if item is not None:
            item.sr.highlight.state = uiconst.UI_DISABLED

    def OnMouseExit(self, *args):
        self.sr.highlight.state = uiconst.UI_HIDDEN
        item = self.GetRemoteItem()
        if item is not None:
            item.sr.highlight.state = uiconst.UI_HIDDEN

    def OnDragEnter(self, dragObj, drag, *args):
        if drag and getattr(drag[0], '__guid__', None) in ('xtriui.DragIcon',) and drag[0].data[0].__guid__ == 'xtriui.TypeIcon' and drag[0].data[0].typeID == self.typeID and drag[0].data[0].itemID != self.itemID and not self.IsDraggable():
            self.sr.highlight.state = uiconst.UI_DISABLED

    def OnDragExit(self, *args):
        self.sr.highlight.state = uiconst.UI_HIDDEN

    def OnDropData(self, dragObj, nodes):
        node = nodes[0]
        if node.__guid__ == 'xtriui.TypeIcon' and node.typeID == self.typeID and node.itemID != self.itemID and not self.IsDraggable():
            if self.sr.Get('callback', None) is not None:
                uthread.new(self.sr.callback, self.typeID, node.itemID, self.itemID, 1)

    def GetDragData(self, *args):
        fakeNode = util.KeyVal()
        fakeNode.__guid__ = 'xtriui.TypeIcon'
        fakeNode.typeID = self.typeID
        fakeNode.itemID = self.itemID
        fakeNode.color = self.color
        fakeNode.quantity = fakeNode.stacksize = self.quantity
        return [fakeNode]


class ReactionView(uicls.Container):
    __guid__ = 'xtriui.ReactionView'
    isDragObject = True

    def init(self):
        self.isInvItem = 1
        self.rec = None
        self.DisableDrag()
        self.height = self.width = 32
        self.locationID = None
        self.itemID = None
        self.typeID = None

    def IsItemHere(self, item):
        return item.locationID == self.locationID and cfg.invtypes.Get(item.typeID).Group().Category().id == const.categoryReaction

    def IsEmpty(self):
        return self.rec is None

    def Startup(self, flag):
        uicls.Frame(parent=self, align=uiconst.RELATIVE, left=0, top=0, width=36, height=36)
        self.sr.highlight = uicls.Fill(parent=self, state=uiconst.UI_HIDDEN, align=uiconst.RELATIVE, left=2, top=2, width=32, height=32)
        self.sr.icon = uicls.Icon(parent=self, align=uiconst.RELATIVE, left=2, top=2, size=32, state=uiconst.UI_DISABLED, typeID=self.typeID)
        self.sr.reactiontext = uicls.EveLabelSmall(text='', parent=self, left=40, width=70, state=uiconst.UI_DISABLED)
        self.flag = flag
        sm.GetService('inv').Register(self)
        self.invReady = 1

    def SetLocation(self, locationID):
        self.locationID = locationID

    def SetShell(self, shell):
        if not util.GetAttrs(self, 'sr'):
            return
        self.sr.shell = shell

    def SetItem(self, rec):
        if rec is not None and rec.typeID:
            self.typeID = rec.typeID
            self.itemID = rec.itemID
            self.sr.icon.LoadIconByTypeID(self.typeID, ignoreSize=True)
            self.sr.icon.SetSize(32, 32)
            self.sr.hint = self.sr.reactiontext.text = cfg.invtypes.Get(self.typeID).name
        else:
            self.typeID = None
            self.itemID = None
            self.sr.icon.LoadIcon('ui_5_64_10', ignoreSize=True)
            self.sr.icon.SetSize(32, 32)
            self.sr.reactiontext.text = localization.GetByLabel('UI/Inflight/MoonMining/Processes/ReactorNoReaction')
            self.sr.hint = localization.GetByLabel('UI/Inflight/MoonMining/Processes/ReactorNoReaction')
        if rec:
            self.EnableDrag()
        else:
            self.DisableDrag()

    def AddItem(self, rec):
        self.SetItem(rec)
        if getattr(self, 'OnReactionChanged', None) is not None:
            self.OnReactionChanged(self.locationID, (self.itemID, self.typeID))

    def UpdateItem(self, item, *etc):
        self.SetItem(item)

    def RemoveItem(self, item):
        if item.itemID == self.itemID:
            self.SetItem(None)
            if getattr(self, 'OnReactionChanged', None) is not None:
                self.OnReactionChanged(self.locationID, None)

    def GetMenu(self):
        m = []
        if self.itemID and self.typeID:
            if eve.session.role & (service.ROLE_GML | service.ROLE_WORLDMOD):
                m += [(str(self.itemID), self.CopyItemIDToClipboard, (self.itemID,)), None]
            m += [(uiutil.MenuLabel('UI/Commands/ShowInfo'), self.ShowInfo), (uiutil.MenuLabel('UI/Inflight/MoonMining/Processes/ReactorRemoveReaction'), self.Unfit)]
        return m

    def CopyItemIDToClipboard(self, itemID):
        blue.pyos.SetClipboardData(str(itemID))

    def ShowInfo(self, *args):
        sm.GetService('info').ShowInfo(self.typeID, self.itemID)

    def Unfit(self):
        sm.GetService('invCache').GetInventoryFromId(eve.session.shipid).Add(self.itemID, self.locationID, qty=None, flag=const.flagCargo)

    def OnDropData(self, dragObj, nodes):
        for node in nodes:
            self.DropNode(node)

    def DropNode(self, node):
        if node.__guid__ not in ('xtriui.InvItem', 'xtriui.FittingSlot', 'listentry.InvItem'):
            return
        try:
            if not getattr(node.rec, 'typeID', None) or node.rec.categoryID != const.categoryReaction:
                eve.Message('error')
                return
            if getattr(node.rec, 'quantity', 1) == 1:
                quantity = 1
            else:
                return
            return self.sr.shell.Add(node.rec.itemID, node.rec.locationID, qty=quantity)
        except UserError as what:
            if what.args[0] == 'NotEnoughChargeSpace':
                if what.dict['capacity'] < 0:
                    raise UserError('DestinationOverloaded')
                sys.exc_clear()
            else:
                raise 

    def GetCapacity(self):
        return 0

    def OnMouseEnter(self, *args):
        self.sr.highlight.state = uiconst.UI_DISABLED

    def OnMouseExit(self, *args):
        self.sr.highlight.state = uiconst.UI_HIDDEN

    def OnDragEnter(self, dragObj, drag, *args):
        if drag and drag[0].__guid__ in ('xtriui.InvItem', 'xtriui.FittingSlot', 'listentry.InvItem') and drag[0].rec.categoryID == const.categoryReaction and drag[0].rec.itemID != self.itemID:
            self.sr.highlight.state = uiconst.UI_DISABLED

    def OnDragExit(self, *args):
        self.sr.highlight.state = uiconst.UI_HIDDEN

    def GetDragData(self, *args):
        if self.itemID is None:
            return []
        rec = util.KeyVal()
        rec.itemID = self.itemID
        rec.typeID = self.typeID
        rec.ownerID = None
        typeOb = cfg.invtypes.Get(self.typeID)
        rec.groupID = typeOb.groupID
        rec.categoryID = typeOb.categoryID
        rec.quantity = rec.stacksize = 1
        rec.locationID = self.locationID
        fakeNode = util.KeyVal()
        fakeNode.__guid__ = 'xtriui.InvItem'
        fakeNode.item = rec
        fakeNode.rec = rec
        fakeNode.itemID = rec.itemID
        fakeNode.ownerID = None
        fakeNode.invtype = typeOb
        fakeNode.container = None
        fakeNode.label = uix.GetItemName(rec, fakeNode)
        return [fakeNode]


class Gauge(uicls.SE_BaseClassCore):
    __guid__ = 'listentry.Gauge'
    __params__ = ['label', 'text']

    def Startup(self, args):
        self.sr.label = uicls.EveLabelMedium(text='', parent=self, left=8, top=2, width=175, state=uiconst.UI_DISABLED, maxLines=1)
        self.sr.text = uicls.EveLabelSmall(text='', parent=self, left=180, top=5, width=20, state=uiconst.UI_DISABLED)
        self.sr.quantity = uicls.EveLabelSmall(text='', parent=self, left=220, top=5, width=30, state=uiconst.UI_DISABLED)
        self.sr.cycles = uicls.EveLabelSmall(text='', parent=self, left=330, top=5, width=100, state=uiconst.UI_DISABLED)
        self.sr.line = uicls.Line(parent=self, align=uiconst.TOBOTTOM)
        self.sr.line.state = uiconst.UI_HIDDEN
        g = uicls.Container(name='gauge', align=uiconst.TOPLEFT, width=64, height=9, left=260, top=6, parent=self)
        uicls.Container(name='push', parent=g, align=uiconst.TOBOTTOM, height=2)
        g.name = ''
        uicls.Line(parent=g, align=uiconst.TOTOP, color=(1.0, 1.0, 1.0, 0.5))
        uicls.Line(parent=g, align=uiconst.TOBOTTOM, color=(1.0, 1.0, 1.0, 0.5))
        uicls.Line(parent=g, align=uiconst.TOLEFT, color=(1.0, 1.0, 1.0, 0.5))
        uicls.Line(parent=g, align=uiconst.TORIGHT, color=(1.0, 1.0, 1.0, 0.5))
        g.sr.bar = uicls.Fill(parent=g, align=uiconst.TOLEFT)
        self.sr.gauge = g

    def Load(self, node):
        data = self.sr.node
        quantity = max(math.ceil(data.factor * data.text), 1.0)
        self.sr.node = node
        self.sr.label.text = self.name = data.label
        self.sr.text.text = '<right>%s' % data.text
        self.sr.quantity.text = '<right>%s' % data.quantity
        if data.factor == 0.0:
            self.sr.cycles.text = localization.GetByLabel('UI/Inflight/MoonMining/Unused')
        else:
            self.sr.cycles.text = util.FmtDate(long(int(data.quantity / quantity) * data.cycle * 10000L), 'ss')
        self.sr.gauge.sr.bar.width = int((self.sr.gauge.width - 2) * data.size * data.quantity / data.capacity)
        if node.Get('line', 0):
            self.sr.line.state = uiconst.UI_DISABLED
        else:
            self.sr.line.state = uiconst.UI_HIDDEN

    def OnDropData(self, dragObj, nodes):
        data = self.sr.node
        if data.OnDropData:
            data.OnDropData(dragObj, nodes)

    def GetHeight(self, *args):
        node, width = args
        node.height = uix.GetTextHeight(node.label, maxLines=1) + 6
        return node.height


class BaseTextStructure(listentry.Generic):
    __guid__ = 'listentry.BaseTextStructure'
    __notifyevents__ = ['OnStateChange']

    def Startup(self, *args):
        listentry.Generic.Startup(self, *args)
        sm.RegisterNotify(self)

    def _OnClose(self, *args):
        listentry.Generic._OnClose(self, *args)
        sm.UnregisterNotify(self)

    def OnStateChange(self, itemID, flag, true, *args):
        if util.GetAttrs(self, 'sr', 'node') is None:
            return
        if self.sr.node.rec.itemID != itemID:
            return
        if flag == state.mouseOver:
            self.Hilite(true)
        elif flag == state.selected:
            self.Select(true)

    def Hilite(self, state):
        if self.sr.Get('hilite'):
            self.sr.hilite.state = [uiconst.UI_HIDDEN, uiconst.UI_DISABLED][state]

    def Select(self, state):
        self.sr.selection.state = [uiconst.UI_HIDDEN, uiconst.UI_DISABLED][state]
        self.sr.node.selected = state

    def OnMouseEnter(self, *args):
        listentry.Generic.OnMouseEnter(self, *args)
        if self.sr.node:
            sm.GetService('state').SetState(self.sr.node.rec.itemID, state.mouseOver, 1)

    def OnMouseExit(self, *args):
        listentry.Generic.OnMouseExit(self, *args)
        if self.sr.node:
            sm.GetService('state').SetState(self.sr.node.rec.itemID, state.mouseOver, 0)

    def OnClick(self, *args):
        if self.sr.node:
            listentry.Generic.OnClick(self, *args)
        if sm.GetService('target').IsTarget(self.sr.node.rec.itemID):
            sm.GetService('state').SetState(self.sr.node.rec.itemID, state.activeTarget, 1)
        elif uicore.uilib.Key(uiconst.VK_CONTROL):
            sm.GetService('target').TryLockTarget(self.sr.node.rec.itemID)
        elif uicore.uilib.Key(uiconst.VK_MENU):
            sm.GetService('menu').TryLookAt(self.sr.node.rec.itemID)


class Structure(BaseTextStructure):
    __guid__ = 'listentry.Structure'
    __params__ = ['label']

    def Startup(self, *args):
        listentry.BaseTextStructure.Startup(self, *args)

    def Load(self, node):
        listentry.BaseTextStructure.Load(self, node)
        self.UpdateState()

    def _OnClose(self, *args):
        listentry.BaseTextStructure._OnClose(self, *args)
        sm.UnregisterNotify(self)

    def Unload(self):
        self.loaded = 0

    def UpdateState(self):
        state = sm.GetService('pwn').GetStructureState(self.sr.node.rec)
        progressCont = uiutil.FindChild(self, 'progresscontainer')
        if progressCont:
            progressCont.Close()
        if state[0] in ('anchoring', 'onlining', 'unanchoring', 'reinforced', 'operating'):
            powerUsageLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/DisplayPowerUsage', powerUsage=self.sr.node.power)
            cpuUsageLabel = localization.GetByLabel('UI/Inflight/MoonMining/Structures/DisplayCPUUsage', cpuUsage=self.sr.node.cpu)
            displayState = structProgressMap.get(state[0], None)
            if displayState:
                stateLabel = entities.POS_STRUCTURE_STATE[displayState]
            else:
                stateLabel = localization.GetByLabel('UI/Generic/Done')
            label = '%s<t>%s<t><right>%s<t><right>%s' % (uix.GetSlimItemName(self.sr.node.rec),
             stateLabel,
             powerUsageLabel,
             cpuUsageLabel)
            uthread.new(self.sr.node.StructureProgress, self, label, state[1], state[2], self.sr.label)
        self.sr.label.text = [uix.GetSlimItemName(self.sr.node.rec),
         '<t>',
         entities.POS_STRUCTURE_STATE[state[0]],
         '<t><right>',
         localization.GetByLabel('UI/Inflight/MoonMining/Structures/DisplayPowerUsage', powerUsage=self.sr.node.power),
         '<t><right>',
         localization.GetByLabel('UI/Inflight/MoonMining/Structures/DisplayCPUUsage', cpuUsage=self.sr.node.cpu)]


class StructureControl(BaseTextStructure):
    __guid__ = 'listentry.StructureControl'
    __params__ = ['label']

    def Startup(self, *args):
        listentry.BaseTextStructure.Startup(self, *args)
        self.sr.controllerID = None
        self.sr.targetID = None
        self.sr.shooting = 0

    def Load(self, node):
        listentry.BaseTextStructure.Load(self, node)
        self.UpdateState()

    def _OnClose(self, *args):
        listentry.BaseTextStructure._OnClose(self, *args)
        sm.UnregisterNotify(self)

    def Unload(self):
        self.loaded = 0

    def UpdateState(self):
        self.isupdating = 1
        structureID = self.sr.node.rec.itemID
        state = sm.GetService('pwn').GetStructureState(self.sr.node.rec)
        progressCont = uiutil.FindChild(self, 'progresscontainer')
        if progressCont:
            progressCont.Close()
        controllerID, controllerName = sm.GetService('pwn').GetControllerIDName(structureID)
        targetID = sm.GetService('pwn').GetCurrentTarget(structureID)
        stateLabel = entities.POS_STRUCTURE_STATE[state[0]]
        self.sr.label.text = [uix.GetSlimItemName(self.sr.node.rec),
         '<t>',
         stateLabel,
         '<t>',
         controllerName]
        self.isupdating = 0


class StructureAccess(BaseTextStructure):
    __guid__ = 'listentry.StructureAccess'
    __params__ = ['label']

    def Startup(self, *args):
        listentry.BaseTextStructure.Startup(self, args)
        options = [(localization.GetByLabel('UI/Inflight/MoonMining/Structures/RoleConfigStarbaseEquipment'), 0),
         (localization.GetByLabel('UI/Inflight/MoonMining/Structures/RoleStarbaseFuelTechnician'), 3),
         (localization.GetByLabel('UI/Common/Corporation'), 1),
         (localization.GetByLabel('UI/Common/Alliance'), 2)]
        i = 200
        self.sr.configs = {}
        self.configs = ['viewput', 'viewputtake', 'use']
        for config in self.configs:
            self.sr.configs[config] = uicls.Combo(label='', parent=self, options=options, name=config, callback=self.ComboChange, pos=(i,
             2,
             0,
             0), width=100, align=uiconst.TOPLEFT)
            i += 106

    def Load(self, node):
        listentry.BaseTextStructure.Load(self, node)
        for key in self.configs:
            if key == 'use':
                if node.rec.groupID not in [const.groupShipMaintenanceArray, const.groupRefiningArray]:
                    self.sr.configs['use'].state = uiconst.UI_HIDDEN
                else:
                    self.sr.configs['use'].state = uiconst.UI_NORMAL
                    self.sr.configs['use'].SelectItemByValue(node.flags[key])
            else:
                self.sr.configs[key].SelectItemByValue(node.flags[key])

        if self.sr.node.scroll.sr.tabs:
            self.OnColumnChanged()

    def OnColumnChanged(self, *args):
        i = self.sr.node.scroll.sr.tabs[0]
        self.sr.label.width = i - 6
        for key in self.configs:
            self.sr.configs[key].left = i + 1
            i += 106

    def ComboChange(self, combo, header, value, *args):
        setattr(self.sr.node.flags, combo.name, value)

    def GetHeight(self, *args):
        node, width = args
        comboHeight = uix.GetTextHeight('aA', fontsize=fontConst.EVE_SMALL_FONTSIZE, hspace=1, uppercase=1)
        node.height = comboHeight + 10
        return node.height