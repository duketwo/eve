#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/services/facWarSvc.py
import uiconst
import service
import blue
import util
import uiutil
import localization
import facwarCommon
import uicls
import uthread
import form

class FactionalWarfare(service.Service):
    __exportedcalls__ = {'IsEnemyCorporation': [],
     'JoinFactionAsAlliance': [],
     'JoinFactionAsCorporation': [],
     'JoinFactionAsCharacter': [],
     'LeaveFactionAsCorporation': [],
     'LeaveFactionAsAlliance': [],
     'WithdrawJoinFactionAsAlliance': [],
     'WithdrawJoinFactionAsCorporation': [],
     'WithdrawLeaveFactionAsAlliance': [],
     'WithdrawLeaveFactionAsCorporation': [],
     'GetFactionalWarStatus': [],
     'GetWarFactions': [],
     'GetCorporationWarFactionID': [],
     'GetFactionCorporations': [],
     'GetFactionMilitiaCorporation': [],
     'GetCharacterRankInfo': [],
     'GetEnemies': [],
     'GetStats_FactionInfo': [],
     'GetStats_Personal': [],
     'GetStats_Corp': [],
     'GetStats_Alliance': [],
     'GetStats_CorpPilots': [],
     'GetSystemsConqueredThisRun': [],
     'GetDistanceToEnemySystems': [],
     'GetMostDangerousSystems': [],
     'GetSystemStatus': [],
     'CheckForSafeSystem': [],
     'GetCurrentSystemVictoryPoints': [],
     'GetAllianceWarFactionID': []}
    __guid__ = 'svc.facwar'
    __servicename__ = 'facwar'
    __displayname__ = 'Factional Warfare'
    __notifyevents__ = ['OnNPCStandingChange',
     'ProcessSystemStatusChanged',
     'ProcessSessionChange',
     'OnSolarSystemLPChange',
     'OnSessionChanged']
    __exportedcalls__ = {'ShowRulesOfEngagementTab': [service.ROLE_IGB]}

    def __init__(self):
        service.Service.__init__(self)
        self.facWarSystemCount = {}
        self.warFactionByOwner = {}
        self.topStats = None
        self.statusBySystemID = {}
        self.remoteFacWarMgr = None
        self.solarSystemLPs = {}
        self.solarSystemVictoryPoints = None
        self.solarSystemVictoryPointThreshold = None
        self.FWSystems = None
        self.FWSystemOccupiers = None

    def Run(self, memStream = None):
        self.LogInfo('Starting Factional Warfare Svc')
        self.objectCaching = sm.GetService('objectCaching')

    @property
    def facWarMgr(self):
        if self.remoteFacWarMgr is None:
            self.remoteFacWarMgr = sm.RemoteSvc('facWarMgr')
        return self.remoteFacWarMgr

    def ProcessSystemStatusChanged(self, *args):
        if args[3]:
            sm.ScatterEvent('OnRemoteMessage', args[3][0], args[3][1])
        self.LogInfo('ProcessSystemStatusChanged() called with stateinfo', args[0], args[1], args[2])
        self.solarSystemVictoryPoints = args[0]
        self.solarSystemVictoryPointThreshold = args[1]
        statusinfo = args[2]
        self.LogInfo('Updating state')
        self.statusBySystemID[session.solarsystemid2] = statusinfo[0]
        sm.GetService('infoPanel').UpdateFactionalWarfarePanel()
        sm.ScatterEvent('OnSystemStatusChanged')

    def ProcessSessionChange(self, isRemote, session, change):
        if 'solarsystemid' in change:
            lastSystem, newSystem = change['solarsystemid']
            if lastSystem and self.statusBySystemID.has_key(lastSystem):
                del self.statusBySystemID[lastSystem]
            if newSystem and self.statusBySystemID.has_key(newSystem):
                del self.statusBySystemID[newSystem]
            if newSystem in self.solarSystemLPs:
                del self.solarSystemLPs[newSystem]

    def OnSolarSystemLPChange(self, oldpoints, newpoints):
        self.LogInfo('OnSolarSystemLPChange: ', oldpoints, newpoints)
        self.solarSystemLPs[session.solarsystemid2] = newpoints
        sm.GetService('infoPanel').UpdateFactionalWarfarePanel()

    def GetSolarSystemUpgradeLevel(self, solarsystemID):
        if solarsystemID in self.solarSystemLPs:
            points = self.solarSystemLPs[solarsystemID]
            thresholds = const.facwarSolarSystemUpgradeThresholds
            for i, threshold in enumerate(thresholds):
                if points < threshold:
                    return i

            return len(thresholds)
        else:
            factionID = self.GetSystemOccupier(solarsystemID)
            warZoneInfo = self.GetFacWarZoneInfo(factionID)
            return warZoneInfo.systemUpgradeLevel[solarsystemID]

    def OnSessionChanged(self, isRemote, session, change):
        if 'solarsystemid2' in change:
            if session.solarsystemid2 in self.GetFacWarSystems():
                self.solarSystemVictoryPoints, self.solarSystemVictoryPointThreshold = self.facWarMgr.GetVictoryPointsAndThreshold()
            sm.GetService('infoPanel').UpdateFactionalWarfarePanel()

    def IsEnemyCorporation(self, enemyID, factionID):
        return self.facWarMgr.IsEnemyCorporation(enemyID, factionID)

    def GetSystemsConqueredThisRun(self):
        return self.facWarMgr.GetSystemsConqueredThisRun()

    def GetDistanceToEnemySystems(self):
        if session.warfactionid is None:
            return
        enemyFactions = self.GetEnemies(session.warfactionid)
        enemySystems = [ util.KeyVal(solarSystemID=k, occupierID=v, numJumps=0) for k, v in self.GetFacWarSystemsOccupiers().iteritems() if v in enemyFactions ]
        for s in enemySystems:
            s.numJumps = int(sm.GetService('pathfinder').GetJumpCountFromCurrent(s.solarSystemID))
            blue.pyos.BeNice()

        enemySystems.sort(lambda x, y: cmp(x.numJumps, y.numJumps))
        return enemySystems

    def GetMostDangerousSystems(self):
        historyDB = sm.RemoteSvc('map').GetHistory(const.mapHistoryStatFacWarKills, 24)
        dangerousSystems = []
        for each in historyDB:
            if each.value1 - each.value2 > 0:
                dangerousSystems.append(util.KeyVal(solarSystemID=each.solarSystemID, numKills=each.value1 - each.value2))

        dangerousSystems.sort(lambda x, y: cmp(y.numKills, x.numKills))
        return dangerousSystems

    def GetCorporationWarFactionID(self, corpID):
        if util.IsNPC(corpID):
            for factionID, militiaCorpID in self.GetWarFactions().iteritems():
                if militiaCorpID == corpID:
                    return factionID

            return None
        ret = self.facWarMgr.GetCorporationWarFactionID(corpID)
        if not ret:
            return None
        return ret

    def GetFactionCorporations(self, factionID):
        return self.facWarMgr.GetFactionCorporations(factionID)

    def GetFacWarSystems(self):
        if self.FWSystems is None:
            self.FWSystems = self.facWarMgr.GetFacWarSystems()
        return self.FWSystems

    def GetFacWarSystemsOccupiers(self):
        if self.FWSystemOccupiers is None:
            self.FWSystemOccupiers = self.facWarMgr.GetAllSystemOccupiers()
        return self.FWSystemOccupiers

    def GetAllianceWarFactionID(self, allianceID):
        return self.facWarMgr.GetAllianceWarFactionID(allianceID)

    def GetFactionIDByRaceID(self, raceID):
        if raceID == const.raceCaldari:
            return const.factionCaldariState
        if raceID == const.raceAmarr:
            return const.factionAmarrEmpire
        if raceID == const.raceGallente:
            return const.factionGallenteFederation
        if raceID == const.raceMinmatar:
            return const.factionMinmatarRepublic

    def GetSolarSystemsOccupiedByFactions(self, factionIDs):
        ret = {}
        systems = self.GetFacWarSystemsOccupiers()
        for systemID, occupierID in systems.iteritems():
            if occupierID in factionIDs:
                ret[systemID] = occupierID

        return ret

    def GetSystemOccupier(self, solarSystemID):
        try:
            return self.GetFacWarSystemsOccupiers()[solarSystemID]
        except KeyError:
            return None

    def IsFacWarSystem(self, solarSystemID):
        return solarSystemID in self.GetFacWarSystems()

    def GetFactionWars(self, ownerID):
        factionWars = {}
        warFactionID = self.GetCorporationWarFactionID(ownerID)
        if warFactionID:
            factions = [ each for each in self.GetWarFactions() ]
            factionWars = util.IndexRowset(['warID',
             'declaredByID',
             'againstID',
             'timeDeclared',
             'timeFinished',
             'retracted',
             'retractedBy',
             'billID',
             'mutual'], [], 'warID')
            for i, faction in enumerate(factions):
                if facwarCommon.IsEnemyFaction(faction, warFactionID):
                    factionWars[i * -1] = [None,
                     faction,
                     warFactionID,
                     None,
                     None,
                     None,
                     None,
                     None,
                     True]

        return factionWars

    def GetFactionMilitiaCorporation(self, factionID):
        ret = self.facWarMgr.GetFactionMilitiaCorporation(factionID)
        if not ret:
            return None
        return ret

    def GetFacWarZoneInfo(self, factionID):
        return sm.RemoteSvc('map').GetFacWarZoneInfo(factionID)

    def GetSystemUpgradeLevelBenefits(self, systemUpgradeLevel):
        return facwarCommon.BENEFITS_BY_LEVEL.get(systemUpgradeLevel, [])

    def GetActiveFactionID(self):
        if session.warfactionid:
            return session.warfactionid
        factionID = self.CheckStationElegibleForMilitia()
        if factionID:
            return factionID
        occupierID = self.GetSystemOccupier(session.solarsystemid2)
        if occupierID:
            return occupierID
        return self.GetFactionIDByRaceID(session.raceID)

    def GetSystemCaptureStatus(self, systemID):
        threshold, victoryPoints, occupier = sm.GetService('starmap').GetFacWarData()[systemID]
        if systemID == session.solarsystemid2:
            if self.GetSystemStatus() == const.contestionStateCaptured:
                return facwarCommon.STATE_CAPTURED
        else:
            capturedSystems = self.GetFacWarZoneInfo(self.GetActiveFactionID()).capturedSystems
            if systemID in capturedSystems:
                return facwarCommon.STATE_CAPTURED
        if victoryPoints == 0:
            return facwarCommon.STATE_STABLE
        if victoryPoints < threshold:
            return facwarCommon.STATE_CONTESTED
        return facwarCommon.STATE_VULNERABLE

    def GetSystemCaptureStatusTxt(self, systemID):
        state = self.GetSystemCaptureStatus(systemID)
        if state == facwarCommon.STATE_STABLE:
            return localization.GetByLabel('UI/FactionWarfare/StatusStable')
        if state == facwarCommon.STATE_CONTESTED:
            return localization.GetByLabel('UI/FactionWarfare/StatusContested', num='%04.1f' % self.GetSystemContestedPercentage(systemID))
        if state == facwarCommon.STATE_VULNERABLE:
            return localization.GetByLabel('UI/FactionWarfare/StatusVulnerable')
        if state == facwarCommon.STATE_CAPTURED:
            return '<color=red>' + localization.GetByLabel('UI/Neocom/SystemLost')

    def GetSystemContestedPercentage(self, systemID):
        threshold, victoryPoints, occupier = sm.GetService('starmap').GetFacWarData()[systemID]
        percent = victoryPoints / float(threshold) * 100
        if percent >= 100.0:
            percent = 100.0
        elif percent > 99.9:
            percent = 99.9
        return percent

    def GetCurrentSystemVictoryPoints(self):
        return self.solarSystemVictoryPoints

    def GetCurrentSystemVictoryPointThreshold(self):
        if self.solarSystemVictoryPointThreshold is None:
            _, self.solarSystemVictoryPointThreshold = self.facWarMgr.GetVictoryPointsAndThreshold()
        return self.solarSystemVictoryPointThreshold

    def GetCurrentSystemEffectOfHeldDistricts(self):
        base = float(const.facwarBaseVictoryPointsThreshold)
        curr = float(self.GetCurrentSystemVictoryPointThreshold())
        return (curr - base) / base * 100

    def JoinFactionAsCharacter(self, factionID, warfactionid):
        if warfactionid:
            alreadyInMilitiaLabel = localization.GetByLabel('UI/FactionWarfare/AlreadyInMilitia')
            eve.Message('CustomInfo', {'info': alreadyInMilitiaLabel})
            return
        ownerName = cfg.eveowners.Get(factionID).name
        headerLabel = localization.GetByLabel('UI/FactionWarfare/JoinConfirmationHeader')
        bodyLabel = localization.GetByLabel('UI/FactionWarfare/JoinConfirmationQuestionPlayer', factionName=ownerName)
        ret = eve.Message('CustomQuestion', {'header': headerLabel,
         'question': bodyLabel}, uiconst.YESNO)
        if ret == uiconst.ID_YES:
            sm.GetService('sessionMgr').PerformSessionChange('corp.joinmilitia', self.facWarMgr.JoinFactionAsCharacter, factionID)
            invalidate = [('facWarMgr', 'GetMyCharacterRankInfo', ()),
             ('facWarMgr', 'GetMyCharacterRankOverview', ()),
             ('facWarMgr', 'GetFactionalWarStatus', ()),
             ('corporationSvc', 'GetEmploymentRecord', (session.charid,))]
            self.objectCaching.InvalidateCachedMethodCalls(invalidate)

    def JoinFactionAsAlliance(self, factionID, warfactionid):
        ownerName = cfg.eveowners.Get(factionID).name
        headerLabel = localization.GetByLabel('UI/FactionWarfare/JoinConfirmationHeader')
        bodyLabel = localization.GetByLabel('UI/FactionWarfare/JoinConfirmationQuestionAlliance', factionName=ownerName)
        if warfactionid:
            alreadyInMilitiaLabel = localization.GetByLabel('UI/FactionWarfare/AlreadyInMilitia')
            eve.Message('CustomInfo', {'info': alreadyInMilitiaLabel})
            return
        ret = eve.Message('CustomQuestion', {'header': headerLabel,
         'question': bodyLabel}, uiconst.YESNO)
        if ret == uiconst.ID_YES:
            self.facWarMgr.JoinFactionAsAlliance(factionID)
            self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])
            sm.ScatterEvent('OnJoinMilitia')

    def JoinFactionAsCorporation(self, factionID, warfactionid):
        ownerName = cfg.eveowners.Get(factionID).name
        headerLabel = localization.GetByLabel('UI/FactionWarfare/JoinConfirmationHeader')
        bodyLabel = localization.GetByLabel('UI/FactionWarfare/JoinConfirmationQuestionCorp', factionName=ownerName)
        if warfactionid:
            alreadyInMilitiaLabel = localization.GetByLabel('UI/FactionWarfare/AlreadyInMilitia')
            eve.Message('CustomInfo', {'info': alreadyInMilitiaLabel})
            return
        ret = eve.Message('CustomQuestion', {'header': headerLabel,
         'question': bodyLabel}, uiconst.YESNO)
        if ret == uiconst.ID_YES:
            self.facWarMgr.JoinFactionAsCorporation(factionID)
            self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])
            sm.ScatterEvent('OnJoinMilitia')

    def LeaveFactionAsAlliance(self, factionID):
        self.facWarMgr.LeaveFactionAsAlliance(factionID)
        self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])

    def LeaveFactionAsCorporation(self, factionID):
        self.facWarMgr.LeaveFactionAsCorporation(factionID)
        self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])

    def WithdrawJoinFactionAsAlliance(self, factionID):
        self.facWarMgr.WithdrawJoinFactionAsAlliance(factionID)
        self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])

    def WithdrawJoinFactionAsCorporation(self, factionID):
        self.facWarMgr.WithdrawJoinFactionAsCorporation(factionID)
        self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])

    def WithdrawLeaveFactionAsAlliance(self, factionID):
        self.facWarMgr.WithdrawLeaveFactionAsAlliance(factionID)
        self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])

    def WithdrawLeaveFactionAsCorporation(self, factionID):
        self.facWarMgr.WithdrawLeaveFactionAsCorporation(factionID)
        self.objectCaching.InvalidateCachedMethodCalls([('facWarMgr', 'GetFactionalWarStatus', ())])

    def GetFactionalWarStatus(self):
        return self.facWarMgr.GetFactionalWarStatus()

    def GetWarFactions(self):
        return self.facWarMgr.GetWarFactions()

    def GetCharacterRankInfo(self, charID, corpID = None):
        if corpID is None or self.GetCorporationWarFactionID(corpID) is not None:
            if charID == session.charid:
                return self.facWarMgr.GetMyCharacterRankInfo()
            else:
                return self.facWarMgr.GetCharacterRankInfo(charID)

    def GetCharacterRankOverview(self, charID):
        if not charID == session.charid:
            return None
        return self.facWarMgr.GetMyCharacterRankOverview()

    def RefreshCorps(self):
        return self.facWarMgr.RefreshCorps()

    def OnNPCStandingChange(self, fromID, newStanding, oldStanding):
        if fromID == self.GetFactionMilitiaCorporation(session.warfactionid):
            oldrank = self.GetCharacterRankInfo(session.charid).currentRank
            if oldrank != min(max(int(newStanding), 0), 9):
                newrank = self.facWarMgr.CheckForRankChange()
                if newrank is not None and oldrank != newrank:
                    self.DoOnRankChange(oldrank, newrank)
        invalidate = [('facWarMgr', 'GetMyCharacterRankInfo', ()), ('facWarMgr', 'GetMyCharacterRankOverview', ())]
        self.objectCaching.InvalidateCachedMethodCalls(invalidate)

    def DoOnRankChange(self, oldrank, newrank):
        messageID = 'RankGained' if newrank > oldrank else 'RankLost'
        rankLabel, rankDescription = self.GetRankLabel(session.warfactionid, newrank)
        try:
            eve.Message(messageID, {'rank': rankLabel})
        except:
            sys.exc_clear()

        sm.ScatterEvent('OnRankChange', oldrank, newrank)

    def GetEnemies(self, factionID):
        warFactions = self.GetWarFactions()
        enemies = []
        for each in warFactions.iterkeys():
            if facwarCommon.IsEnemyFaction(factionID, each):
                enemies.append(each)

        return enemies

    def GetStats_FactionInfo(self):
        return self.facWarMgr.GetStats_FactionInfo()

    def GetStats_Personal(self):
        header = ['you', 'top', 'all']
        data = {'killsY': {'you': 0,
                    'top': 0,
                    'all': 0},
         'killsLW': {'you': 0,
                     'top': 0,
                     'all': 0},
         'killsTotal': {'you': 0,
                        'top': 0,
                        'all': 0},
         'vpY': {'you': 0,
                 'top': 0,
                 'all': 0},
         'vpLW': {'you': 0,
                  'top': 0,
                  'all': 0},
         'vpTotal': {'you': 0,
                     'top': 0,
                     'all': 0}}
        if not self.topStats:
            self.topStats = self.facWarMgr.GetStats_TopAndAllKillsAndVPs()
        for k in ('killsY', 'killsLW', 'killsTotal', 'vpY', 'vpLW', 'vpTotal'):
            data[k]['top'] = self.topStats[0][const.groupCharacter][k]
            data[k]['all'] = self.topStats[1][const.groupCharacter][k]

        for k, v in self.facWarMgr.GetStats_Character().items():
            data[k]['you'] = v

        return {'header': header,
         'data': data}

    def GetStats_Corp(self, corpID):
        header = ['your', 'top', 'all']
        data = {'killsY': {'your': 0,
                    'top': 0,
                    'all': 0},
         'killsLW': {'your': 0,
                     'top': 0,
                     'all': 0},
         'killsTotal': {'your': 0,
                        'top': 0,
                        'all': 0},
         'vpY': {'your': 0,
                 'top': 0,
                 'all': 0},
         'vpLW': {'your': 0,
                  'top': 0,
                  'all': 0},
         'vpTotal': {'your': 0,
                     'top': 0,
                     'all': 0}}
        if not self.topStats:
            self.topStats = self.facWarMgr.GetStats_TopAndAllKillsAndVPs()
        for k in ('killsY', 'killsLW', 'killsTotal', 'vpY', 'vpLW', 'vpTotal'):
            data[k]['top'] = self.topStats[0][const.groupCorporation][k]
            data[k]['all'] = self.topStats[1][const.groupCorporation][k]

        for k, v in self.facWarMgr.GetStats_Corp().items():
            data[k]['your'] = v

        return {'header': header,
         'data': data}

    def GetStats_Alliance(self, allianceID):
        header = ['your', 'top', 'all']
        data = {'killsY': {'your': 0,
                    'top': 0,
                    'all': 0},
         'killsLW': {'your': 0,
                     'top': 0,
                     'all': 0},
         'killsTotal': {'your': 0,
                        'top': 0,
                        'all': 0},
         'vpY': {'your': 0,
                 'top': 0,
                 'all': 0},
         'vpLW': {'your': 0,
                  'top': 0,
                  'all': 0},
         'vpTotal': {'your': 0,
                     'top': 0,
                     'all': 0}}
        if not self.topStats:
            self.topStats = self.facWarMgr.GetStats_TopAndAllKillsAndVPs()
        for k in ('killsY', 'killsLW', 'killsTotal', 'vpY', 'vpLW', 'vpTotal'):
            data[k]['top'] = self.topStats[0][const.groupAlliance][k]
            data[k]['all'] = self.topStats[1][const.groupAlliance][k]

        for k, v in self.facWarMgr.GetStats_Alliance().items():
            data[k]['your'] = v

        return {'header': header,
         'data': data}

    def GetStats_Militia(self):
        return self.facWarMgr.GetStats_Militia()

    def GetStats_CorpPilots(self):
        return self.facWarMgr.GetStats_CorpPilots()

    def GetStats_Systems(self):
        systemsThatWillSwitchNextDownTime = self.GetSystemsConqueredThisRun()
        cfg.evelocations.Prime([ d['solarsystemID'] for d in systemsThatWillSwitchNextDownTime ])
        cfg.eveowners.Prime([ d['occupierID'] for d in systemsThatWillSwitchNextDownTime ])
        tempList = []
        for each in systemsThatWillSwitchNextDownTime:
            tempList.append((each.get('taken'), each))

        systemsThatWillSwitchNextDownTime = uiutil.SortListOfTuples(tempList, reverse=1)
        return systemsThatWillSwitchNextDownTime

    def CheckOwnerInFaction(self, ownerID, factionID = None):
        factions = [ each for each in self.GetWarFactions() ]
        if not self.warFactionByOwner.has_key(ownerID):
            faction = sm.GetService('faction').GetFaction(ownerID)
            if faction and faction in factions:
                self.warFactionByOwner[ownerID] = faction
        return self.warFactionByOwner.get(ownerID, None)

    def GetSystemStatus(self):
        if self.statusBySystemID.has_key(session.solarsystemid2):
            self.LogInfo('GetSystemStatus: Returning cached status:', self.statusBySystemID[session.solarsystemid2])
            return self.statusBySystemID[session.solarsystemid2]
        status = self.facWarMgr.GetSystemStatus(session.solarsystemid2)
        self.statusBySystemID[session.solarsystemid2] = status
        self.LogInfo('GetSystemStatus: Returning status from server:', status)
        return status

    def CheckForSafeSystem(self, stationItem, factionID, solarSystemID = None):
        ss = sm.GetService('map').GetSecurityClass(solarSystemID or session.solarsystemid2)
        if ss != const.securityClassHighSec:
            return True
        fosi = sm.GetService('faction').GetFaction(stationItem.ownerID)
        if fosi is None:
            return True
        foss = sm.GetService('faction').GetFactionOfSolarSystem(solarSystemID or session.solarsystemid2)
        eof = self.GetEnemies(factionID)
        if foss in eof:
            return False
        return True

    def CheckStationElegibleForMilitia(self, station = None):
        if session.warfactionid:
            return session.warfactionid
        if station is None and not session.stationid2:
            return False
        ownerID = None
        if station:
            ownerID = station.ownerID
        elif session.stationid2:
            ownerID = eve.stationItem.ownerID
        if ownerID:
            check = self.CheckOwnerInFaction(ownerID)
            if check is not None:
                return check
        return False

    def GetRankLabel(self, factionID, rank):
        rank = min(9, rank)
        rankLabel, rankDescription = ('', '')
        if rank < 0:
            rankLabel = localization.GetByLabel('UI/FactionWarfare/Ranks/NoRank')
            rankDescription = ''
        else:
            rankPath, descPath = RankLabelsByFactionID.get((factionID, rank), ('UI/FactionWarfare/Ranks/NoRank', 'UI/FactionWarfare/Ranks/NoRank'))
            rankLabel = localization.GetByLabel(rankPath)
            rankDescription = localization.GetByLabel(descPath)
        return (rankLabel, rankDescription)

    def GetSolarSystemLPs(self):
        if not self.IsFacWarSystem(session.solarsystemid2):
            return 0
        if session.solarsystemid2 not in self.solarSystemLPs:
            self.solarSystemLPs[session.solarsystemid2] = self.facWarMgr.GetSolarSystemLPs()
        return self.solarSystemLPs[session.solarsystemid2]

    def DonateLPsToSolarSystem(self, pointsDonated, pointsToIhub):
        pointsDonated = max(pointsDonated, const.facwarMinLPDonation)
        militiaCorpID = self.GetFactionMilitiaCorporation(session.warfactionid)
        if militiaCorpID is None:
            raise RuntimeError("Don't know the militia corp for faction", session.warfactionid)
        pointsWithCorp = sm.GetService('lpstore').GetMyLPs(militiaCorpID)
        if pointsDonated > pointsWithCorp:
            militiaName = cfg.eveowners.Get(militiaCorpID).ownerName
            raise UserError('FacWarCantDonateSoMuch', {'militiaName': militiaName,
             'points': pointsWithCorp})
        solarSystemLPs = self.GetSolarSystemLPs()
        if pointsToIhub + solarSystemLPs > const.facwarSolarSystemMaxLPPool:
            militiaName = cfg.eveowners.Get(militiaCorpID).ownerName
            maxPointsToAdd = const.facwarSolarSystemMaxLPPool - solarSystemLPs
            raise UserError('FacWarPoolOverloaded', {'militiaName': militiaName,
             'points': maxPointsToAdd})
        return self.facWarMgr.DonateLPsToSolarSystem(pointsDonated, pointsToIhub)

    def ShowRulesOfEngagementTab(self):
        wnd = form.MilitiaWindow.GetIfOpen()
        if wnd:
            wnd.ShowRulesOfEngagementTab()


