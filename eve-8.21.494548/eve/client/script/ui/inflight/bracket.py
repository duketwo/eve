#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/eve/client/script/ui/inflight/bracket.py
import weakref
import blue
import telemetry
import xtriui
import uix
import mathUtil
import uthread
import util
import state
import base
import menu
import trinity
import fleetbr
import uiutil
import uiconst
import pos
import uicls
import maputils
import log
import random
import entities
import localization
import fontConst
import bracketUtils
SHOWLABELS_NEVER = 0
SHOWLABELS_ONMOUSEENTER = 1
SHOWLABELS_ALWAYS = 2
TARGETTING_UI_UPDATE_RATE = 50
LABELMARGIN = 6
entityStateStrings = {entities.STATE_ANCHORING: 'Entities/States/Anchoring',
 entities.STATE_ONLINING: 'Entities/States/Onlining',
 entities.STATE_ANCHORED: 'Entities/States/Anchored',
 entities.STATE_UNANCHORING: 'Entities/States/Unanchoring',
 entities.STATE_UNANCHORED: 'Entities/States/Unanchored',
 entities.STATE_INCAPACITATED: 'Entities/States/Incapacitated',
 entities.STATE_IDLE: 'Entities/States/Idle',
 entities.STATE_COMBAT: 'Entities/States/Fighting',
 entities.STATE_MINING: 'Entities/States/Mining',
 entities.STATE_APPROACHING: 'Entities/States/Approaching',
 entities.STATE_FLEEING: 'Entities/States/Fleeing',
 entities.STATE_REINFORCED: 'Entities/States/Reinforced',
 entities.STATE_OPERATING: 'Entities/States/Operating',
 entities.STATE_VULNERABLE: 'Entities/States/Vulnerable',
 entities.STATE_INVULNERABLE: 'Entities/States/Invulnerable',
 entities.STATE_SHIELD_REINFORCE: 'Entities/States/ShieldReinforced',
 entities.STATE_ARMOR_REINFORCE: 'Entities/States/ArmorReinforced',
 entities.STATE_SALVAGING: 'Entities/States/Salvaging'}

def GetEntityStateString(entityState):
    if entityState in entityStateStrings:
        return localization.GetByLabel(entityStateStrings[entityState])
    else:
        return localization.GetByLabel('Entities/States/Unknown', entityStateID=entityState)


class BracketLabel(uicls.Label):
    __guid__ = 'xtriui.BracketLabel'
    default_fontsize = fontConst.EVE_SMALL_FONTSIZE
    default_fontStyle = fontConst.STYLE_SMALLTEXT
    default_shadowOffset = (0, 1)
    displayText = None

    def ApplyAttributes(self, attributes):
        uicls.Label.ApplyAttributes(self, attributes)
        bracket = attributes.bracket
        cs = uicore.uilib.bracketCurveSet
        xBinding = trinity.CreateBinding(cs, bracket.renderObject, 'displayX', self.renderObject, 'displayX')
        yBinding = trinity.CreateBinding(cs, bracket.renderObject, 'displayY', self.renderObject, 'displayY')
        self.bindings = (xBinding, yBinding)
        self.OnMouseUp = bracket.OnMouseUp
        self.OnMouseDown = bracket.OnMouseDown
        self.OnMouseEnter = bracket.OnMouseEnter
        self.OnMouseExit = bracket.OnMouseExit
        self.OnMouseHover = bracket.OnMouseHover
        self.OnClick = bracket.OnClick
        self.OnDblClick = bracket.OnDblClick
        self.GetMenu = bracket.GetMenu

    def Close(self, *args, **kw):
        if getattr(self, 'bindings', None):
            cs = uicore.uilib.bracketCurveSet
            for each in self.bindings:
                if cs and each in cs.bindings:
                    cs.bindings.remove(each)

        self.OnMouseUp = None
        self.OnMouseDown = None
        self.OnMouseEnter = None
        self.OnMouseExit = None
        self.OnMouseHover = None
        self.OnClick = None
        self.GetMenu = None
        uicls.Label.Close(self, *args, **kw)


class BracketSubIcon(uicls.Icon):
    __guid__ = 'uicls.BracketSubIcon'

    def ApplyAttributes(self, attributes):
        uicls.Icon.ApplyAttributes(self, attributes)
        bracket = attributes.bracket
        cs = uicore.uilib.bracketCurveSet
        xBinding = trinity.CreateBinding(cs, bracket.renderObject, 'displayX', self.renderObject, 'displayX')
        yBinding = trinity.CreateBinding(cs, bracket.renderObject, 'displayY', self.renderObject, 'displayY')
        self.bindings = (xBinding, yBinding)
        self.OnMouseUp = bracket.OnMouseUp
        self.OnMouseDown = bracket.OnMouseDown
        self.OnMouseEnter = bracket.OnMouseEnter
        self.OnMouseExit = bracket.OnMouseExit
        self.OnMouseHover = bracket.OnMouseHover
        self.OnClick = bracket.OnClick
        self.GetMenu = bracket.GetMenu

    def Close(self, *args, **kw):
        if getattr(self, 'bindings', None):
            cs = uicore.uilib.bracketCurveSet
            for each in self.bindings:
                if cs and each in cs.bindings:
                    cs.bindings.remove(each)

        self.OnMouseUp = None
        self.OnMouseDown = None
        self.OnMouseEnter = None
        self.OnMouseExit = None
        self.OnMouseHover = None
        self.OnClick = None
        self.GetMenu = None
        uicls.Icon.Close(self, *args, **kw)


