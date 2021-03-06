#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/standingLevelSelector.py
import uicls
import uiconst
import localization
import state

class StandingLevelSelector(uicls.Container):
    __guid__ = 'uicls.StandingLevelSelector'

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        self.level = attributes.get('level', None)
        self.iconPadding = attributes.get('iconPadding', 6)
        self.vertical = attributes.get('vertical', False)
        if attributes.get('callback', None):
            self.OnStandingLevelSelected = attributes.get('callback', None)
        self.ConstructLayout()

    def ConstructLayout(self):
        self.standingList = {const.contactHighStanding: localization.GetByLabel('UI/PeopleAndPlaces/ExcellentStanding'),
         const.contactGoodStanding: localization.GetByLabel('UI/PeopleAndPlaces/GoodStanding'),
         const.contactNeutralStanding: localization.GetByLabel('UI/PeopleAndPlaces/NeutralStanding'),
         const.contactBadStanding: localization.GetByLabel('UI/PeopleAndPlaces/BadStanding'),
         const.contactHorribleStanding: localization.GetByLabel('UI/PeopleAndPlaces/TerribleStanding')}
        levelList = self.standingList.keys()
        levelList.sort()
        shift = 20 + self.iconPadding
        for i, relationshipLevel in enumerate(levelList):
            leftPos = i * shift * float(not self.vertical)
            rightPos = i * shift * float(self.vertical)
            contName = 'level%d' % i
            level = uicls.StandingsContainer(name=contName, parent=self, align=uiconst.TOPLEFT, pos=(leftPos,
             rightPos,
             20,
             20), level=relationshipLevel, text=self.standingList.get(relationshipLevel), windowName='contactmanagement')
            setattr(self.sr, contName, level)
            level.OnClick = (self.LevelOnClick, relationshipLevel, level)
            if self.level == relationshipLevel:
                level.sr.selected.state = uiconst.UI_DISABLED
                uicore.registry.SetFocus(level)

    def LevelOnClick(self, level, container, *args):
        for i in xrange(0, 5):
            cont = self.sr.Get('level%d' % i)
            cont.sr.selected.state = uiconst.UI_HIDDEN

        container.sr.selected.state = uiconst.UI_DISABLED
        self.level = level
        if hasattr(self, 'OnStandingLevelSelected'):
            self.OnStandingLevelSelected(level)

    def GetValue(self):
        return self.level


class StandingsContainer(uicls.Container):
    __guid__ = 'uicls.StandingsContainer'

    def ApplyAttributes(self, attributes):
        uicls.Container.ApplyAttributes(self, attributes)
        text = attributes.get('text', '')
        self.text = text
        level = attributes.get('level', None)
        self.level = level
        windowName = attributes.get('windowName', '')
        self.enabled = attributes.get('enabled', True)
        self.windowName = windowName
        self.Prepare_(text, level)
        self.cursor = 1

    def Prepare_(self, text = '', contactLevel = None, *args):
        self.isTabStop = 1
        self.state = uiconst.UI_NORMAL
        flag = None
        iconNum = 0
        if contactLevel == const.contactHighStanding:
            flag = state.flagStandingHigh
            iconNum = 3
        elif contactLevel == const.contactGoodStanding:
            flag = state.flagStandingGood
            iconNum = 3
        elif contactLevel == const.contactNeutralStanding:
            flag = state.flagStandingNeutral
            iconNum = 5
        elif contactLevel == const.contactBadStanding:
            flag = state.flagStandingBad
            iconNum = 4
        elif contactLevel == const.contactHorribleStanding:
            flag = state.flagStandingHorrible
            iconNum = 4
        if flag:
            col = sm.GetService('state').GetStateFlagColor(flag)
            if not self.enabled:
                avgCol = col[0] / 3.0 + col[1] / 3.0 + col[1] / 3.0
                col = (avgCol, avgCol, avgCol)
            flag = uicls.Container(parent=self, pos=(0, 0, 20, 20), name='flag', state=uiconst.UI_DISABLED, align=uiconst.RELATIVE)
            selected = uicls.Frame(parent=flag, color=(1.0, 1.0, 1.0, 0.75), state=uiconst.UI_HIDDEN)
            hilite = uicls.Frame(parent=flag, color=(1.0, 1.0, 1.0, 0.75), state=uiconst.UI_HIDDEN)
            uicls.Sprite(parent=flag, pos=(3, 3, 15, 15), name='icon', state=uiconst.UI_DISABLED, rectLeft=iconNum * 10, rectWidth=10, rectHeight=10, texturePath='res:/UI/Texture/classes/Bracket/flagIcons.png', align=uiconst.RELATIVE)
            fill = uicls.Fill(parent=flag, color=col)
            uicls.Frame(parent=self, color=(1.0, 1.0, 1.0, 0.2))
            fill.color.a = 0.6
            self.sr.hilite = hilite
            self.sr.selected = selected
            if self.enabled:
                self.hint = text

    def OnMouseEnter(self, *args):
        if self.enabled:
            self.sr.hilite.state = uiconst.UI_DISABLED

    def OnMouseExit(self, *args):
        if self.enabled:
            self.sr.hilite.state = uiconst.UI_HIDDEN

    def OnSetFocus(self, *args):
        if self.enabled:
            self.sr.hilite.state = uiconst.UI_DISABLED

    def OnKillFocus(self, *args):
        if self.enabled:
            self.sr.hilite.state = uiconst.UI_HIDDEN

    def OnChar(self, char, *args):
        if char in (uiconst.VK_SPACE, uiconst.VK_RETURN):
            self.parent.LevelOnClick(self.level, self)