RankLabelsByFactionID = {(const.factionCaldariState, 0): ('UI/FactionWarfare/Ranks/RankCaldari0', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari0'),
 (const.factionCaldariState, 1): ('UI/FactionWarfare/Ranks/RankCaldari1', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari1'),
 (const.factionCaldariState, 2): ('UI/FactionWarfare/Ranks/RankCaldari2', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari2'),
 (const.factionCaldariState, 3): ('UI/FactionWarfare/Ranks/RankCaldari3', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari3'),
 (const.factionCaldariState, 4): ('UI/FactionWarfare/Ranks/RankCaldari4', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari4'),
 (const.factionCaldariState, 5): ('UI/FactionWarfare/Ranks/RankCaldari5', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari5'),
 (const.factionCaldariState, 6): ('UI/FactionWarfare/Ranks/RankCaldari6', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari6'),
 (const.factionCaldariState, 7): ('UI/FactionWarfare/Ranks/RankCaldari7', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari7'),
 (const.factionCaldariState, 8): ('UI/FactionWarfare/Ranks/RankCaldari8', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari8'),
 (const.factionCaldariState, 9): ('UI/FactionWarfare/Ranks/RankCaldari9', 'UI/FactionWarfare/Ranks/RankDescriptionCaldari9'),
 (const.factionMinmatarRepublic, 0): ('UI/FactionWarfare/Ranks/RankMinmatar0', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar0'),
 (const.factionMinmatarRepublic, 1): ('UI/FactionWarfare/Ranks/RankMinmatar1', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar1'),
 (const.factionMinmatarRepublic, 2): ('UI/FactionWarfare/Ranks/RankMinmatar2', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar2'),
 (const.factionMinmatarRepublic, 3): ('UI/FactionWarfare/Ranks/RankMinmatar3', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar3'),
 (const.factionMinmatarRepublic, 4): ('UI/FactionWarfare/Ranks/RankMinmatar4', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar4'),
 (const.factionMinmatarRepublic, 5): ('UI/FactionWarfare/Ranks/RankMinmatar5', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar5'),
 (const.factionMinmatarRepublic, 6): ('UI/FactionWarfare/Ranks/RankMinmatar6', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar6'),
 (const.factionMinmatarRepublic, 7): ('UI/FactionWarfare/Ranks/RankMinmatar7', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar7'),
 (const.factionMinmatarRepublic, 8): ('UI/FactionWarfare/Ranks/RankMinmatar8', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar8'),
 (const.factionMinmatarRepublic, 9): ('UI/FactionWarfare/Ranks/RankMinmatar9', 'UI/FactionWarfare/Ranks/RankDescriptionMinmatar9'),
 (const.factionAmarrEmpire, 0): ('UI/FactionWarfare/Ranks/RankAmarr0', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr0'),
 (const.factionAmarrEmpire, 1): ('UI/FactionWarfare/Ranks/RankAmarr1', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr1'),
 (const.factionAmarrEmpire, 2): ('UI/FactionWarfare/Ranks/RankAmarr2', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr2'),
 (const.factionAmarrEmpire, 3): ('UI/FactionWarfare/Ranks/RankAmarr3', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr3'),
 (const.factionAmarrEmpire, 4): ('UI/FactionWarfare/Ranks/RankAmarr4', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr4'),
 (const.factionAmarrEmpire, 5): ('UI/FactionWarfare/Ranks/RankAmarr5', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr5'),
 (const.factionAmarrEmpire, 6): ('UI/FactionWarfare/Ranks/RankAmarr6', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr6'),
 (const.factionAmarrEmpire, 7): ('UI/FactionWarfare/Ranks/RankAmarr7', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr7'),
 (const.factionAmarrEmpire, 8): ('UI/FactionWarfare/Ranks/RankAmarr8', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr8'),
 (const.factionAmarrEmpire, 9): ('UI/FactionWarfare/Ranks/RankAmarr9', 'UI/FactionWarfare/Ranks/RankDescriptionAmarr9'),
 (const.factionGallenteFederation, 0): ('UI/FactionWarfare/Ranks/RankGallente0', 'UI/FactionWarfare/Ranks/RankDescriptionGallente0'),
 (const.factionGallenteFederation, 1): ('UI/FactionWarfare/Ranks/RankGallente1', 'UI/FactionWarfare/Ranks/RankDescriptionGallente1'),
 (const.factionGallenteFederation, 2): ('UI/FactionWarfare/Ranks/RankGallente2', 'UI/FactionWarfare/Ranks/RankDescriptionGallente2'),
 (const.factionGallenteFederation, 3): ('UI/FactionWarfare/Ranks/RankGallente3', 'UI/FactionWarfare/Ranks/RankDescriptionGallente3'),
 (const.factionGallenteFederation, 4): ('UI/FactionWarfare/Ranks/RankGallente4', 'UI/FactionWarfare/Ranks/RankDescriptionGallente4'),
 (const.factionGallenteFederation, 5): ('UI/FactionWarfare/Ranks/RankGallente5', 'UI/FactionWarfare/Ranks/RankDescriptionGallente5'),
 (const.factionGallenteFederation, 6): ('UI/FactionWarfare/Ranks/RankGallente6', 'UI/FactionWarfare/Ranks/RankDescriptionGallente6'),
 (const.factionGallenteFederation, 7): ('UI/FactionWarfare/Ranks/RankGallente7', 'UI/FactionWarfare/Ranks/RankDescriptionGallente7'),
 (const.factionGallenteFederation, 8): ('UI/FactionWarfare/Ranks/RankGallente8', 'UI/FactionWarfare/Ranks/RankDescriptionGallente8'),
 (const.factionGallenteFederation, 9): ('UI/FactionWarfare/Ranks/RankGallente9', 'UI/FactionWarfare/Ranks/RankDescriptionGallente9')}