class SimpleBracket(uicls.Bracket):
    __guid__ = 'xtriui.SimpleBracket'
    default_width = 16
    default_height = 16
    targetingPath = None
    stateItemID = None
    fleetBroadcastIcon = None
    fleetTagAndTarget = None
    _originalIconColor = None
    _fleetTag = None
    _fleetTargetNo = None

    def Startup_update(self, *args):
        self.sr.targetItem = None

    def ApplyAttributes(self, attributes):
        uicls.Bracket.ApplyAttributes(self, attributes)
        self.IsBracket = 1
        self.invisible = False
        self.inflight = False
        self.categoryID = None
        self.groupID = None
        self.itemID = None
        self.displayName = ''
        self.displaySubLabel = ''
        self.sr.icon = None
        self.sr.flag = None
        self.sr.bgColor = None
        self.sr.hilite = None
        self.sr.selection = None
        self.sr.posStatus = None
        self.sr.orbitalHack = None
        self.sr.orbitalHackLocal = None
        self.slimItem = None
        self.ball = None
        self.stateItemID = None
        self.label = None
        self.subLabel = None
        self.fadeColor = True
        self.iconNo = None
        self.iconXOffset = 0
        self.lastPosEvent = None
        self.scanAttributeChangeFlag = False
        self.iconTop = 0

    def Close(self, *args, **kw):
        self.subItemsUpdateTimer = None
        if getattr(self, 'label', None):
            self.label.Close()
            self.label = None
        if getattr(self, 'subLabel', None):
            self.subLabel.Close()
            self.subLabel = None
        if getattr(self, 'fleetBroadcastIcon', None):
            self.fleetBroadcastIcon.Close()
            self.fleetBroadcastIcon = None
        if getattr(self, 'fleetTagAndTarget', None):
            self.fleetTagAndTarget.Close()
            self.fleetTagAndTarget = None
        uicls.Bracket.Close(self, *args, **kw)

    def Show(self):
        projectBracket = self.projectBracket
        if projectBracket:
            projectBracket.bracket = self.renderObject
        uicls.Bracket.Show(self)

    def Hide(self):
        uicls.Bracket.Hide(self)
        self.KillLabel()
        projectBracket = self.projectBracket
        if projectBracket:
            projectBracket.bracket = None

    def Startup(self, itemID, groupID, categoryID, iconNo):
        self.iconNo = iconNo
        self.LoadIcon(iconNo)
        self.itemID = itemID
        self.stateItemID = itemID
        self.groupID = groupID
        self.categoryID = categoryID

    def LoadIcon(self, iconNo):
        if getattr(self, 'noIcon', 0) == 1:
            return
        if self.sr.icon is None:
            icon = uicls.Icon(parent=self, name='mainicon', state=uiconst.UI_DISABLED, pos=(0, 0, 16, 16), icon=iconNo, align=uiconst.RELATIVE)
            if self.fadeColor:
                self.color = icon.color
            else:
                icon.color.a = 0.75
            self.sr.icon = icon
        else:
            self.sr.icon.LoadIcon(iconNo)

    def ShowLabel(self, *args):
        if not self.destroyed and (self.displayName == '' or not getattr(self, 'showLabel', True)):
            return
        if not self.label:
            self.label = BracketLabel(parent=self.parent, name='labelparent', idx=0, align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL, text=self.displayName, bracket=self)
        if not self.subLabel and self.displaySubLabel:
            self.subLabel = BracketLabel(parent=self.parent, name='sublabelparent', align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL, text=self.displaySubLabel, bracket=self)
        if hasattr(self, 'UpdateSubItems'):
            self.UpdateSubItems()

    def KillLabel(self, *args, **kwds):
        if getattr(self, 'label', None):
            self.label.Close()
        if getattr(self, 'subLabel', None):
            self.subLabel.Close()
        self.label = None
        self.subLabel = None
        if hasattr(self, 'UpdateSubItems'):
            self.UpdateSubItems()

    def GetMenu(self):
        return None

    def Select(self, status):
        if status:
            if not self.sr.selection:
                self.sr.selection = uicls.Sprite(parent=self, pos=(0, 0, 30, 30), name='selection', state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Bracket/selectionCircle.png', align=uiconst.CENTER, color=(1, 1, 1, 0.5))
            self.sr.selection.display = True
            self.ShowLabel()
        else:
            if self.sr.selection:
                self.sr.selection.state = uiconst.UI_HIDDEN
            if self.projectBracket and self.projectBracket.bracket:
                self.KillLabel()

    def Hilite(self, status):
        if status and self.state != uiconst.UI_HIDDEN:
            uthread.pool('Bracket::Hilite', self._ShowLabel)
        elif self.projectBracket and self.projectBracket.bracket and sm.GetService('state').GetExclState(state.selected) != self.itemID:
            self.KillLabel()

    def _ShowLabel(self):
        blue.pyos.synchro.SleepWallclock(50)
        if self.destroyed:
            return
        over = uicore.uilib.mouseOver
        if getattr(over, 'stateItemID', None) == self.itemID:
            self.ShowLabel()

    def GetDistance(self):
        ball = self.ball
        if ball:
            return ball.surfaceDist
        slimItem = self.GetSlimItem()
        if slimItem:
            ballPark = sm.GetService('michelle').GetBallpark()
            if ballPark and slimItem.itemID in ballPark.balls:
                return ballPark.balls[slimItem.itemID].surfaceDist
        elif self.trackTransform or self.sr.trackTransform:
            tf = self.trackTransform or self.sr.trackTransform
            trans = tf.translation
            pos = trinity.TriVector(trans[0], trans[1], trans[2])
            myPos = maputils.GetMyPos()
            return (pos - myPos).Length()

    @apply
    def ball():
        doc = ''

        def fget(self):
            if self._ball:
                return self._ball()

        def fset(self, value):
            if value is None:
                self._ball = None
                return
            self._ball = weakref.ref(value)

        return property(**locals())

    def GetSlimItem(self):
        return self.slimItem

    def HideBubble(self):
        if self.sr.bubble is not None:
            self.sr.bubble.Close()
            self.sr.bubble = None

    def ShowBubble(self, hint):
        if self.sr.bubble is not None:
            self.sr.bubble.Close()
            self.sr.bubble = None
        if hint:
            bubble = xtriui.BubbleHint(parent=self, name='bubblehint', align=uiconst.TOPLEFT, width=0, height=0, idx=0, state=uiconst.UI_PICKCHILDREN)
            pointer = {const.groupStargate: 5,
             const.groupStation: 3}.get(self.groupID, 0)
            bubble.ShowHint(hint, pointer)
            self.sr.bubble = bubble
            self.sr.bubble.state = uiconst.UI_NORMAL

    def GetLockedPositionTopBottomMargin(self):
        hasBubble = bool(self.sr.bubble)
        topMargin = 1
        bottomMargin = 1
        if hasBubble:
            if self.sr.bubble.data[1] in (3, 4, 5):
                bottomMargin += self.sr.bubble.height + 8
            elif self.sr.bubble.data[1] in (0, 1, 2):
                topMargin += self.sr.bubble.height + 8
        else:
            if getattr(self, 'subLabel', None):
                bottomMargin += self.subLabel.textheight
            if getattr(self, 'fleetTagAndTarget', None):
                topMargin += self.fleetTagAndTarget.textheight
        return (topMargin, bottomMargin)

    subItemsUpdateTimer = None

    def OnMouseDown(self, *args):
        if getattr(self, 'slimItem', None):
            if sm.GetService('menu').TryExpandActionMenu(self.itemID, uicore.uilib.x, uicore.uilib.y, self):
                return
        sm.GetService('viewState').GetView('inflight').layer.looking = True

    def OnMouseEnter(self, *args):
        if uicore.uilib.leftbtn:
            return
        if self.itemID == sm.GetService('bracket').CheckingOverlaps():
            return
        if not getattr(self, 'invisible', False):
            sm.GetService('state').SetState(self.itemID, state.mouseOver, 1)
        if self.projectBracket and self.projectBracket.bracket:
            sm.GetService('bracket').CheckOverlaps(self, not getattr(self, 'inflight', 1))

    def OnMouseExit(self, *args):
        if uicore.uilib.leftbtn:
            return
        if self.projectBracket and self.projectBracket.bracket:
            over = uicore.uilib.mouseOver
            if self.itemID == sm.GetService('bracket').CheckingOverlaps():
                return
            sm.GetService('state').SetState(self.itemID, state.mouseOver, 0)

    def OnClick(self, *args):
        if self.sr.clicktime and blue.os.TimeDiffInMs(self.sr.clicktime, blue.os.GetWallclockTime()) < 1000.0:
            cameraSvc = sm.GetService('camera')
            if cameraSvc.IsFreeLook():
                cameraSvc.LookAt(self.itemID)
                return
            sm.GetService('state').SetState(self.itemID, state.selected, 1)
            slimItem = getattr(self, 'slimItem', None)
            if slimItem:
                if uicore.uilib.Key(uiconst.VK_CONTROL):
                    return
                sm.GetService('menu').Activate(slimItem)
            self.sr.clicktime = None
        else:
            sm.GetService('state').SetState(self.itemID, state.selected, 1)
            if sm.GetService('target').IsTarget(self.itemID):
                sm.GetService('state').SetState(self.itemID, state.activeTarget, 1)
            elif uicore.uilib.Key(uiconst.VK_CONTROL) and uicore.uilib.Key(uiconst.VK_SHIFT):
                sm.GetService('fleet').SendBroadcast_Target(self.itemID)
            self.sr.clicktime = blue.os.GetWallclockTime()
        sm.GetService('menu').TacticalItemClicked(self.itemID)

    def OnDblClick(self, *args):
        pass

    @telemetry.ZONE_METHOD
    def Load_update(self, slimItem, *args):
        if slimItem is None:
            return
        self.stateItemID = slimItem.itemID
        selected, hilited, attacking, hostile, targeting, targeted, activeTarget = sm.GetService('state').GetStates(self.stateItemID, [state.selected,
         state.mouseOver,
         state.threatAttackingMe,
         state.threatTargetsMe,
         state.targeting,
         state.targeted,
         state.activeTarget])
        self.Select(selected)
        self.Hilite(hilited)
        self.Targeted(targeted)
        self.UpdateIconColor(slimItem)
        self.ActiveTarget(activeTarget)
        if not activeTarget:
            self.Targeting(targeting)
            if not targeting:
                targeted, = sm.GetService('state').GetStates(slimItem.itemID, [state.targeted])
                self.Targeted(targeted)
        if self.updateItem:
            self.UpdateFlagAndBackground(slimItem)
            self.Attacking(attacking)
            self.Hostile(not attacking and hostile, attacking)
        else:
            if self.sr.flag:
                self.sr.flag.Close()
                self.sr.flag = None
            if self.sr.bgColor:
                self.sr.bgColor.Close()
                self.sr.bgColor = None
        fleetTag = sm.GetService('fleet').GetTargetTag(slimItem.itemID)
        self.AddFleetTag(fleetTag)
        if slimItem.groupID == const.groupWreck:
            uthread.worker('bracket.WreckEmpty', self.WreckEmpty, slimItem.isEmpty)
        broadcastID, broadcastType, broadcastData = sm.GetService('fleet').GetCurrentFleetBroadcastOnItem(slimItem.itemID)
        if broadcastID is not None:
            uthread.worker('bracket.UpdateFleetBroadcasts', self.UpdateFleetBroadcasts, broadcastID, broadcastType, broadcastData)

    @telemetry.ZONE_METHOD
    def UpdateFleetBroadcasts(self, broadcastID, broadcastType, broadcastData):
        if self.destroyed:
            return
        for typeName in fleetbr.types:
            if broadcastType == getattr(state, 'gb%s' % typeName):
                handler = getattr(self, 'GB%s' % typeName, None)
                if handler is None:
                    self.FleetBroadcast(True, typeName, broadcastID, *broadcastData)
                else:
                    handler(True, broadcastID, *broadcastData)
                break

    def RefreshBounty(self):
        self.UpdateFlagAndBackground(self.slimItem)

    @telemetry.ZONE_METHOD
    def UpdateFlagAndBackground(self, slimItem, *args):
        if self.destroyed or not self.updateItem:
            return
        try:
            if slimItem.groupID != const.groupAgentsinSpace and (slimItem.ownerID and util.IsNPC(slimItem.ownerID) or slimItem.charID and util.IsNPC(slimItem.charID)):
                if self.sr.flag:
                    self.sr.flag.Close()
                    self.sr.flag = None
                if self.sr.bgColor:
                    self.sr.bgColor.Close()
                    self.sr.bgColor = None
            else:
                stateSvc = sm.GetService('state')
                uiSvc = sm.GetService('ui')
                iconFlag, backgroundFlag = stateSvc.GetIconAndBackgroundFlags(slimItem)
                icon = None
                if self.sr.icon and self.sr.icon.display:
                    icon = self.sr.icon
                if icon and iconFlag and iconFlag != -1:
                    if self.sr.flag is None:
                        self.sr.flag = self.CreateFlagMarker()
                    props = stateSvc.GetStateProps(iconFlag)
                    col = stateSvc.GetStateFlagColor(iconFlag)
                    blink = stateSvc.GetStateBackgroundBlink(iconFlag)
                    self.sr.flag.children[0].color.SetRGB(*props.iconColor)
                    self.sr.flag.children[1].color.SetRGB(*col)
                    if blink:
                        if not self.sr.flag.HasAnimation('opacity'):
                            uicore.animations.FadeTo(self.sr.flag, startVal=0.0, endVal=1.0, duration=0.5, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_WAVE)
                    else:
                        self.sr.flag.StopAnimations()
                        self.sr.flag.opacity = 1.0
                    self.UpdateFlagPositions(icon)
                    if settings.user.overview.Get('useSmallColorTags', 0):
                        iconNum = 0
                    else:
                        iconNum = props.iconIndex + 1
                    self.sr.flag.children[0].rectLeft = iconNum * 10
                    self.sr.flag.state = uiconst.UI_DISABLED
                elif self.sr.flag:
                    self.sr.flag.Close()
                    self.sr.flag = None
                if backgroundFlag and backgroundFlag != -1:
                    r, g, b, a = stateSvc.GetStateBackgroundColor(backgroundFlag)
                    a = a * 0.5
                    if not self.sr.bgColor:
                        self.sr.bgColor = uicls.Fill(name='bgColor', parent=self, state=uiconst.UI_DISABLED, color=(r,
                         g,
                         b,
                         a))
                    else:
                        self.sr.bgColor.SetRGBA(r, g, b, a)
                    blink = stateSvc.GetStateBackgroundBlink(backgroundFlag)
                    if blink:
                        if not self.sr.bgColor.HasAnimation('opacity'):
                            uicore.animations.FadeTo(self.sr.bgColor, startVal=0.0, endVal=a, duration=0.75, loops=uiconst.ANIM_REPEAT, curveType=uiconst.ANIM_WAVE)
                    else:
                        self.sr.bgColor.StopAnimations()
                elif self.sr.bgColor:
                    self.sr.bgColor.Close()
                    self.sr.bgColor = None
        except AttributeError:
            if not self.destroyed:
                raise 

    def UpdateIconColor(self, slimItem):
        if self.destroyed:
            return
        if self.sr.icon is None or not slimItem:
            return
        if self.sr.node and self.sr.node.iconColor is not None:
            iconColor = self.sr.node.iconColor
        else:
            iconColor = bracketUtils.GetIconColor(slimItem)
        self.SetColor(*iconColor)
        if slimItem.groupID in (const.groupWreck, const.groupSpawnContainer) and sm.GetService('wreck').IsViewedWreck(slimItem.itemID):
            self.Viewed(True)

    def UpdateFlagPositions(self, *args, **kwds):
        pass

    def CreateFlagMarker(self):
        flag = uicls.Container(parent=self, name='flag', pos=(0, 0, 10, 10), align=uiconst.TOPLEFT, idx=0)
        icon = uicls.Sprite(parent=flag, name='icon', pos=(0, 0, 10, 10), state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Bracket/flagIcons.png')
        icon.rectWidth = 10
        icon.rectHeight = 10
        uicls.Fill(parent=flag)
        return flag

    def OnStateChange(self, itemID, flag, status, *args):
        if self.stateItemID != itemID:
            return
        if flag == state.mouseOver:
            self.Hilite(status)
        elif flag == state.selected:
            self.Select(status)
        elif flag == state.targeted:
            self.Targeted(status)
        elif flag == state.targeting:
            self.Targeting(status)
        elif flag == state.activeTarget:
            self.ActiveTarget(status)
        elif flag == state.flagWreckAlreadyOpened:
            self.Viewed(status)
        elif flag == state.flagWreckEmpty:
            self.WreckEmpty(status)
        else:
            for name in fleetbr.types:
                if flag == getattr(state, 'gb%s' % name):
                    handler = getattr(self, 'GB%s' % name, None)
                    if handler is None:
                        self.FleetBroadcast(status, name, *args)
                    else:
                        handler(status, *args)
                    break

    def SetColor(self, r, g, b, _save = True):
        if _save:
            self._originalIconColor = (r, g, b)
        self.sr.icon.color.SetRGB(r, g, b)

    def Viewed(self, status):
        if not self._originalIconColor:
            color = self.sr.icon.color
            self._originalIconColor = (color.r, color.g, color.b)
        r, g, b = self._originalIconColor
        if status:
            attenuation = 0.55
            self.SetColor(r * attenuation, g * attenuation, b * attenuation, _save=False)
        else:
            self.SetColor(r, g, b, _save=False)

    def WreckEmpty(self, isEmpty):
        if isEmpty:
            wreckIcon = 'ui_38_16_29'
        else:
            wreckIcon = 'ui_38_16_28'
        self.sr.icon.LoadIcon(wreckIcon)
        self.iconNo = wreckIcon

    def AddFleetTag(self, tag):
        self._fleetTag = tag
        self.UpdateFleetTagAndTarget()

    def UpdateFleetTagAndTarget(self):
        tagAndTargetStr = ''
        if self._fleetTargetNo:
            tagAndTargetStr += unicode(self._fleetTargetNo)
        if self._fleetTag:
            if tagAndTargetStr:
                tagAndTargetStr += ' / '
            tagAndTargetStr += unicode(self._fleetTag)
        if tagAndTargetStr:
            if not self.fleetTagAndTarget:
                self.fleetTagAndTarget = BracketLabel(parent=self.parent, name='fleetTagAndTarget', align=uiconst.TOPLEFT, state=uiconst.UI_NORMAL, text=tagAndTargetStr, fontsize=fontConst.EVE_MEDIUM_FONTSIZE, bracket=self, bold=True, idx=0)
            else:
                self.fleetTagAndTarget.text = tagAndTargetStr
        elif self.fleetTagAndTarget:
            self.fleetTagAndTarget.Close()
            self.fleetTagAndTarget = None
        self.UpdateSubItems()

    def GBTarget(self, active, fleetBroadcastID, charID, targetNo = None):
        self.FleetBroadcast(active, 'Target', fleetBroadcastID, charID)
        if active:
            self._fleetTargetNo = targetNo
        else:
            self._fleetTargetNo = None
        self.UpdateFleetTagAndTarget()

    def FleetBroadcast(self, active, broadcastType, fleetBroadcastID, charID):
        if active:
            self.fleetBroadcastSender = charID
            self.fleetBroadcastType = broadcastType
            self.fleetBroadcastID = fleetBroadcastID
            if self.fleetBroadcastIcon:
                self.fleetBroadcastIcon.Close()
                self.fleetBroadcastIcon = None
                self.UpdateSubItems()
            icon = fleetbr.types[broadcastType]['smallIcon']
            if not self.sr.icon and self.stateItemID != eve.session.shipid:
                self.LoadIcon(self.iconNo)
            self.fleetBroadcastIcon = uicls.BracketSubIcon(icon=icon, parent=self.parent, state=uiconst.UI_NORMAL, name='fleetBroadcastIcon', bracket=self, hint=fleetbr.GetBroadcastName(broadcastType), idx=0)
            self.UpdateSubItems()
        elif fleetBroadcastID == getattr(self, 'fleetBroadcastID', None):
            if self.fleetBroadcastIcon:
                self.fleetBroadcastIcon.Close()
                self.fleetBroadcastIcon = None
                self.UpdateSubItems()
            self.fleetBroadcastSender = self.fleetBroadcastType = self.fleetBroadcastID = None

    def _UpdateSubItems(self):
        self.UpdateSubItems()

    def UpdateSubItems(self):
        if self.destroyed:
            return
        bracketRO = self.renderObject
        x, y = bracketRO.displayX, bracketRO.displayY
        bracketLayerWidth = uicore.layer.bracket.renderObject.displayWidth
        bracketLayerHeight = uicore.layer.bracket.renderObject.displayHeight
        labelsXOffset = 0
        if self.fleetBroadcastIcon:
            xb, yb = self.fleetBroadcastIcon.bindings
            if x <= 0:
                xb.offset = (self.width + 2,
                 0,
                 0,
                 0)
                yb.offset = ((self.height - self.fleetBroadcastIcon.height) / 2,
                 0,
                 0,
                 0)
                labelsXOffset = self.fleetBroadcastIcon.width
            elif x + self.width >= bracketLayerWidth:
                xb.offset = (-self.fleetBroadcastIcon.width - 2,
                 0,
                 0,
                 0)
                yb.offset = ((self.height - self.fleetBroadcastIcon.height) / 2,
                 0,
                 0,
                 0)
                labelsXOffset = self.fleetBroadcastIcon.width
            elif self.projectBracket and self.projectBracket.bracket:
                xb.offset = ((self.width - self.fleetBroadcastIcon.width) / 2,
                 0,
                 0,
                 0)
                if y <= 0:
                    yb.offset = (self.fleetBroadcastIcon.height,
                     0,
                     0,
                     0)
                else:
                    yb.offset = (-self.fleetBroadcastIcon.height,
                     0,
                     0,
                     0)
            else:
                yb.offset = ((self.height - self.fleetBroadcastIcon.height) / 2,
                 0,
                 0,
                 0)
                xb.offset = (-self.fleetBroadcastIcon.width - 2,
                 0,
                 0,
                 0)
        if self.label:
            newStr = self.displayName
            if newStr is None:
                self.Close()
                return
            if getattr(self, 'showDistance', 1):
                distance = self.GetDistance()
                if distance:
                    newStr += ' ' + util.FmtDist(distance)
            self.label.text = newStr
        mainLabelsYOffset = 0
        maxLabelWidth = 0
        if self.label:
            maxLabelWidth = max(maxLabelWidth, self.label.textwidth)
        if self.subLabel:
            maxLabelWidth = max(maxLabelWidth, self.subLabel.textwidth)
        if self.fleetTagAndTarget:
            maxLabelWidth = max(maxLabelWidth, self.fleetTagAndTarget.textwidth)
            xb, yb = self.fleetTagAndTarget.bindings
            if x + self.width + LABELMARGIN + maxLabelWidth > bracketLayerWidth:
                xb.offset = (-self.fleetTagAndTarget.textwidth - LABELMARGIN - labelsXOffset,
                 0,
                 0,
                 0)
            else:
                xb.offset = (self.width + LABELMARGIN + labelsXOffset,
                 0,
                 0,
                 0)
            if y <= 0:
                tagLabelYShift = (self.height - self.fleetTagAndTarget.textheight) / 2 + 1
                yb.offset = (tagLabelYShift,
                 0,
                 0,
                 0)
                mainLabelsYOffset = self.fleetTagAndTarget.textheight
            else:
                yb.offset = (-self.fleetTagAndTarget.textheight,
                 0,
                 0,
                 0)
        if self.label:
            xb, yb = self.label.bindings
            mainLabelsYOffset += (self.height - self.label.textheight) / 2 + 1
            yb.offset = (mainLabelsYOffset,
             0,
             0,
             0)
            if x + self.width + LABELMARGIN + maxLabelWidth > bracketLayerWidth:
                xb.offset = (-self.label.textwidth - LABELMARGIN - labelsXOffset,
                 0,
                 0,
                 0)
                if self.subLabel:
                    sxb, syb = self.subLabel.bindings
                    sxb.offset = (-self.subLabel.textwidth - LABELMARGIN - labelsXOffset,
                     0,
                     0,
                     0)
                    syb.offset = (mainLabelsYOffset + self.label.textheight,
                     0,
                     0,
                     0)
            else:
                xb.offset = (self.width + LABELMARGIN + labelsXOffset,
                 0,
                 0,
                 0)
                if self.subLabel:
                    sxb, syb = self.subLabel.bindings
                    sxb.offset = (self.width + LABELMARGIN + labelsXOffset,
                     0,
                     0,
                     0)
                    syb.offset = (mainLabelsYOffset + self.label.textheight,
                     0,
                     0,
                     0)
        if not (self.label or self.subLabel or self.fleetBroadcastIcon or self.fleetTagAndTarget):
            self.subItemsUpdateTimer = None
        elif not getattr(self, 'subItemsUpdateTimer', None):
            self.subItemsUpdateTimer = base.AutoTimer(500, self._UpdateSubItems)

    def ActiveTarget(self, activestate):
        for each in self.children[:]:
            if each.name == 'activetarget':
                each.Close()

        if activestate:
            activeTarget = self.GetActiveTargetUI()
        else:
            targeted, = sm.GetService('state').GetStates(self.stateItemID, [state.targeted])
            self.Targeted(targeted, 0)

    def Targeted(self, state, tryActivate = 1):
        obs = sm.GetService('target').IsObserving()
        if obs:
            return
        if state:
            if not self.sr.targetItem:
                targ = self.GetTargetedUI()
                lines = targ.lines
                if not settings.user.ui.Get('targetCrosshair', 1):
                    lines.display = False
                else:
                    lines.display = True
                    bracketUtils.FixLines(targ)
                self.sr.targetItem = targ
            circle = self.sr.targetItem.circle
            if circle is not None and not circle.destroyed:
                circle.state = uiconst.UI_DISABLED
            if tryActivate:
                self.ActiveTarget(0)
            t = self.sr.targetItem
            self.sr.targetItem = None
            if t is not None:
                t.Close()

    def Targeting(self, state):
        if state:
            if self.sr.targetItem is None or self.sr.targetItem.destroyed:
                self.Targeted(1)
            if self.sr.targetItem:
                uthread.new(self.CountDown, self.sr.targetItem)
                self.sr.targetItem.ShowTargetingIndicators()
        elif self.sr.targetItem:
            self.sr.targetItem.HideTargetingIndicators()

    def CountDown(self, *args):
        pass

    def GetActiveTargetUI(self):
        return uicls.Sprite(parent=self, name='activetarget', pos=(0, 0, 18, 18), state=uiconst.UI_PICKCHILDREN, texturePath='res:/UI/Texture/classes/Bracket/activeTarget.png', color=(1.0, 1.0, 1.0, 0.6), align=uiconst.CENTERLEFT)

    def UpdateStructureState(self, slimItem):
        if not util.IsStructure(slimItem.categoryID):
            return
        self.lastPosEvent = blue.os.GetWallclockTime()
        stateName, stateTimestamp, stateDelay = sm.GetService('pwn').GetStructureState(slimItem)
        if self.sr.posStatus is None:
            self.sr.posStatus = uicls.EveLabelSmall(text=entities.POS_STRUCTURE_STATE[stateName], parent=self, left=24, top=30, state=uiconst.UI_NORMAL)
        else:
            self.sr.posStatus.text = entities.POS_STRUCTURE_STATE[stateName]
        if stateName in ('anchoring', 'onlining', 'unanchoring', 'reinforced', 'operating', 'incapacitated'):
            uthread.new(self.StructureProgress, self.lastPosEvent, stateName, stateTimestamp, stateDelay)

    def UpdateOrbitalState(self, slimItem):
        if not util.IsOrbital(slimItem.categoryID):
            return
        self.lastOrbitalEvent = blue.os.GetWallclockTime()
        if slimItem.orbitalState in (entities.STATE_ANCHORING, entities.STATE_ONLINING, entities.STATE_SHIELD_REINFORCE) or slimItem.groupID == const.groupOrbitalConstructionPlatforms:
            statusString = GetEntityStateString(slimItem.orbitalState)
            if self.sr.orbitalStatus is None:
                self.sr.orbitalStatus = uicls.EveLabelSmall(text=statusString, parent=self, left=24, top=30, state=uiconst.UI_NORMAL)
            else:
                self.sr.orbitalStatus.text = statusString
        if slimItem.orbitalState in (entities.STATE_UNANCHORED, entities.STATE_IDLE, entities.STATE_ANCHORED) and slimItem.groupID != const.groupOrbitalConstructionPlatforms:
            if self.sr.orbitalStatus is not None:
                self.sr.orbitalStatus.Close()
                self.sr.orbitalStatus = None
        if slimItem.orbitalHackerID is not None:
            if self.sr.orbitalHack is None:
                self.sr.orbitalHack = uicls.HackingNumberGrid(parent=self, width=140, height=140, numCellRows=7, cellsPerRow=7, cellHeight=20, cellWidth=20, align=uiconst.CENTERTOP, top=-150)
                self.sr.orbitalHack.BeginColorCycling()
            progress = 0.0 if slimItem.orbitalHackerProgress is None else slimItem.orbitalHackerProgress
            self.sr.orbitalHack.SetProgress(progress)
        elif self.sr.orbitalHack is not None:
            self.sr.orbitalHack.StopColorCycling()
            self.children.remove(self.sr.orbitalHack)
            self.sr.orbitalHack = None
        if slimItem.orbitalState in (entities.STATE_ONLINING,
         entities.STATE_OFFLINING,
         entities.STATE_ANCHORING,
         entities.STATE_UNANCHORING,
         entities.STATE_SHIELD_REINFORCE):
            uthread.new(self.OrbitalProgress, self.lastOrbitalEvent, slimItem)

    def UpdateOutpostState(self, slimItem, oldSlimItem = None):
        if slimItem.groupID == const.groupStation and hasattr(slimItem, 'structureState') and slimItem.structureState in [pos.STRUCTURE_SHIELD_REINFORCE, pos.STRUCTURE_ARMOR_REINFORCE]:
            endTime = slimItem.startTimestamp + slimItem.delayTime * const.MSEC
            if getattr(self, 'reinforcedProgressThreadRunning', False) == False:
                uthread.new(self.ReinforcedProgress, slimItem.startTimestamp, endTime)
        elif slimItem.groupID == const.groupStation and hasattr(slimItem, 'structureState') and slimItem.structureState == pos.STRUCTURE_INVULNERABLE:
            if not hasattr(self, 'reinforcedTimeText'):
                self.reinforcedTimeText = uicls.EveLabelSmall(text=' ', parent=self, left=-10, top=32, lineSpacing=0.2, state=uiconst.UI_NORMAL)
            timeText = self.reinforcedTimeText
            timeText.text = localization.GetByLabel('UI/Inflight/Brackets/OutpostInvulnerable')
            timeText.left = -32
            self.ChangeReinforcedState(uiconst.UI_NORMAL)
        else:
            if oldSlimItem is not None and getattr(oldSlimItem, 'structureState', None) in [pos.STRUCTURE_SHIELD_REINFORCE, pos.STRUCTURE_ARMOR_REINFORCE] and getattr(slimItem, 'structureState', None) not in [pos.STRUCTURE_SHIELD_REINFORCE, pos.STRUCTURE_ARMOR_REINFORCE]:
                self.reinforcedProgressThreadRunning = False
            self.ChangeReinforcedState(uiconst.UI_HIDDEN)
            self.ChangeReinforcedState(uiconst.UI_HIDDEN)

    def UpdatePlanetaryLaunchContainer(self, slimItem):
        uthread.new(self._UpdatePlanetaryLaunchContainer, slimItem)

    def _UpdatePlanetaryLaunchContainer(self, slimItem):
        if slimItem.typeID != const.typePlanetaryLaunchContainer:
            return
        cnt = 0
        while slimItem.launchTime is None and cnt < 90:
            blue.pyos.synchro.SleepWallclock(1000)
            cnt += 1

        if getattr(self, 'planetaryLaunchContainerThreadRunning', False) == False and slimItem.launchTime is not None:
            uthread.new(self.PlanetaryLaunchContainerProgress, slimItem.launchTime, long(slimItem.launchTime + const.piLaunchOrbitDecayTime))

    def PlanetaryLaunchContainerProgress(self, startTime, endTime):
        self.planetaryLaunchContainerThreadRunning = True
        try:
            boxwidth = 82
            fillwidth = boxwidth - 2
            boxheight = 14
            fillheight = boxheight - 2
            boxtop = 30
            filltop = boxtop + 1
            boxleft = -(boxwidth / 2) + 5
            fillleft = boxleft + 1
            boxcolor = (1.0, 1.0, 1.0, 0.35)
            fillcolor = (1.0, 1.0, 1.0, 0.25)
            if not hasattr(self, 'reinforcedState'):
                self.burnupFill = uicls.Fill(parent=self, align=uiconst.RELATIVE, width=fillwidth, height=fillheight, left=fillleft, top=filltop, color=fillcolor)
            burnupFill = self.burnupFill
            if not hasattr(self, 'burnupTimeText'):
                self.burnupTimeText = uicls.EveLabelSmall(text=' ', parent=self, left=-10, top=32, lineSpacing=0.2, state=uiconst.UI_NORMAL)
            timeText = self.burnupTimeText
            if not hasattr(self, 'burnupFrame'):
                self.burnupFrame = uicls.Frame(parent=self, align=uiconst.RELATIVE, width=boxwidth, height=boxheight, left=boxleft, top=boxtop, color=boxcolor)
            frame = self.burnupFrame
            while not self.destroyed and self.planetaryLaunchContainerThreadRunning:
                currentTime = blue.os.GetWallclockTime()
                portion = float(currentTime - startTime) / (endTime - startTime)
                if portion > 1.0:
                    break
                width = min(int(portion * fillwidth), fillwidth)
                width = fillwidth - abs(width)
                if burnupFill.width != width:
                    burnupFill.width = width
                newTimeText = util.FmtDate(endTime - currentTime, 'ss')
                if timeText.text != newTimeText:
                    timeText.text = newTimeText
                    timeText.left = -32
                blue.pyos.synchro.SleepWallclock(1000)

        finally:
            self.planetaryLaunchContainerThreadRunning = False

    def ChangeReinforcedState(self, state):
        if hasattr(self, 'reinforcedState'):
            self.reinforcedState.state = state
        if hasattr(self, 'reinforcedTimeText'):
            self.reinforcedTimeText.state = state
        if hasattr(self, 'reinforcedFrame'):
            self.reinforcedFrame.state = state

    def ReinforcedProgress(self, startTime, endTime):
        self.reinforcedProgressThreadRunning = True
        try:
            boxwidth = 82
            fillwidth = boxwidth - 2
            boxheight = 14
            fillheight = boxheight - 2
            boxtop = 30
            filltop = boxtop + 1
            boxleft = -(boxwidth / 2) + 5
            fillleft = boxleft + 1
            boxcolor = (1.0, 1.0, 1.0, 0.35)
            fillcolor = (1.0, 1.0, 1.0, 0.25)
            if not hasattr(self, 'reinforcedState'):
                self.reinforcedState = uicls.Fill(parent=self, align=uiconst.RELATIVE, width=fillwidth, height=fillheight, left=fillleft, top=filltop, color=fillcolor)
            p = self.reinforcedState
            if not hasattr(self, 'reinforcedTimeText'):
                self.reinforcedTimeText = uicls.EveLabelSmall(text=' ', parent=self, left=-10, top=32, lineSpacing=0.2, state=uiconst.UI_NORMAL)
            timeText = self.reinforcedTimeText
            if not hasattr(self, 'reinforcedFrame'):
                self.reinforcedFrame = uicls.Frame(parent=self, align=uiconst.RELATIVE, width=boxwidth, height=boxheight, left=boxleft, top=boxtop, color=boxcolor)
            frame = self.reinforcedFrame
            self.ChangeReinforcedState(uiconst.UI_NORMAL)
            while not self.destroyed and self.reinforcedProgressThreadRunning:
                currentTime = blue.os.GetWallclockTime()
                portion = float(currentTime - startTime) / (endTime - startTime)
                if portion > 1.0:
                    break
                width = min(int(portion * fillwidth), fillwidth)
                width = fillwidth - abs(width)
                if p.width != width:
                    p.width = width
                timeText.text = localization.GetByLabel('UI/Inflight/Brackets/RemainingReinforcedTime', timeRemaining=endTime - currentTime)
                timeText.left = -32
                blue.pyos.synchro.SleepWallclock(1000)

        finally:
            self.reinforcedProgressThreadRunning = False

    def UpdateCaptureProgress(self, captureData):
        slimItem = self.slimItem
        if slimItem.groupID != const.groupCapturePointTower:
            return
        if captureData:
            self.captureData = captureData
        else:
            self.captureData = sm.GetService('bracket').GetCaptureData(self.itemID)
        if not self.captureData:
            return
        if not getattr(self, 'captureTaskletRunning', False):
            uthread.new(self.CaptureProgress)

    def CaptureProgress(self):
        captureID = self.captureData.get('captureID', None)
        if captureID is None:
            return
        self.captureTaskletRunning = True
        boxwidth = 82
        fillwidth = boxwidth - 2
        boxheight = 14
        fillheight = boxheight - 2
        boxtop = 30
        filltop = boxtop + 1
        boxleft = -(boxwidth / 2) + 5
        fillleft = boxleft + 1
        boxcolor = (1.0, 1.0, 1.0, 0.35)
        fillcolor = (1.0, 1.0, 1.0, 0.25)
        frame = uicls.Frame(parent=self, align=uiconst.RELATIVE, width=boxwidth, height=boxheight, left=boxleft, top=boxtop, color=boxcolor)
        if not hasattr(self, 'captureState'):
            self.captureState = uicls.Fill(parent=self, align=uiconst.RELATIVE, width=0, height=fillheight, left=fillleft, top=filltop, color=fillcolor)
        p = self.captureState
        texttop = boxtop + boxheight + 2
        if not hasattr(self, 'captureStateText'):
            self.captureStateText = uicls.EveLabelSmall(text=' ', parent=self, left=boxleft, top=texttop, state=uiconst.UI_NORMAL)
        t = self.captureStateText
        if not hasattr(self, 'captureStateTimeText'):
            self.captureStateTimeText = uicls.EveLabelSmall(text=' ', parent=self, left=-10, top=filltop + 1, state=uiconst.UI_NORMAL)
        timeText = self.captureStateTimeText
        portion = 0.0
        while not self.destroyed and portion < 1.0:
            if self.captureData['captureID'] != 'contested':
                totalTimeMs = self.captureData['captureTime'] * 60 * 1000
                timeDiff = blue.os.TimeDiffInMs(self.captureData['lastIncident'], blue.os.GetSimTime())
                portion = float(timeDiff) / totalTimeMs
                portion = portion + float(self.captureData['points']) / 100
                width = min(int(portion * fillwidth), fillwidth)
                width = abs(width)
                if p.width != width:
                    p.width = width
                capText = localization.GetByLabel('UI/Inflight/Brackets/FacWarCapturing', ownerName=cfg.eveowners.Get(self.captureData['captureID']).name)
                if t.text != capText:
                    t.text = capText
                newTimeText = self.GetCaptureTimeString(portion)
                if timeText.text != newTimeText:
                    timeText.text = newTimeText
                    timeText.left = -8
                if portion < 0.0:
                    self.SetCaptureLogo(self.captureData['lastCapturing'])
                else:
                    self.SetCaptureLogo(self.captureData['captureID'])
            else:
                self.SetCaptureLogo(self.captureData['lastCapturing'])
                portion = float(self.captureData['points']) / 100
                width = min(int(portion * fillwidth), fillwidth)
                width = abs(width)
                if p.width != width:
                    p.width = width
                t.text = localization.GetByLabel('UI/Inflight/Brackets/SystemContested')
                break
            blue.pyos.synchro.SleepWallclock(500)

        if self and not self.destroyed:
            timeText.text = self.GetCaptureTimeString(portion)
            captureID = self.captureData['captureID']
            if captureID != 'contested' and portion >= 1.0:
                t.text = cfg.eveowners.Get(captureID).name
        self.captureTaskletRunning = False

    def GetCaptureTimeString(self, portion):
        if self.captureData['captureID'] == 'contested':
            return ' '
        timeScalar = 1 - portion
        if timeScalar <= 0:
            return localization.GetByLabel('UI/Inflight/Brackets/FacWarCaptured')
        maxTime = self.captureData['captureTime']
        timeLeft = timeScalar * maxTime
        properTime = long(60000L * const.dgmTauConstant * timeLeft)
        return util.FmtDate(properTime, 'ns')

    def SetCaptureLogo(self, teamID):
        if teamID == 'contested' or teamID is None:
            return
        if self.sr.Get('captureLogo'):
            if self.sr.captureLogo.name == cfg.eveowners.Get(teamID).name:
                return
            self.sr.captureLogo.Close()
        raceIDByTeamID = {const.factionCaldariState: const.raceCaldari,
         const.factionMinmatarRepublic: const.raceMinmatar,
         const.factionAmarrEmpire: const.raceAmarr,
         const.factionGallenteFederation: const.raceGallente}
        logo = uicls.LogoIcon(itemID=raceIDByTeamID.get(teamID, teamID), parent=self, state=uiconst.UI_DISABLED, size=32, pos=(-70, 22, 32, 32), name=cfg.eveowners.Get(teamID).name, align=uiconst.RELATIVE, ignoreSize=True)
        self.sr.captureLogo = logo

    def StructureProgress(self, lastPosEvent, stateName, stateTimestamp, stateDelay):
        if self.destroyed:
            return
        t = self.sr.posStatus
        uicls.Frame(parent=self, align=uiconst.RELATIVE, width=82, height=13, left=18, top=30, color=(1.0, 1.0, 1.0, 0.5))
        p = uicls.Fill(parent=self, align=uiconst.RELATIVE, width=80, height=11, left=19, top=31, color=(1.0, 1.0, 1.0, 0.25))
        startTime = blue.os.GetWallclockTime()
        if stateDelay:
            stateDelay = float(stateDelay * const.MSEC)
        doneStr = {'anchoring': localization.GetByLabel('Entities/States/Anchored'),
         'onlining': localization.GetByLabel('Entities/States/Online'),
         'unanchoring': localization.GetByLabel('Entities/States/Unanchored'),
         'reinforced': localization.GetByLabel('Entities/States/Online'),
         'operating': localization.GetByLabel('Entities/States/Operating'),
         'incapacitated': localization.GetByLabel('Entities/States/Incapacitated')}.get(stateName, localization.GetByLabel('Entities/States/Done'))
        endTime = 0
        if stateDelay:
            endTime = stateTimestamp + stateDelay
        while 1 and endTime:
            if not self or self.destroyed or lastPosEvent != self.lastPosEvent:
                return
            timeLeft = endTime - blue.os.GetWallclockTime()
            portion = timeLeft / stateDelay
            timeLeftSec = timeLeft / 1000.0
            if timeLeft <= 0:
                t.text = doneStr
                break
            t.text = localization.GetByLabel('UI/Inflight/Brackets/StructureProgress', stateName=entities.POS_STRUCTURE_STATE[stateName], timeRemaining=long(timeLeft))
            p.width = int(80 * portion)
            blue.pyos.synchro.SleepWallclock(900)

        blue.pyos.synchro.SleepWallclock(250)
        if not self or self.destroyed:
            return
        for each in self.children[-2:]:
            if each is not None and not getattr(each, 'destroyed', 0):
                each.Close()

        if lastPosEvent != self.lastPosEvent:
            return
        t.text = ''
        blue.pyos.synchro.SleepWallclock(250)
        if not self or self.destroyed or lastPosEvent != self.lastPosEvent:
            return
        t.text = doneStr
        blue.pyos.synchro.SleepWallclock(250)
        if not self or self.destroyed or lastPosEvent != self.lastPosEvent:
            return
        t.text = ''
        blue.pyos.synchro.SleepWallclock(250)
        if not self or self.destroyed or lastPosEvent != self.lastPosEvent:
            return
        t.text = doneStr

    def OrbitalProgress(self, lastOrbitalEvent, slimItem):
        if self.destroyed:
            return
        t = self.sr.orbitalStatus
        uicls.Frame(parent=self, align=uiconst.TOPLEFT, width=82, height=13, left=18, top=30, color=(1.0, 1.0, 1.0, 0.5))
        p = uicls.Fill(parent=self, align=uiconst.TOPLEFT, width=80, height=11, left=19, top=31, color=(1.0, 1.0, 1.0, 0.25))
        stateName = GetEntityStateString(slimItem.orbitalState)
        stateTimestamp = slimItem.orbitalTimestamp
        stateDelay = None
        doneText = localization.GetByLabel('Entities/States/Done')
        godmaSM = sm.GetService('godma').GetStateManager()
        if slimItem.orbitalState == entities.STATE_ANCHORING:
            stateDelay = godmaSM.GetType(slimItem.typeID).anchoringDelay
            doneText = GetEntityStateString(entities.STATE_ANCHORED)
        elif slimItem.orbitalState == entities.STATE_ONLINING:
            stateName = localization.GetByLabel('Entities/States/Upgrading')
            stateDelay = godmaSM.GetType(slimItem.typeID).onliningDelay
            doneText = localization.GetByLabel('Entities/States/Online')
        elif slimItem.orbitalState == entities.STATE_UNANCHORING:
            stateDelay = godmaSM.GetType(slimItem.typeID).unanchoringDelay
            doneText = GetEntityStateString(entities.STATE_UNANCHORED)
        elif slimItem.orbitalState == entities.STATE_SHIELD_REINFORCE:
            doneText = GetEntityStateString(entities.STATE_ANCHORED)
        if stateDelay:
            stateDelay = float(stateDelay * const.MSEC)
        else:
            stateDelay = const.DAY
        timeLeft = stateTimestamp - blue.os.GetWallclockTime()
        try:
            while timeLeft > 0:
                blue.pyos.synchro.SleepWallclock(900)
                if not self or self.destroyed or lastOrbitalEvent != self.lastOrbitalEvent:
                    return
                timeLeft = stateTimestamp - blue.os.GetWallclockTime()
                portion = max(0.0, min(1.0, timeLeft / stateDelay))
                t.text = localization.GetByLabel('UI/Inflight/Brackets/StructureProgress', stateName=stateName, timeRemaining=long(timeLeft))
                p.width = int(80 * portion)

            t.text = doneText
            blue.pyos.synchro.SleepWallclock(250)
            if not self or self.destroyed:
                return
        finally:
            if self and not self.destroyed:
                t.text = doneText
                for each in self.children[-2:]:
                    if each is not None and not getattr(each, 'destroyed', 0):
                        each.Close()

        if lastOrbitalEvent != self.lastOrbitalEvent:
            return
        t.text = ''
        blue.pyos.synchro.SleepWallclock(250)
        if not self or self.destroyed or lastOrbitalEvent != self.lastOrbitalEvent:
            return
        t.text = doneText
        blue.pyos.synchro.SleepWallclock(250)
        if not self or self.destroyed or lastOrbitalEvent != self.lastOrbitalEvent:
            return
        t.text = ''
        blue.pyos.synchro.SleepWallclock(250)
        if not self or self.destroyed or lastOrbitalEvent != self.lastOrbitalEvent:
            return
        t.text = doneText

    def SetBracketAnchoredState(self, slimItem):
        if not cfg.invgroups.Get(slimItem.groupID).anchorable:
            return
        if not slimItem or slimItem.itemID == eve.session.shipid or slimItem.ownerID != eve.session.charid and slimItem.ownerID != eve.session.corpid:
            return
        ball = self.ball
        if ball is None:
            bp = sm.GetService('michelle').GetBallpark()
            ball = bp.GetBall(slimItem.itemID)
            if not ball:
                return
        _iconNo, _dockType, _minDist, _maxDist, _iconOffset, _logflag = sm.GetService('bracket').GetBracketProps(slimItem, ball)
        iconNo, dockType, minDist, maxDist, iconOffset, logflag = self.data
        for each in self.children:
            if each.name == 'anchoredicon':
                if ball.isFree:
                    self.data = (iconNo,
                     dockType,
                     _minDist,
                     _maxDist,
                     iconOffset,
                     logflag)
                    each.Close()
                return

        if not ball.isFree:
            self.data = (iconNo,
             dockType,
             0.0,
             1e+32,
             iconOffset,
             logflag)
            uicls.Icon(icon='ui_38_16_15', name='anchoredicon', parent=self, pos=(0, 16, 16, 16), align=uiconst.TOPLEFT)

    def UpdateHackProgress(self, hackProgress):
        if self.sr.orbitalHackLocal is None:
            return
        self.sr.orbitalHackLocal.SetValue(hackProgress)

    def BeginHacking(self):
        if self.sr.orbitalHackLocal is None:
            self.sr.orbitalHackLocal = uicls.HackingProgressBar(parent=self, height=20, width=120, align=uiconst.CENTERBOTTOM, top=-50, color=(0.0, 0.8, 0.0, 1.0), backgroundColor=(0.25, 0.0, 0.0, 1.0))

    def _StopHacking(self):
        blue.pyos.synchro.SleepWallclock(5000)
        if self and self.sr.orbitalHackLocal:
            self.sr.orbitalHackLocal.state = uiconst.UI_HIDDEN
            self.sr.orbitalHackLocal.Close()
            self.sr.orbitalHackLocal = None

    def StopHacking(self, success = False):
        if self.sr.orbitalHackLocal is not None:
            self.sr.orbitalHackLocal.Finalize(complete=success)
            uthread.new(self._StopHacking)


class Bracket(SimpleBracket):
    __guid__ = 'xtriui.Bracket'
    _displayName = None
    _slimItem = None

    def Startup(self, slimItem, ball = None, transform = None):
        self.iconNo, dockType, minDist, maxDist, iconOffset, logflag = self.data
        self.slimItem = slimItem
        self.itemID = slimItem.itemID
        self.groupID = slimItem.groupID
        self.categoryID = slimItem.categoryID
        SimpleBracket.Startup_update(self)
        if not self.invisible:
            self.LoadIcon(self.iconNo)
        self.UpdateStructureState(slimItem)
        self.UpdateCaptureProgress(None)
        self.UpdateOutpostState(slimItem)
        self.UpdatePlanetaryLaunchContainer(slimItem)
        self.SetBracketAnchoredState(slimItem)
        SimpleBracket.Load_update(self, slimItem)

    @apply
    def slimItem():

        def fget(self):
            if self._slimItem:
                return self._slimItem()
            else:
                return None

        def fset(self, value):
            if value is None:
                self._slimItem = None
            else:
                self._slimItem = weakref.ref(value)

        return property(**locals())

    @apply
    def displayName():
        doc = 'Property to dynamically fetch displayName if it hasnt been set'

        def fset(self, value):
            self._displayName = value

        def fget(self):
            if self._displayName:
                return self._displayName
            slimItem = self.slimItem
            if slimItem:
                self._displayName = sm.GetService('bracket').GetDisplayNameForBracket(slimItem)
            return self._displayName

        return property(**locals())

    def GetMenu(self):
        return sm.GetService('menu').CelestialMenu(self.itemID, slimItem=self.slimItem)

    def OnAttribute(self, attributeName, item, newValue):
        self.scanAttributeChangeFlag = True

    def UpdateFlagPositions(self, icon = None):
        if icon is None:
            icon = self.sr.icon
        flag = self.sr.flag
        if icon and flag:
            if settings.user.overview.Get('useSmallColorTags', 0):
                flag.width = flag.height = 5
                flag.left = icon.left + 10
                flag.top = icon.top + 10
            else:
                flag.width = flag.height = 9
                flag.left = icon.left + 9
                flag.top = icon.top + 8

    @telemetry.ZONE_METHOD
    def CountDown(self, target):
        if self.destroyed:
            return
        self.scanAttributeChangeFlag = False
        slimItem = self.slimItem
        source = eve.session.shipid
        time = sm.GetService('bracket').GetScanSpeed(source, slimItem)
        if target:
            par = uicls.Container(parent=target, width=82, height=13, left=36, top=37, align=uiconst.TOPLEFT, state=uiconst.UI_DISABLED)
            t = uicls.EveLabelSmall(text='', parent=par, width=200, left=6, state=uiconst.UI_NORMAL)
            p = uicls.Fill(parent=par, align=uiconst.RELATIVE, width=80, height=11, left=1, top=1, color=(1.0, 1.0, 1.0, 0.25))
            uicls.Frame(parent=par, color=(1.0, 1.0, 1.0, 0.5))
            targetSvc = sm.GetService('target')
            startTime = targetSvc.GetTargetingStartTime(slimItem.itemID)
            if startTime is None:
                return
            lockedText = localization.GetByLabel('UI/Inflight/Brackets/TargetLocked')
            while not self.destroyed:
                now = blue.os.GetSimTime()
                dt = blue.os.TimeDiffInMs(startTime, now)
                if self.scanAttributeChangeFlag:
                    waitRatio = dt / float(time)
                    self.scanAttributeChangeFlag = False
                    time = sm.GetService('bracket').GetScanSpeed(source, slimItem)
                    startTime = now - long(time * waitRatio * 10000)
                    dt = blue.os.TimeDiffInMs(startTime, now)
                if t.destroyed:
                    return
                t.text = localization.GetByLabel('UI/Inflight/Brackets/TargetingCountdownTimer', numSeconds=(time - dt) / 1000.0)
                if dt > time:
                    t.text = lockedText
                    break
                p.width = int(80 * ((time - dt) / time))
                blue.pyos.synchro.Sleep(TARGETTING_UI_UPDATE_RATE)

            blue.pyos.synchro.SleepWallclock(250)
            if t.destroyed:
                return
            t.text = ''
            blue.pyos.synchro.SleepWallclock(250)
            if t.destroyed:
                return
            t.text = lockedText
            blue.pyos.synchro.SleepWallclock(250)
            if t.destroyed:
                return
            t.text = ''
            blue.pyos.synchro.SleepWallclock(250)
            if t.destroyed:
                return
            t.text = lockedText
            blue.pyos.synchro.SleepWallclock(250)
            par.Close()

    def GBEnemySpotted(self, active, fleetBroadcastID, charID):
        self.NearIDFleetBroadcast(active, fleetBroadcastID, charID, 'EnemySpotted')

    def GBNeedBackup(self, active, fleetBroadcastID, charID):
        self.NearIDFleetBroadcast(active, fleetBroadcastID, charID, 'NeedBackup')

    def GBInPosition(self, active, fleetBroadcastID, charID):
        self.NearIDFleetBroadcast(active, fleetBroadcastID, charID, 'InPosition')

    def GBHoldPosition(self, active, fleetBroadcastID, charID):
        self.NearIDFleetBroadcast(active, fleetBroadcastID, charID, 'HoldPosition')

    def NearIDFleetBroadcast(self, active, fleetBroadcastID, charID, broadcastType):
        inBubble = bool(util.SlimItemFromCharID(charID))
        if inBubble:
            return self.FleetBroadcast(active, broadcastType, fleetBroadcastID, charID)
        if not active:
            if fleetBroadcastID == getattr(self, 'fleetBroadcastID', None):
                if self.fleetBroadcastIcon is not None:
                    self.fleetBroadcastIcon.Close()
                    self.fleetBroadcastIcon = None
                    self.UpdateSubItems()
                self.fleetBroadcastSender = self.fleetBroadcastType = self.fleetBroadcastID = None

    def GetHostileAttackingUI(self):
        threat = uicls.Sprite(parent=self, name='threat', pos=(0, 0, 32, 32), align=uiconst.CENTER, state=uiconst.UI_DISABLED, texturePath='res:/UI/Texture/classes/Bracket/threatBracket.png')
        return threat

    def GetActiveTargetUI(self):
        return uicls.ActiveTargetOnBracket(parent=self)

    def GetTargetedUI(self):
        return uicls.TargetOnBracket(parent=self)

    def GetCanTargetSprite(self, create = True, *args):
        return None

    def AddBinding(self, sourceObject, sourceAttribute, destObject, destAttribute, curveSet):
        binding = trinity.TriValueBinding()
        binding.sourceObject = sourceObject
        binding.sourceAttribute = sourceAttribute
        binding.destinationObject = destObject.GetRenderObject()
        binding.destinationAttribute = destAttribute
        curveSet.bindings.append(binding)
        return binding


exports = util.AutoExports('bracket', locals())