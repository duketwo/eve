#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/ui/primitives/base.py
import uicls
import uiutil
import uiconst
import uthread
import blue
import types
import util
import base
import log
import trinity
import copy
import telemetry
import weakref
import uiconstLoaded
PUSHALIGNMENTS = (uiconst.TOLEFT,
 uiconst.TOTOP,
 uiconst.TORIGHT,
 uiconst.TOBOTTOM,
 uiconst.TOLEFT_PROP,
 uiconst.TOTOP_PROP,
 uiconst.TORIGHT_PROP,
 uiconst.TOBOTTOM_PROP)
AFFECTEDBYPUSHALIGNMENTS = PUSHALIGNMENTS + (uiconst.TOALL,
 uiconst.TOLEFT_NOPUSH,
 uiconst.TOTOP_NOPUSH,
 uiconst.TORIGHT_NOPUSH,
 uiconst.TOBOTTOM_NOPUSH)

class Base(uicls.DragDropObject):
    __guid__ = 'uicls.Base'
    __renderObject__ = None
    __members__ = ['name',
     'left',
     'top',
     'width',
     'height',
     'padLeft',
     'padTop',
     'padRight',
     'padBottom',
     'display',
     'align',
     'pickState',
     'parent',
     'renderObject']
    default_name = None
    default_parent = None
    default_idx = -1
    default_state = uiconst.UI_NORMAL
    default_align = uiconst.TOPLEFT
    default_hint = None
    default_hintDelay = 100
    default_left = 0
    default_top = 0
    default_width = 0
    default_height = 0
    default_padLeft = 0
    default_padTop = 0
    default_padRight = 0
    default_padBottom = 0
    default_cursor = None
    _left = 0
    _top = 0
    _width = 0
    _height = 0
    _align = None
    _display = True
    _sr = None
    _name = default_name
    _cursor = default_cursor
    _parentRef = None
    _alignmentDirty = False
    _consumeFunc = None
    _displayDirty = False
    _displayX = 0
    _displayY = 0
    _displayWidth = 0
    _displayHeight = 0
    _attachedObjects = None
    _attachedTo = None
    _animationCurves = None
    _pickState = uiconst.TR2_SPS_ON
    destroyed = False
    renderObject = None
    auxiliaryHint = None

    def __init__(self, **kw):
        if self.default_name is None:
            self.default_name = self.__class__.__name__
        if self.__renderObject__:
            self.renderObject = RO = self.__renderObject__()
            uicore.uilib.RegisterObject(self, RO)
            RO.display = True
        attributesBunch = uiutil.Bunch(kw)
        self.ApplyAttributes(attributesBunch)
        if self.PostApplyAttributes.im_func != Base.PostApplyAttributes.im_func:
            self.PostApplyAttributes(attributesBunch)
        if hasattr(self, 'init'):
            self.init()

    def __repr__(self):
        if self.name:
            name = self.name.encode('utf8')
        else:
            name = 'None'
        return '%s object at %s, name=%s, destroyed=%s>' % (self.__guid__,
         hex(id(self)),
         name,
         self.destroyed)

    def ApplyAttributes(self, attributes):
        self.name = attributes.get('name', self.default_name)
        self.align = attributes.get('align', self.default_align)
        self.hint = attributes.get('hint', self.default_hint)
        self.hintDelay = attributes.get('hintDelay', self.default_hintDelay)
        self._cursor = attributes.get('cursor', self.default_cursor)
        if 'pos' in attributes and attributes.pos is not None:
            self.pos = attributes.pos
        else:
            left = attributes.get('left', self.default_left)
            top = attributes.get('top', self.default_top)
            width = attributes.get('width', self.default_width)
            height = attributes.get('height', self.default_height)
            self.pos = (left,
             top,
             width,
             height)
        if 'padding' in attributes and attributes.padding is not None:
            self.padding = attributes.padding
        else:
            padLeft = attributes.get('padLeft', self.default_padLeft)
            padTop = attributes.get('padTop', self.default_padTop)
            padRight = attributes.get('padRight', self.default_padRight)
            padBottom = attributes.get('padBottom', self.default_padBottom)
            self.padding = (padLeft,
             padTop,
             padRight,
             padBottom)
        self.SetState(attributes.get('state', self.default_state))
        if attributes.get('bgParent', None):
            idx = attributes.get('idx', self.default_idx)
            if idx is None:
                idx = -1
            attributes.bgParent.background.insert(idx, self)
        else:
            self.SetParent(attributes.get('parent', self.default_parent), attributes.get('idx', self.default_idx))

    def Close(self):
        if getattr(self, 'destroyed', False):
            return
        self.destroyed = True
        uicore.uilib.ReleaseObject(self)
        notifyevents = getattr(self, '__notifyevents__', None)
        if notifyevents:
            sm.UnregisterNotify(self)
        attachedTo = getattr(self, '_attachedTo', None)
        if attachedTo:
            object = attachedTo[0]
            object._RemoveAttachment(self)
        if self._OnClose.im_func != Base._OnClose.im_func:
            self._OnClose()
        parent = self.GetParent()
        if parent and not parent._containerClosing:
            parent.children.remove(self)
        if self._animationCurves:
            self.StopAnimations()
        self.renderObject = None
        self._alignFunc = None
        self._consumeFunc = None

    def _GetLegacyDeadAttr(self):
        log.LogTraceback('UIObject.dead attribute is deprecated, use UIObject.destroyed')
        return self.destroyed

    dead = property(_GetLegacyDeadAttr)

    def _GetSR(self):
        if self._sr is None:
            self._sr = uiutil.Bunch()
        return self._sr

    sr = property(_GetSR)

    def HasEventHandler(self, handlerName):
        handlerArgs, handler = self.FindEventHandler(handlerName)
        if not handler:
            return False
        baseHandler = getattr(uicls.Base, handlerName, None)
        if baseHandler and getattr(handler, 'im_func', None) is baseHandler.im_func:
            return False
        return bool(handler)

    def FindEventHandler(self, handlerName):
        handler = getattr(self, handlerName, None)
        if not handler:
            return (None, None)
        if type(handler) == types.TupleType:
            handlerArgs = handler[1:]
            handler = handler[0]
        else:
            handlerArgs = ()
        return (handlerArgs, handler)

    def StopAnimations(self):
        if self._animationCurves:
            for curveSet in self._animationCurves.values():
                curveSet.Stop()

        self._animationCurves = None

    def HasAnimation(self, attrName):
        if self._animationCurves:
            return attrName in self._animationCurves
        return False

    def AttachAnimationCurveSet(self, curveSet, attrName):
        if self._animationCurves is None:
            self._animationCurves = {}
        else:
            currCurveSet = self._animationCurves.get(attrName, None)
            if currCurveSet:
                currCurveSet.Stop()
        self._animationCurves[attrName] = curveSet

    def ProcessEvent(self, eventID):
        uicore.uilib._TryExecuteHandler(eventID, self)

    def GetRenderObject(self):
        return self.renderObject

    def PostApplyAttributes(self, attributes):
        pass

    def SetParent(self, parent, idx = None):
        currentParent = self.GetParent()
        if currentParent:
            currentParent.FlagNextChildrenDirty(self)
            currentParent.children.remove(self)
            currentParent.FlagAlignmentDirty()
        if parent is not None:
            if idx is None:
                idx = -1
            parent.children.insert(idx, self)
            parent.FlagAlignmentDirty()
            self.FlagAlignmentDirty()
            parent.FlagNextChildrenDirty(self)

    def GetParent(self):
        if self._parentRef:
            return self._parentRef()

    parent = property(GetParent)

    def SetOrder(self, idx):
        parent = self.GetParent()
        if parent:
            currentIndex = parent.children.index(self)
            if currentIndex != idx:
                self.SetParent(parent, idx)
        self.FlagAlignmentDirty()
        parent.FlagNextChildrenDirty(self)

    @apply
    def pos():
        doc = 'Position of UI element'

        def fget(self):
            return (self._left,
             self._top,
             self._width,
             self._height)

        def fset(self, value):
            left, top, width, height = value
            if left < 1.0:
                adjustedLeft = left
            else:
                adjustedLeft = int(round(left))
            if top < 1.0:
                adjustedTop = top
            else:
                adjustedTop = int(round(top))
            if width < 1.0:
                adjustedWidth = width
            else:
                adjustedWidth = int(round(width))
            if height < 1.0:
                adjustedHeight = height
            else:
                adjustedHeight = int(round(height))
            self._left = adjustedLeft
            self._top = adjustedTop
            self._width = adjustedWidth
            self._height = adjustedHeight
            if self.parent:
                self.parent.FlagNextChildrenDirty(self)
            self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def left():
        doc = 'x-coordinate of UI element'

        def fget(self):
            return self._left

        def fset(self, value):
            if value < 1.0:
                adjustedValue = value
            else:
                adjustedValue = int(round(value))
            if adjustedValue != self._left:
                self._left = adjustedValue
                if self.parent:
                    self.parent.FlagNextChildrenDirty(self)
                self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def top():
        doc = 'y-coordinate of UI element'

        def fget(self):
            return self._top

        def fset(self, value):
            if value < 1.0:
                adjustedValue = value
            else:
                adjustedValue = int(round(value))
            if adjustedValue != self._top:
                self._top = adjustedValue
                if self.parent:
                    self.parent.FlagNextChildrenDirty(self)
                self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def width():
        doc = 'Width of UI element'

        def fget(self):
            return self._width

        def fset(self, value):
            if value < 1.0:
                adjustedValue = value
            else:
                adjustedValue = int(round(value))
            if adjustedValue != self._width:
                self._width = adjustedValue
                self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def height():
        doc = 'Height of UI element'

        def fget(self):
            return self._height

        def fset(self, value):
            if value < 1.0:
                adjustedValue = value
            else:
                adjustedValue = int(round(value))
            if adjustedValue != self._height:
                self._height = adjustedValue
                self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def padding():
        doc = '\n        Padding as a tuple of four values (left, top, right, bottom).\n        It can also be assigned an integer value - all four items will\n        then receive the same value.\n        '

        def fget(self):
            return (self._padLeft,
             self._padTop,
             self._padRight,
             self._padBottom)

        def fset(self, value):
            if isinstance(value, (tuple, list)):
                padLeft, padTop, padRight, padBottom = value
            else:
                padLeft = padTop = padRight = padBottom = value
            self._padLeft = padLeft
            self._padTop = padTop
            self._padRight = padRight
            self._padBottom = padBottom
            if self.parent:
                self.parent.FlagNextChildrenDirty(self)
            self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def padLeft():
        doc = 'Left padding'

        def fget(self):
            return self._padLeft

        def fset(self, value):
            self._padLeft = value
            if self.parent:
                self.parent.FlagNextChildrenDirty(self)
            self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def padRight():
        doc = 'Right padding'

        def fget(self):
            return self._padRight

        def fset(self, value):
            self._padRight = value
            if self.parent:
                self.parent.FlagNextChildrenDirty(self)
            self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def padTop():
        doc = 'Top padding'

        def fget(self):
            return self._padTop

        def fset(self, value):
            self._padTop = value
            if self.parent:
                self.parent.FlagNextChildrenDirty(self)
            self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def padBottom():
        doc = 'Bottom padding'

        def fget(self):
            return self._padBottom

        def fset(self, value):
            self._padBottom = value
            if self.parent:
                self.parent.FlagNextChildrenDirty(self)
            self.FlagAlignmentDirty()

        return property(**locals())

    @apply
    def display():
        doc = 'Is UI element displayed?'

        def fget(self):
            return self._display

        def fset(self, value):
            if value != self._display:
                self._display = value
                ro = self.renderObject
                if ro:
                    ro.display = value
                self._alignmentDirty = False
                if self.parent:
                    self.parent.FlagNextChildrenDirty(self)
                self.FlagAlignmentDirty()
                self._displayDirty = True

        return property(**locals())

    def SetAlign(self, align):
        if align == self._align:
            return
        if hasattr(self.renderObject, 'absoluteCoordinates'):
            if align == uiconst.ABSOLUTE:
                self.renderObject.absoluteCoordinates = True
            else:
                self.renderObject.absoluteCoordinates = False
        self._align = align
        self._alignFunc, self._consumeFunc = ALIGN_AND_CONSUME_FUNCTIONS[align]
        self.FlagAlignmentDirty()
        if self.parent:
            self.parent.FlagNextChildrenDirty(self)

    def GetAlign(self):
        return self._align

    align = property(GetAlign, SetAlign)

    @apply
    def name():
        doc = 'Name of this UI element'

        def fget(self):
            return self._name

        def fset(self, value):
            self._name = value
            ro = self.renderObject
            if ro:
                ro.name = self._name

        return property(**locals())

    @apply
    def translation():
        doc = '\n            Translation is a tuple of (displayX,displayY). Prefer this over setting\n            x and y separately.\n            '

        def fget(self):
            return (self._displayX, self._displayY)

        def fset(self, value):
            self._displayX = value[0]
            self._displayY = value[1]
            ro = self.renderObject
            if ro:
                ro.displayX = self._displayX
                ro.displayY = self._displayY

        return property(**locals())

    @apply
    def displayRect():
        doc = '\n            displayRect is a tuple of (displayX,displayY,displayWidth,displayHeight).\n            Prefer this over setting x, y, width and height separately if all are\n            being set.\n            '

        def fget(self):
            return (self._displayX,
             self._displayY,
             self._displayWidth,
             self._displayHeight)

        def fset(self, value):
            displayX, displayY, displayWidth, displayHeight = value
            self._displayX = int(round(displayX))
            self._displayY = int(round(displayY))
            self._displayWidth = int(round(displayX + displayWidth)) - self._displayX
            self._displayHeight = int(round(displayY + displayHeight)) - self._displayY
            if self._displayWidth == 0 and round(displayWidth) > 0:
                self._displayWidth = 1
            if self._displayHeight == 0 and round(displayHeight) > 0:
                self._displayHeight = 1
            ro = self.renderObject
            if ro:
                ro.displayX = self._displayX
                ro.displayY = self._displayY
                ro.displayWidth = self._displayWidth
                ro.displayHeight = self._displayHeight

        return property(**locals())

    @apply
    def displayX():
        doc = 'x-coordinate of render object'

        def fget(self):
            return self._displayX

        def fset(self, value):
            self._displayX = int(round(value))
            ro = self.renderObject
            if ro:
                ro.displayX = self._displayX

        return property(**locals())

    @apply
    def displayY():
        doc = 'y-coordinate of render object'

        def fget(self):
            return self._displayY

        def fset(self, value):
            self._displayY = int(round(value))
            ro = self.renderObject
            if ro:
                ro.displayY = self._displayY

        return property(**locals())

    @apply
    def displayWidth():
        doc = 'Width of render object'

        def fget(self):
            return self._displayWidth

        def fset(self, value):
            self._displayWidth = int(round(value))
            ro = self.renderObject
            if ro:
                ro.displayWidth = self._displayWidth

        return property(**locals())

    @apply
    def displayHeight():
        doc = 'Height of render object'

        def fget(self):
            return self._displayHeight

        def fset(self, value):
            self._displayHeight = int(round(value))
            ro = self.renderObject
            if ro:
                ro.displayHeight = self._displayHeight

        return property(**locals())

    @apply
    def pickState():
        doc = 'Pick state of render object'

        def fget(self):
            return self._pickState

        def fset(self, value):
            self._pickState = value
            ro = self.renderObject
            if ro:
                ro.pickState = value

        return property(**locals())

    def Disable(self, *args):
        self.pickState = uiconst.TR2_SPS_OFF

    def Enable(self, *args):
        self.pickState = uiconst.TR2_SPS_ON

    def SetFocus(self, *args):
        pass

    def SendMessage(self, *args, **kwds):
        pass

    def SetHint(self, hint):
        self.hint = hint or ''

    def GetHint(self):
        return getattr(self, 'hint', None)

    def SetDisplayRect(self, displayRect):
        align = self.GetAlign()
        if align != uiconst.NOALIGN:
            return
        self.displayRect = displayRect

    def SetPadding(self, *padding):
        log.LogTraceback('UIObject.SetPadding is deprecated, use UIObject.padding instead')
        try:
            self.padding = padding
        except:
            pass

    def SetPosition(self, left, top):
        self.left = left
        self.top = top

    def GetPosition(self):
        return (self.left, self.top)

    def IsClippedBy(self, clipper = None):
        if self.GetAbsoluteTop() > clipper.GetAbsoluteBottom():
            return True
        if self.GetAbsoluteBottom() < clipper.GetAbsoluteTop():
            return True
        if self.GetAbsoluteRight() < clipper.GetAbsoluteLeft():
            return True
        if self.GetAbsoluteLeft() > clipper.GetAbsoluteLeft():
            return True
        return False

    def SetSize(self, width, height):
        self.width = width
        self.height = height

    def GetSize(self):
        return (self.width, self.height)

    def GetAbsoluteViewportPosition(self):
        if self.destroyed or not self.display:
            return (0, 0)
        if self._alignmentDirty or self._displayDirty:
            parent = self.parent
            if parent:
                prevParent = None
                while parent and parent.display:
                    prevParent = parent
                    parent = parent.parent

                parent = parent or prevParent
                parent.UpdateAlignmentAsRoot()
        if self.renderObject:
            l, t = self.renderObject.displayX, self.renderObject.displayY
        else:
            l, t = self.displayX, self.displayY
        if self.align in (uiconst.ABSOLUTE, uiconst.NOALIGN):
            return (uicore.ReverseScaleDpi(l), uicore.ReverseScaleDpi(t))
        parent = self.GetParent()
        while parent and not parent.destroyed:
            if type(parent.renderObject) == trinity.Tr2Sprite2dLayer:
                break
            l += parent.renderObject.displayX
            t += parent.renderObject.displayY
            if parent.align in (uiconst.ABSOLUTE, uiconst.NOALIGN):
                break
            parent = parent.GetParent()

        return (uicore.ReverseScaleDpi(l), uicore.ReverseScaleDpi(t))

    def GetAbsoluteViewport(self, doPrint = False):
        if not self.display:
            return (0, 0, 0, 0)
        w, h = self.GetAbsoluteSize()
        l, t = self.GetAbsoluteViewportPosition()
        return (l,
         t,
         w,
         h)

    def GetAbsolute(self, doPrint = False):
        if not self.display:
            return (0, 0, 0, 0)
        w, h = self.GetAbsoluteSize()
        l, t = self.GetAbsolutePosition()
        return (l,
         t,
         w,
         h)

    @telemetry.ZONE_METHOD
    def GetAbsoluteSize(self):
        if self.destroyed or not self.display:
            return (0, 0)
        elif self.align in AFFECTEDBYPUSHALIGNMENTS:
            if self._alignmentDirty or self._displayDirty:
                parent = self.parent
                if parent:
                    prevParent = None
                    while parent and parent.display:
                        prevParent = parent
                        parent = parent.parent

                    parent = parent or prevParent
                    parent.UpdateAlignmentAsRoot()
            return (uicore.ReverseScaleDpi(self.displayWidth), uicore.ReverseScaleDpi(self.displayHeight))
        else:
            return (self.width, self.height)

    def GetCurrentAbsoluteSize(self):
        if self.destroyed or not self.display:
            return (0, 0)
        elif self.align in AFFECTEDBYPUSHALIGNMENTS:
            return (uicore.ReverseScaleDpi(self.displayWidth), uicore.ReverseScaleDpi(self.displayHeight))
        else:
            return (self.width, self.height)

    @telemetry.ZONE_METHOD
    def GetAbsolutePosition(self):
        if self.destroyed or not self.display:
            return (0, 0)
        if self._alignmentDirty or self._displayDirty:
            parent = self.parent
            if parent:
                prevParent = None
                while parent and parent.display:
                    prevParent = parent
                    parent = parent.parent

                parent = parent or prevParent
                parent.UpdateAlignmentAsRoot()
        if self.renderObject:
            l, t = self.renderObject.displayX, self.renderObject.displayY
        else:
            l, t = self.displayX, self.displayY
        if self.align in (uiconst.ABSOLUTE, uiconst.NOALIGN):
            return (uicore.ReverseScaleDpi(l), uicore.ReverseScaleDpi(t))
        parent = self.GetParent()
        while parent and not parent.destroyed:
            l += parent.renderObject.displayX
            t += parent.renderObject.displayY
            if parent.align in (uiconst.ABSOLUTE, uiconst.NOALIGN):
                break
            parent = parent.GetParent()

        return (uicore.ReverseScaleDpi(l), uicore.ReverseScaleDpi(t))

    def GetAbsoluteLeft(self):
        l, t = self.GetAbsolutePosition()
        return l

    absoluteLeft = property(GetAbsoluteLeft)

    def GetAbsoluteTop(self):
        l, t = self.GetAbsolutePosition()
        return t

    absoluteTop = property(GetAbsoluteTop)

    def GetAbsoluteBottom(self):
        l, t = self.GetAbsolutePosition()
        w, h = self.GetAbsoluteSize()
        return t + h

    absoluteBottom = property(GetAbsoluteBottom)

    def GetAbsoluteRight(self):
        l, t = self.GetAbsolutePosition()
        w, h = self.GetAbsoluteSize()
        return l + w

    absoluteRight = property(GetAbsoluteRight)

    def SetState(self, state):
        if state == uiconst.UI_NORMAL:
            self.display = True
            self.pickState = uiconst.TR2_SPS_ON
        elif state == uiconst.UI_DISABLED:
            self.display = True
            self.pickState = uiconst.TR2_SPS_OFF
        elif state == uiconst.UI_HIDDEN:
            self.display = False
        elif state == uiconst.UI_PICKCHILDREN:
            self.display = True
            self.pickState = uiconst.TR2_SPS_CHILDREN

    def GetState(self):
        if not self.display:
            return uiconst.UI_HIDDEN
        if self.pickState == uiconst.TR2_SPS_CHILDREN:
            return uiconst.UI_PICKCHILDREN
        if self.pickState == uiconst.TR2_SPS_ON:
            return uiconst.UI_NORMAL
        if self.pickState == uiconst.TR2_SPS_OFF:
            return uiconst.UI_DISABLED

    state = property(GetState, SetState)

    def _RemoveAttachment(self, attachment):
        attachedObjects = self._attachedObjects
        if attachedObjects and attachment in attachedObjects:
            attachedObjects.remove(attachment)

    def _AddAttachment(self, attachment):
        if self._attachedObjects is None:
            self._attachedObjects = []
        attachedObjects = self._attachedObjects
        if attachment not in attachedObjects:
            attachedObjects.append(attachment)
            self.UpdateAttachments()

    def ClearAttachTo(self):
        if self._attachedTo:
            self.SetAlign(uiconst.TOPLEFT)
            oldObject = self._attachedTo[0]
            oldObject._RemoveAttachment(self)
            self._attachedTo = None

    def GetMyAttachments(self):
        return self._attachedObjects

    def SetAttachTo(self, toObject, objectPoint, myPoint, offset = None):
        if self._attachedTo:
            oldObject = self._attachedTo[0]
            oldObject._RemoveAttachment(self)
            self._attachedTo = None
        toParent = toObject.GetParent()
        parent = self.GetParent()
        if toParent != parent:
            raise RuntimeError, 'SetAttachTo: toObject has to be on same level as the attachment'
        self.SetAlign(uiconst.ATTACHED)
        self._attachedTo = (toObject,
         objectPoint,
         myPoint,
         offset)
        toObject._AddAttachment(self)

    def FlagAlignmentDirty(self):
        if self._alignmentDirty:
            return
        self._alignmentDirty = True
        if self.align == uiconst.NOALIGN:
            uicore.uilib.alignIslands.append(self)
            return
        parent = self.parent
        if parent:
            parent.FlagHasDirtyChildren()

    def ConsumeBudget(self, budget):
        consumeFunc = self._consumeFunc
        if consumeFunc:
            return consumeFunc(self, budget)
        else:
            return budget

    @telemetry.ZONE_METHOD
    def ConsumeBudgetToLeftAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        widthUsed = uicore.ScaleDpiF(self._padLeft + self._width + self._left + self._padRight)
        budgetLeft += widthUsed
        budgetWidth -= widthUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def ConsumeBudgetToRightAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        widthUsed = uicore.ScaleDpiF(self._padLeft + self._width + self._padRight + self._left)
        budgetWidth -= widthUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def ConsumeBudgetToTopAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        heightUsed = uicore.ScaleDpiF(self._padTop + self._height + self._top + self._padBottom)
        budgetTop += heightUsed
        budgetHeight -= heightUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def ConsumeBudgetToBottomAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        heightUsed = uicore.ScaleDpiF(self._padTop + self._height + self._top + self._padBottom)
        budgetHeight -= heightUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def ConsumeBudgetToLeftProportionalAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        widthUsed = uicore.ScaleDpiF(self._padLeft + self._left + self._padRight) + self.displayWidth
        budgetLeft += widthUsed
        budgetWidth -= widthUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def ConsumeBudgetToRightProportionalAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        widthUsed = uicore.ScaleDpiF(self._padLeft + self._padRight + self._left) + self.displayWidth
        budgetWidth -= widthUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def ConsumeBudgetToTopProportionalAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        heightUsed = uicore.ScaleDpiF(self._padTop + self._top + self._padBottom) + self.displayHeight
        budgetTop += heightUsed
        budgetHeight -= heightUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def ConsumeBudgetToBottomProportionalAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        heightUsed = uicore.ScaleDpiF(self._padTop + self._top + self._padBottom) + self.displayHeight
        budgetHeight -= heightUsed
        return (budgetLeft,
         budgetTop,
         budgetWidth,
         budgetHeight)

    @telemetry.ZONE_METHOD
    def UpdateToLeftAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        displayX = budgetLeft + uicore.ScaleDpiF(self._padLeft + self._left)
        displayY = budgetTop + uicore.ScaleDpiF(self._padTop + self._top)
        displayHeight = budgetHeight - uicore.ScaleDpiF(self._padTop + self._padBottom)
        displayWidth = uicore.ScaleDpiF(self._width)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        if not self.display:
            return budget
        return self.ConsumeBudget(budget)

    @telemetry.ZONE_METHOD
    def UpdateToRightAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        displayX = budgetLeft + budgetWidth - uicore.ScaleDpiF(self._width + self._padRight + self._left)
        displayY = budgetTop + uicore.ScaleDpiF(self._padTop + self._top)
        displayHeight = budgetHeight - uicore.ScaleDpiF(self._padTop + self._padBottom)
        displayWidth = uicore.ScaleDpiF(self._width)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        if not self.display:
            return budget
        return self.ConsumeBudget(budget)

    @telemetry.ZONE_METHOD
    def UpdateToBottomAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        displayX = budgetLeft + uicore.ScaleDpiF(self._padLeft + self._left)
        displayY = budgetTop + budgetHeight - uicore.ScaleDpiF(self._height + self._padBottom + self._top)
        displayWidth = budgetWidth - uicore.ScaleDpiF(self._padLeft + self._padRight)
        displayHeight = uicore.ScaleDpiF(self._height)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        if not self.display:
            return budget
        return self.ConsumeBudget(budget)

    @telemetry.ZONE_METHOD
    def UpdateToTopAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        displayX = budgetLeft + uicore.ScaleDpiF(self._padLeft + self._left)
        displayY = budgetTop + uicore.ScaleDpiF(self._padTop + self._top)
        displayWidth = budgetWidth - uicore.ScaleDpiF(self._padLeft + self._padRight)
        displayHeight = uicore.ScaleDpiF(self._height)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        if not self.display:
            return budget
        return self.ConsumeBudget(budget)

    @telemetry.ZONE_METHOD
    def UpdateToAllAlignment(self, budget):
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        displayX = budgetLeft + uicore.ScaleDpiF(self._padLeft + self._left)
        displayY = budgetTop + uicore.ScaleDpiF(self._padTop + self._top)
        displayWidth = budgetWidth - uicore.ScaleDpiF(self._padLeft + self._padRight + self._left + self._width)
        displayHeight = budgetHeight - uicore.ScaleDpiF(self._padTop + self._padBottom + self._top + self._height)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateAbsoluteAlignment(self, budget):
        self._left, self._top, self._width, self._height = (self.left,
         self.top,
         self.width or 0,
         self.height or 0)
        displayX = uicore.ScaleDpiF(self._left)
        displayY = uicore.ScaleDpiF(self._top)
        displayWidth = uicore.ScaleDpiF(self._width)
        displayHeight = uicore.ScaleDpiF(self._height)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateTopLeftAlignment(self, budget):
        displayX = uicore.ScaleDpiF(self._left + self._padLeft)
        displayY = uicore.ScaleDpiF(self._top + self._padTop)
        displayWidth = uicore.ScaleDpiF(self._width - self._padLeft - self._padRight)
        displayHeight = uicore.ScaleDpiF(self._height - self._padTop - self._padBottom)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateTopRightAlignment(self, budget):
        parent = self.GetParent()
        budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
        displayX = budgetWidth + uicore.ScaleDpiF(self._padLeft - self._width - self._left)
        displayY = uicore.ScaleDpiF(self._top + self._padTop)
        displayWidth = uicore.ScaleDpiF(self._width - self._padLeft - self._padRight)
        displayHeight = uicore.ScaleDpiF(self._height - self._padTop - self._padBottom)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateBottomRightAlignment(self, budget):
        parent = self.GetParent()
        budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
        displayX = budgetWidth + uicore.ScaleDpiF(self._padLeft - self._width - self._left)
        displayY = budgetHeight + uicore.ScaleDpiF(self._padTop - self._height - self._top)
        displayWidth = uicore.ScaleDpiF(self._width - self._padLeft - self._padRight)
        displayHeight = uicore.ScaleDpiF(self._height - self._padTop - self._padBottom)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateBottomLeftAlignment(self, budget):
        parent = self.GetParent()
        budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
        displayX = uicore.ScaleDpiF(self._left + self._padLeft)
        displayY = budgetHeight + uicore.ScaleDpiF(self._padTop - self._height - self._top)
        displayWidth = uicore.ScaleDpiF(self._width - self._padLeft - self._padRight)
        displayHeight = uicore.ScaleDpiF(self._height - self._padTop - self._padBottom)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateCenterAlignment(self, budget):
        parent = self.GetParent()
        budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
        displayX = (budgetWidth - uicore.ScaleDpiF(self._width)) / 2 + uicore.ScaleDpiF(self._left + self._padLeft)
        displayY = (budgetHeight - uicore.ScaleDpiF(self._height)) / 2 + uicore.ScaleDpiF(self._top + self._padTop)
        displayWidth = uicore.ScaleDpiF(self._width - self._padLeft - self._padRight)
        displayHeight = uicore.ScaleDpiF(self._height - self._padTop - self._padBottom)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateCenterBottomAlignment(self, budget):
        parent = self.GetParent()
        budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
        displayX = (budgetWidth - uicore.ScaleDpiF(self._width)) / 2 + uicore.ScaleDpiF(self._left + self._padLeft)
        displayY = budgetHeight - uicore.ScaleDpiF(self._height + self._top - self._padTop)
        displayWidth = uicore.ScaleDpiF(self._width - self._padLeft - self._padRight)
        displayHeight = uicore.ScaleDpiF(self._height - self._padTop - self._padBottom)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateCenterTopAlignment(self, budget):
        parent = self.GetParent()
        budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
        displayX = (budgetWidth - uicore.ScaleDpiF(self._width)) / 2 + uicore.ScaleDpiF(self._left + self._padLeft)
        displayY = uicore.ScaleDpiF(self._top + self._padTop)
        displayWidth = uicore.ScaleDpiF(self._width - self._padLeft - self._padRight)
        displayHeight = uicore.ScaleDpiF(self._height - self._padTop - self._padBottom)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateCenterLeftAlignment(self, budget):
        parent = self.GetParent()
        budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
        displayX = uicore.ScaleDpiF(self._left + self._padLeft)
        displayY = (budgetHeight - uicore.ScaleDpiF(self._height)) / 2 + uicore.ScaleDpiF(self._top + self._padTop)
        displayWidth = uicore.ScaleDpiF(self._width - self._padLeft - self._padRight)
        displayHeight = uicore.ScaleDpiF(self._height - self._padTop - self._padBottom)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateCenterRightAlignment(self, budget):
        parent = self.GetParent()
        budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
        displayX = budgetWidth - uicore.ScaleDpiF(self._width + self._left - self._padLeft)
        displayY = (budgetHeight - uicore.ScaleDpiF(self._height)) / 2 + uicore.ScaleDpiF(self._top + self._padTop)
        displayWidth = uicore.ScaleDpiF(self._width - self._padLeft - self._padRight)
        displayHeight = uicore.ScaleDpiF(self._height - self._padTop - self._padBottom)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateNoAlignment(self, budget):
        return budget

    @telemetry.ZONE_METHOD
    def UpdateToLeftProportionalAlignment(self, budget):
        width = int(float(self.parent.displayWidth) * self._width)
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        displayX = budgetLeft + uicore.ScaleDpiF(self._padLeft + self._left)
        displayY = budgetTop + uicore.ScaleDpiF(self._padTop + self._top)
        displayHeight = budgetHeight - uicore.ScaleDpiF(self._padTop + self._padBottom)
        displayWidth = width - uicore.ScaleDpiF(self._padLeft + self._padRight)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        if not self.display:
            return budget
        return self.ConsumeBudget(budget)

    @telemetry.ZONE_METHOD
    def UpdateToRightProportionalAlignment(self, budget):
        width = int(float(self.parent.displayWidth) * self._width)
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        displayX = budgetLeft + budgetWidth - width - uicore.ScaleDpiF(self._padRight + self._left)
        displayY = budgetTop + uicore.ScaleDpiF(self._padTop + self._top)
        displayHeight = budgetHeight - uicore.ScaleDpiF(self._padTop + self._padBottom)
        displayWidth = width - uicore.ScaleDpiF(self._padLeft + self._padRight)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        if not self.display:
            return budget
        return self.ConsumeBudget(budget)

    @telemetry.ZONE_METHOD
    def UpdateToTopProportionalAlignment(self, budget):
        height = int(float(self.parent.displayHeight) * self._height)
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        displayX = budgetLeft + uicore.ScaleDpiF(self._padLeft + self._left)
        displayY = budgetTop + uicore.ScaleDpiF(self._padTop + self._top)
        displayWidth = budgetWidth - uicore.ScaleDpiF(self._padLeft + self._padRight)
        displayHeight = height - uicore.ScaleDpiF(self._padTop + self._padBottom)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        if not self.display:
            return budget
        return self.ConsumeBudget(budget)

    @telemetry.ZONE_METHOD
    def UpdateToBottomProportionalAlignment(self, budget):
        height = int(float(self.parent.displayHeight) * self._height)
        budgetLeft, budgetTop, budgetWidth, budgetHeight = budget
        displayX = budgetLeft + uicore.ScaleDpiF(self._padLeft + self._left)
        displayY = budgetTop + budgetHeight - height - uicore.ScaleDpiF(self._padBottom + self._top)
        displayWidth = budgetWidth - uicore.ScaleDpiF(self._padLeft + self._padRight)
        displayHeight = height - uicore.ScaleDpiF(self._padTop + self._padBottom)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        if not self.display:
            return budget
        return self.ConsumeBudget(budget)

    @telemetry.ZONE_METHOD
    def UpdateTopLeftProportionalAlignment(self, budget):
        parent = self.GetParent()
        budgetWidth, budgetHeight = parent.displayWidth, parent.displayHeight
        if self._width < 1.0:
            displayWidth = self._width * budgetWidth - uicore.ScaleDpiF(self._padLeft + self._padRight)
        else:
            displayWidth = uicore.ScaleDpiF(self._width - self._padLeft - self._padRight)
        if self._height < 1.0:
            displayHeight = self._height * budgetHeight - uicore.ScaleDpiF(self._padTop + self._padBottom)
        else:
            displayHeight = uicore.ScaleDpiF(self._height - self._padTop - self._padBottom)
        if self._left < 1.0:
            displayX = (budgetWidth - displayWidth) * (self._left + self._padLeft)
        else:
            displayX = uicore.ScaleDpiF(self._left + self._padLeft)
        if self._top < 1.0:
            displayY = (budgetHeight - displayHeight) * (self._top + self._padTop)
        else:
            displayY = uicore.ScaleDpiF(self._top + self._padTop)
        self.displayRect = (displayX,
         displayY,
         displayWidth,
         displayHeight)
        return budget

    @telemetry.ZONE_METHOD
    def UpdateAlignmentAsRoot(self):
        self._alignmentDirty = False
        self._childrenDirty = False
        self.displayWidth = uicore.ScaleDpiF(self.width)
        self.displayHeight = uicore.ScaleDpiF(self.height)
        if hasattr(self, 'children'):
            budget = (0,
             0,
             self.displayWidth,
             self.displayHeight)
            for each in self.children:
                if each.display:
                    budget = each.Traverse(budget)

    def Traverse(self, mbudget):
        if self.destroyed:
            return mbudget
        if self._alignmentDirty:
            mbudget = self.UpdateAlignment(mbudget)
        elif self.display:
            mbudget = self.ConsumeBudget(mbudget)
        return mbudget

    @telemetry.ZONE_METHOD
    def UpdateAlignment(self, budget):
        if self.destroyed:
            return budget
        align = self.align
        if align == uiconst.NOALIGN:
            self.UpdateAlignmentAsRoot()
            return budget
        self._alignmentDirty = False
        preDX = self.displayX
        preDY = self.displayY
        preDWidth = self.displayWidth
        preDHeight = self.displayHeight
        budget = self._alignFunc(self, budget)
        sizeChange = preDWidth != self.displayWidth or preDHeight != self.displayHeight
        posChange = preDX != self.displayX or preDY != self.displayY
        if sizeChange or posChange:
            if self._OnResize.im_func != Base._OnResize.im_func:
                self._OnResize()
        if sizeChange:
            self._OnSizeChange_NoBlock(uicore.ReverseScaleDpi(self.displayWidth), uicore.ReverseScaleDpi(self.displayHeight))
        self.UpdateAttachments()
        if sizeChange or self._displayDirty:
            children = getattr(self, 'children', None)
            if children:
                for child in children:
                    if child.display:
                        child._alignmentDirty = True
                        if self._displayDirty:
                            child._displayDirty = True

            if self.parent:
                self.parent.FlagNextChildrenDirty(self)
        self._displayDirty = False
        return budget

    @telemetry.ZONE_METHOD
    def UpdateAttachments(self):
        attachedObjects = getattr(self, '_attachedObjects', None)
        if attachedObjects:
            for object in attachedObjects:
                object.UpdateAttachedPosition()

    @telemetry.ZONE_METHOD
    def UpdateAttachedPosition(self):
        parent = self.GetParent()
        if self._attachedTo and parent:
            toObject, objectPoint, myPoint, offset = self._attachedTo
            al, at, aw, ah = (toObject.displayX,
             toObject.displayY,
             toObject.displayWidth,
             toObject.displayHeight)
            if objectPoint in (uiconst.ANCH_TOPLEFT, uiconst.ANCH_CENTERTOP, uiconst.ANCH_TOPRIGHT):
                yPoint = at
            elif objectPoint in (uiconst.ANCH_CENTERLEFT, uiconst.ANCH_CENTER, uiconst.ANCH_CENTERRIGHT):
                yPoint = at + ah / 2
            elif objectPoint in (uiconst.ANCH_BOTTOMLEFT, uiconst.ANCH_CENTERBOTTOM, uiconst.ANCH_BOTTOMRIGHT):
                yPoint = at + ah
            if myPoint in (uiconst.ANCH_TOPLEFT, uiconst.ANCH_CENTERTOP, uiconst.ANCH_TOPRIGHT):
                self.top = yPoint
            elif myPoint in (uiconst.ANCH_CENTERLEFT, uiconst.ANCH_CENTER, uiconst.ANCH_CENTERRIGHT):
                self.top = yPoint - self.height / 2
            elif myPoint in (uiconst.ANCH_BOTTOMLEFT, uiconst.ANCH_CENTERBOTTOM, uiconst.ANCH_BOTTOMRIGHT):
                self.top = yPoint - self.height
            if objectPoint in (uiconst.ANCH_TOPLEFT, uiconst.ANCH_CENTERLEFT, uiconst.ANCH_BOTTOMLEFT):
                xPoint = al
            elif objectPoint in (uiconst.ANCH_CENTERTOP, uiconst.ANCH_CENTER, uiconst.ANCH_CENTERBOTTOM):
                xPoint = al + aw / 2
            elif objectPoint in (uiconst.ANCH_TOPRIGHT, uiconst.ANCH_CENTERRIGHT, uiconst.ANCH_BOTTOMRIGHT):
                xPoint = al + aw
            if myPoint in (uiconst.ANCH_TOPLEFT, uiconst.ANCH_CENTERLEFT, uiconst.ANCH_BOTTOMLEFT):
                self.left = xPoint
            elif myPoint in (uiconst.ANCH_CENTERTOP, uiconst.ANCH_CENTER, uiconst.ANCH_CENTERBOTTOM):
                self.left = xPoint - self.width / 2
            elif myPoint in (uiconst.ANCH_TOPRIGHT, uiconst.ANCH_CENTERRIGHT, uiconst.ANCH_BOTTOMRIGHT):
                self.left = xPoint - self.width
            if offset:
                ox, oy = offset
                self.left += ox
                self.top += oy

    def ScaleDpi(self, value):
        return uicore.ScaleDpi(value)

    def ReverseScaleDpi(self, value):
        return uicore.ReverseScaleDpi(value)

    def Toggle(self, *args):
        if self.IsHidden():
            self.Show()
        else:
            self.Hide()

    def Hide(self, *args):
        self.display = False

    def Show(self, *args):
        self.display = True

    def IsHidden(self):
        return not self.display

    def FindParentByName(self, parentName):
        parent = self.GetParent()
        while parent:
            if parent.name == parentName:
                return parent
            parent = parent.GetParent()

    @apply
    def cursor():
        doc = 'Cursor value of this object. Triggers cursor update when set'

        def fget(self):
            return self._cursor

        def fset(self, value):
            self._cursor = value
            uicore.CheckCursor()

        return property(**locals())

    def _OnClose(self, *args, **kw):
        pass

    def _OnResize(self, *args):
        pass

    def _OnSizeChange_NoBlock(self, *args):
        pass

    def OnMouseUp(self, *args):
        pass

    def OnMouseDown(self, *args):
        pass

    def OnMouseEnter(self, *args):
        pass

    def OnMouseExit(self, *args):
        pass

    def OnMouseHover(self, *args):
        pass

    def OnClick(self, *args):
        pass

    def OnMouseMove(self, *args):
        pass

    @apply
    def __bluetype__():
        doc = 'legacy trinity name of object'

        def fget(self):
            if self.__renderObject__:
                return self.__renderObject__().__bluetype__

        return property(**locals())

    @apply
    def __typename__():
        doc = 'legacy type name of object'

        def fget(self):
            if self.__renderObject__:
                return self.__renderObject__().__typename__

        return property(**locals())


ALIGN_AND_CONSUME_FUNCTIONS = {uiconst.TOPLEFT: (Base.UpdateTopLeftAlignment, None),
 uiconst.TOALL: (Base.UpdateToAllAlignment, None),
 uiconst.NOALIGN: (Base.UpdateNoAlignment, None),
 uiconst.TOLEFT: (Base.UpdateToLeftAlignment, Base.ConsumeBudgetToLeftAlignment),
 uiconst.TORIGHT: (Base.UpdateToRightAlignment, Base.ConsumeBudgetToRightAlignment),
 uiconst.TOTOP: (Base.UpdateToTopAlignment, Base.ConsumeBudgetToTopAlignment),
 uiconst.TOBOTTOM: (Base.UpdateToBottomAlignment, Base.ConsumeBudgetToBottomAlignment),
 uiconst.TOLEFT_NOPUSH: (Base.UpdateToLeftAlignment, None),
 uiconst.TORIGHT_NOPUSH: (Base.UpdateToRightAlignment, None),
 uiconst.TOTOP_NOPUSH: (Base.UpdateToTopAlignment, None),
 uiconst.TOBOTTOM_NOPUSH: (Base.UpdateToBottomAlignment, None),
 uiconst.TOLEFT_PROP: (Base.UpdateToLeftProportionalAlignment, Base.ConsumeBudgetToLeftProportionalAlignment),
 uiconst.TORIGHT_PROP: (Base.UpdateToRightProportionalAlignment, Base.ConsumeBudgetToRightProportionalAlignment),
 uiconst.TOTOP_PROP: (Base.UpdateToTopProportionalAlignment, Base.ConsumeBudgetToTopProportionalAlignment),
 uiconst.TOBOTTOM_PROP: (Base.UpdateToBottomProportionalAlignment, Base.ConsumeBudgetToBottomProportionalAlignment),
 uiconst.ABSOLUTE: (Base.UpdateAbsoluteAlignment, None),
 uiconst.TOPLEFT_PROP: (Base.UpdateTopLeftProportionalAlignment, None),
 uiconst.TOPRIGHT: (Base.UpdateTopRightAlignment, None),
 uiconst.BOTTOMRIGHT: (Base.UpdateBottomRightAlignment, None),
 uiconst.BOTTOMLEFT: (Base.UpdateBottomLeftAlignment, None),
 uiconst.CENTER: (Base.UpdateCenterAlignment, None),
 uiconst.CENTERBOTTOM: (Base.UpdateCenterBottomAlignment, None),
 uiconst.CENTERTOP: (Base.UpdateCenterTopAlignment, None),
 uiconst.CENTERLEFT: (Base.UpdateCenterLeftAlignment, None),
 uiconst.CENTERRIGHT: (Base.UpdateCenterRightAlignment, None),
 uiconst.ATTACHED: (Base.UpdateTopLeftAlignment, None)}
exports = {'uiconst.AFFECTEDBYPUSHALIGNMENTS': AFFECTEDBYPUSHALIGNMENTS,
 'uiconst.PUSHALIGNMENTS': PUSHALIGNMENTS}