#Embedded file name: c:/depot/games/branches/release/EVE-TRANQUILITY/carbon/client/script/util/monitor.py
import service
import blue
import uthread
import operator
import util
import base
import gc
import sys
import blue
import trinity
import log
import uicls
import uiconst
import copy
import uiutil
from service import ROLE_IGB
import pychartdir as chart
chart.setLicenseCode('DIST-0000-05de-f7ec-ffbeURDT-232Q-M544-C2XM-BD6E-C452')
GRAPH_MEMORY = 1
GRAPH_PERFORMANCE = 2
GRAPH_HEAP = 3
MAX_LOG_CAPACITY = 10000
LOGTYPE_MAPPING = {0: ('info', '0xffeeeeee'),
 1: ('notice', '0xff22dd22'),
 2: ('warning', '0xffcccc00'),
 3: ('error', '0xffcc0000')}
LOGUPDATETIME = 2000

class Monitor(service.Service):
    __exportedcalls__ = {'Show': [],
     'ShowOutstandingTab': [ROLE_IGB],
     'ShowLogTab': []}
    __dependencies__ = ['settings']
    __update_on_reload__ = 0
    __guid__ = 'svc.monitor'
    __servicename__ = 'monitor'
    __displayname__ = 'Monitor Service'

    def Run(self, memStream = None):
        self.LogInfo('Starting MonitorSvc')
        self.started = False
        self.logRunning = False
        self.logSaveHandle = None
        self.lastLogEntry = None
        self.totalVidMem = trinity.renderContext.GetTotalVideoMemory() / 1048576

    def UpdateHeapHistory(self):
        heaps = blue.MemoryTrackerGetAllProcessHeapsSizes()
        for i, h in enumerate(heaps):
            if i not in self.heaphistory:
                self.heaphistory[i] = []
            self.heaphistory[i].append((blue.os.GetWallclockTime(), h))

    def Stop(self, memStream = None):
        if self.started:
            self.CleanUp()

    def Show(self):
        if not self.started:
            self.started = True
            self.CleanUp()
            self.ResetCounters()
            self.tabs = None
            self.heaphistory = {}
            if prefs.GetValue('heapinfo', 0):
                self.heaphistorytimer = base.AutoTimer(1000, self.UpdateHeapHistory)
        wnd = self.GetWnd(1)
        if wnd is not None and not wnd.destroyed:
            wnd.Maximize()
            self.uitimer = base.AutoTimer(100, self.UpdateUI)
            self.graphtimer = base.AutoTimer(20000, self.UpdateGraph)
            self.heapgraphtimer = base.AutoTimer(20000, self.UpdateHeapGraph)
        wnd.sr.updateTimer = None

    def ShowOutstandingTab(self):
        self.Show()
        blue.pyos.synchro.SleepWallclock(500)
        tabName = 'Outstanding_tab'
        tab = self.tabs.sr.Get(tabName)
        tab.Select(1)

    def ShowLogTab(self):
        self.Show()
        blue.pyos.synchro.SleepWallclock(500)
        tabName = 'Logs_tab'
        tab = self.tabs.sr.Get(tabName)
        tab.Select(1)

    def _OnResize(self, *args):
        if self.tabs and self.tabs.GetSelectedArgs() in ('memory', 'performance', 'heap'):
            self.GetWnd().sr.updateTimer = base.AutoTimer(500, self.UpdateSize)

    def GetGraphMenu(self, *args):
        MEMORY_FILTERS = {'total_memory': 'Total Memory',
         'python_memory': 'Python Memory',
         'blue_memory': 'Blue Memory',
         'other_memory': 'Other Memory',
         'working_set': 'Working Set'}
        PERFORMANCE_FILTERS = {'fps': 'FPS',
         'thread_cpu': 'Thread CPU'}
        if self.GetGraphType() == GRAPH_PERFORMANCE:
            filters = PERFORMANCE_FILTERS
        elif self.GetGraphType() == GRAPH_MEMORY:
            filters = MEMORY_FILTERS
        else:
            return []
        m = []
        for name, label in filters.iteritems():
            m.append(('%s %s' % (['Show', 'Hide'][settings.user.ui.Get('monitor_setting_' + name, 1)], label), self.ToggleMemory, (name,)))

        m.append(None)
        m.append(('Time', self.MemoryTimeMenu()))
        return m

    def GetHeapGraphMenu(self, *args):
        m = []
        for k, v in self.heaphistory.iteritems():
            m.append(('%s %s' % (['Show', 'Hide'][settings.user.ui.Get('monitor_setting_heap_%s' % k, 1)], 'Heap #%s' % k), self.ToggleHeap, (k,)))

        m.append(None)
        return m

    def ToggleHeap(self, name):
        name = 'monitor_setting_heap_%s' % name
        curr = settings.user.ui.Get(name, 1)
        settings.user.ui.Set(name, not curr)
        uthread.new(self.GetHeapGraph)

    def ToggleMemory(self, name):
        name = 'monitor_setting_' + name
        curr = settings.user.ui.Get(name, 1)
        settings.user.ui.Set(name, not curr)
        uthread.new(self.GetGraph)

    def MemoryTimeMenu(self):
        m = []
        for i in [5,
         10,
         30,
         60,
         120,
         9999]:
            m.append(('last %s minutes' % i if i < 9999 else 'Since counter started', self.SetMemoryTime, (i,)))

        return m

    def SetMemoryTime(self, n):
        settings.user.ui.Set('monitor_setting_memory_time', n)
        uthread.new(self.GetGraph)

    def UpdateGraph(self):
        wnd = self.GetWnd()
        if wnd is not None and not wnd.destroyed and self.tabs and hasattr(self.tabs, 'GetSelectedArgs') and self.tabs.GetSelectedArgs() in ('memory', 'performance'):
            self.LogInfo('Updating memory graph')
            self.GetGraph()

    def UpdateHeapGraph(self):
        wnd = self.GetWnd()
        try:
            if wnd is not None and not wnd.destroyed and self.tabs and hasattr(self.tabs, 'GetSelectedArgs') and self.tabs.GetSelectedArgs() in ('heap',):
                self.LogInfo('Updating heap graph')
                self.GetHeapGraph()
        except:
            pass

    def UpdateSize(self):
        uthread.new(self.GetGraph)
        uthread.new(self.GetHeapGraph)
        self.GetWnd(1).sr.updateTimer = None

    def CleanUp(self):
        wnd = self.GetWnd()
        if wnd and not wnd.destroyed:
            wnd.CloseByUser()
        self.timer = None
        self.uitimer = None
        self.modeltimer = None
        self.graphtimer = None
        self.laststats = {}
        self.maxPeaks = {}
        self.lastresetstats = {}
        self.lastVM = None
        self.lastVMDelta = 0
        self.totalVMDelta = 0
        self.statsdiffs = {}
        self.showing = None
        self.settingsinited = 0
        self.pythonProfile = None

    def GetWnd(self, new = 0):
        wnd = uicls.MonitorWnd.GetIfOpen()
        if wnd is None and new:
            wnd = uicls.MonitorWnd.Open()
            wnd.OnClose = self.CloseWnd
            wnd._OnResize = self._OnResize
            main = wnd.sr.maincontainer
            topcontainer = uicls.Container(name='push', parent=main, align=uiconst.TOTOP, height=46, clipChildren=1)
            w = wnd.sr.telemetryButton = uicls.Button(parent=topcontainer, label='Telemetry', align=uiconst.TOPRIGHT, func=self.RunTelemetry)
            w = wnd.sr.fpsText = uicls.Label(text='', parent=topcontainer, align=uiconst.TOPLEFT, top=0, left=8)
            w = wnd.sr.vmText = uicls.Label(text='', parent=topcontainer, align=uiconst.TOPLEFT, top=14, left=8)
            w = wnd.sr.cacheText = uicls.Label(text='', parent=topcontainer, align=uiconst.TOPLEFT, top=28, left=8)
            self.tabs = maintabs = uicls.TabGroup(parent=main)
            wnd.sr.scroll = uicls.Scroll(parent=main, padding=(const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding,
             const.defaultPadding))
            wnd.sr.scroll.sr.id = 'monitorscroll'
            textonly = uicls.Container(name='textonly', parent=main, clipChildren=1, padding=8)
            graph = wnd.sr.graph = uicls.Container(name='graph', parent=main, clipChildren=1, padding=8)
            statusHeader = ' '
            for tme in self.intvals:
                statusHeader += '<t><right>%s' % util.FmtDate(long(tme * 10000), 'ss')

            statusHeader += '<t><right>total'
            wnd.statusLabels = []
            txt = uicls.Label(text=statusHeader, parent=textonly, align=uiconst.TOPLEFT, tabs=[80,
             130,
             180,
             230,
             280,
             330,
             380], state=uiconst.UI_DISABLED)
            for i in xrange(7):
                statusLabel = uicls.Label(text='', parent=textonly, top=(i + 1) * txt.height + 1, align=uiconst.TOPLEFT, tabs=[80,
                 130,
                 180,
                 230,
                 280,
                 330,
                 380], state=uiconst.UI_DISABLED)
                wnd.statusLabels.append(statusLabel)

            wnd.sr.settings = uicls.Container(name='settings', parent=main, clipChildren=1, padding=8)
            w = wnd.sr.queueText = uicls.Label(text='', parent=wnd.sr.settings, align=uiconst.TOTOP)
            wnd.sr.settingsInner = uicls.Container(name='settingsInner', parent=wnd.sr.settings, align=uiconst.TOALL)
            tabs = [('Main',
              wnd.sr.settings,
              self,
              'settings'),
             ('Network',
              textonly,
              self,
              'network'),
             ('Rot',
              wnd.sr.scroll,
              self,
              'rot'),
             ('Timers',
              wnd.sr.scroll,
              self,
              'timers'),
             ('Objects',
              wnd.sr.scroll,
              self,
              'objects'),
             ('Memory',
              graph,
              self,
              'memory'),
             ('Performance',
              graph,
              self,
              'performance'),
             ('Outstanding',
              wnd.sr.scroll,
              self,
              'outstanding'),
             ('Logs',
              wnd.sr.scroll,
              self,
              'logs')]
            if prefs.GetValue('heapinfo', 0):
                tabs.append(['Heap',
                 graph,
                 self,
                 'heap'])
            if session.role & service.ROLE_GML:
                tabs.append(['Method Calls',
                 wnd.sr.scroll,
                 self,
                 'methodcalls'])
            tabData = []
            for label, panel, code, args in tabs:
                tabData.append(uiutil.Bunch(label=label, panel=panel, code=code, args=args, LoadTabCallback=self.Load))

            self.tabs.LoadTabs(tabData, 1, settingsID='monitortabs')
            wnd.sr.bottomCont = bottomCont = uicls.Container(parent=main, align=uiconst.TOBOTTOM, height=48, idx=0)
            wnd.sr.resetWnd = uicls.Container(name='resetwnd', parent=bottomCont, align=uiconst.TOTOP, height=24, idx=0)
            wnd.sr.logWnd = uicls.Container(name='logwnd', parent=bottomCont, align=uiconst.TOTOP, height=24, idx=0)
            wnd.sr.logWnd2 = uicls.Container(name='logwnd2', parent=bottomCont, align=uiconst.TOTOP, height=24, idx=0)
            btns = uicls.ButtonGroup(parent=wnd.sr.logWnd, line=False, btns=[['Start',
              self.StartLogInMemory,
              (),
              51],
             ['Stop',
              self.StopLogInMemory,
              (),
              51],
             ['Clear',
              self.ClearLogInMemory,
              (),
              51],
             ['Copy',
              self.ExportLogInMemory,
              (),
              51],
             ['Attach',
              self.AttachToLogServer,
              (),
              51],
             ['Save',
              self.SaveLogsToFile,
              (),
              51]])
            uicls.Label(parent=wnd.sr.logWnd2, text='<b>Threshold:</b>', align=uiconst.TOLEFT, padLeft=10, padTop=1)
            options = (('Info', 0),
             ('Notice', 1),
             ('Warning', 2),
             ('Error', 3))
            for text, value in options:
                isChecked = blue.logInMemory.threshold == value
                uicls.Checkbox(parent=wnd.sr.logWnd2, text=text, groupname='threshold', align=uiconst.TOLEFT, width=100, top=5, checked=isChecked, callback=self.OnLogThresholdRadioButtons, retval=value)

            edit = uicls.SinglelineEdit(parent=wnd.sr.logWnd2, name='capacityEdit', align=uiconst.TORIGHT, ints=(1, MAX_LOG_CAPACITY), padRight=5, padBottom=5, setvalue=blue.logInMemory.capacity, OnChange=self.OnLogCapacityEdit)
            uicls.Label(parent=wnd.sr.logWnd2, text='<b>Capacity:</b>', align=uiconst.TORIGHT, padLeft=10, padTop=1)
            wnd.sr.methodcallWnd = uicls.Container(name='methodcallwnd', parent=bottomCont, align=uiconst.TOTOP, height=24, idx=0)
            btns = uicls.ButtonGroup(btns=[['Copy',
              self.ExportMethodCalls,
              (),
              51]])
            wnd.sr.methodcallWnd.children.insert(0, btns)
            uicls.Line(parent=wnd.sr.resetWnd, align=uiconst.TOTOP)
            uicls.Button(parent=wnd.sr.resetWnd, label='Reset', align=uiconst.CENTER, func=self.Reset)
            wnd.SetMinSize([400, 300])
            wnd.Maximize(1)
            wnd.SetParent(uicore.layer.abovemain)
        return wnd

    def Load(self, args, *arg):
        wnd = self.GetWnd()
        if wnd:
            wnd.sr.logWnd.state = uiconst.UI_HIDDEN
            wnd.sr.logWnd2.state = uiconst.UI_HIDDEN
            wnd.sr.resetWnd.state = uiconst.UI_HIDDEN
            wnd.sr.methodcallWnd.state = uiconst.UI_HIDDEN
            wnd.sr.bottomCont.height = 24
            self.timer = None
            if args == 'objects':
                wnd.sr.resetWnd.state = uiconst.UI_NORMAL
                self.GetObjects()
            elif args in ('memory', 'performance'):
                blue.pyos.synchro.SleepWallclock(100)
                self.GetGraph()
            elif args in ('heap',):
                self.GetHeapGraph()
            elif args == 'network':
                wnd.sr.resetWnd.state = uiconst.UI_NORMAL
                self.UpdateData()
                self.timer = base.AutoTimer(1000, self.UpdateData)
            elif args == 'rot':
                wnd.sr.resetWnd.state = uiconst.UI_NORMAL
                self.UpdateROT(force=True)
                self.timer = base.AutoTimer(1000, self.UpdateROT)
            elif args == 'settings':
                if not self.settingsinited:
                    self.LoadSettings()
                    self.settingsinited = 1
            elif args == 'timers':
                wnd.sr.resetWnd.state = uiconst.UI_NORMAL
                self.UpdateTimers()
                self.timer = base.AutoTimer(2500, self.UpdateTimers)
            elif args == 'outstanding':
                self.UpdateOutstanding()
                self.timer = base.AutoTimer(100, self.UpdateOutstanding)
            elif args == 'methodcalls':
                wnd.sr.methodcallWnd.state = uiconst.UI_NORMAL
                self.UpdateMethodCalls()
                self.timer = base.AutoTimer(2500, self.UpdateMethodCalls)
            elif args == 'logs':
                self.ShowLogs()
            self.showing = args

    def ShowLogs(self):
        wnd = self.GetWnd()
        if wnd:
            wnd.sr.logWnd.state = uiconst.UI_NORMAL
            wnd.sr.logWnd2.state = uiconst.UI_NORMAL
            wnd.sr.bottomCont.height = 48
            wnd.sr.scroll.Load(contentList=[], headers=['#',
             'time',
             'channel',
             'type',
             'message'], fixedEntryHeight=18)
            self.lastLogEntry = None
            self.DoUpdateLogs()

    def LoadSettings(self):
        wnd = self.GetWnd()
        uicls.Label(text='<br><b>Debug Settings</b> (changing these settings is <b>not</b> recommended):', parent=wnd.sr.settingsInner, align=uiconst.TOTOP)
        if wnd:
            for cfgname, value, label, checked, group in [['userotcache',
              None,
              'Enable rot cache',
              settings.public.generic.Get('userotcache', 1),
              None],
             ['lazyLoading',
              None,
              'Enable Lazy model loading',
              settings.public.generic.Get('lazyLoading', 1),
              None],
             ['preload',
              None,
              'Enable Preloading',
              settings.public.generic.Get('preload', 1),
              None],
             ['asyncLoad',
              None,
              'Enable Asyncronous Loading (change requires reboot)',
              settings.public.generic.Get('asyncLoad', 1),
              None],
             ['resourceUnloading',
              None,
              'Enable Resource Unloading',
              settings.public.generic.Get('resourceUnloading', 1),
              None]]:
                uicls.Checkbox(text=label, parent=wnd.sr.settingsInner, configName=cfgname, retval=value, checked=checked, groupname=group, callback=self.CheckBoxChange, prefstype=('generic',))

    def CheckBoxChange(self, checkbox):
        config = checkbox.data['config']
        if config == 'resourceUnloading':
            trinity.SetEveSpaceObjectResourceUnloadingEnabled(settings.public.generic.Get('resourceUnloading', 1))

    def RunTelemetry(self, *args):
        blue.synchro.SleepWallclock(5000)
        blue.statistics.StartTelemetry('localhost')
        blue.synchro.SleepWallclock(20000)
        blue.statistics.StopTelemetry()

    def Reset(self, *args):
        self.ResetCounters()
        self.lastresetstats = sm.GetService('machoNet').GetConnectionProperties()
        self.laststats = {}
        self.rotinited = 0
        self.lastVM = None
        self.lastVMDelta = 0
        self.totalVMDelta = 0
        self.maxPeaks = {}
        self.typeBag = {}

    def ResetCounters(self, *args):
        self.intvals = [5000,
         10000,
         15000,
         30000,
         60000]
        self.counter = [[],
         [],
         [],
         [],
         [],
         []]
        self.ticker = 0
        self.packets_outTotal = 0
        self.packets_inTotal = 0
        self.bytes_outTotal = 0
        self.bytes_inTotal = 0

    def UpdateROT(self, force = False):
        wnd = self.GetWnd()
        if wnd:
            try:
                rot = blue.classes.LiveCount()
                if not getattr(self, 'rotinited', 0) or force:
                    scrolllist = []
                    for k, v in rot.iteritems():
                        scrolllist.append(uicls.ScrollEntryNode(decoClass=uicls.SE_Generic, totalDelta=0, typeName=k, peakValue=v, lastValue=v, label='%s<t>%s<t>%s<t>%s' % (k,
                         0,
                         v,
                         v)))

                    wnd.sr.scroll.Load(contentList=scrolllist, headers=['type',
                     'delta',
                     'instances',
                     'peak'], fixedEntryHeight=18)
                    self.showing = 'rot'
                    self.rotinited = 1
                    return
                for entry in wnd.sr.scroll.GetNodes():
                    v = rot[entry.typeName]
                    d = v - entry.lastValue
                    td = d + entry.totalDelta
                    entry.totalDelta = td
                    peak = self.maxPeaks.get(entry.typeName, -1)
                    p = max(peak, v)
                    self.maxPeaks[entry.typeName] = p
                    c = ['<color=0xff00ff00>', '<color=0xffff0000>'][td > 0]
                    entry.label = '%s<t>%s%s<color=0xffffffff><t>%s<t>%s' % (entry.typeName,
                     c,
                     td,
                     v,
                     p)
                    if entry.panel:
                        entry.panel.sr.label.text = entry.label
                    entry.lastValue = v

                wnd.sr.scroll.RefreshSort()
            except:
                self.timer = None
                sys.exc_clear()

    def UpdateUI(self):
        wnd = self.GetWnd()
        if not wnd or wnd.destroyed:
            return
        hd, li = blue.pyos.ProbeStuff()
        info = util.Row(list(hd), li)
        virtualMem = info.pagefileUsage / 1024
        if self.lastVM is None:
            self.lastVM = virtualMem
        delta = virtualMem - self.lastVM
        self.totalVMDelta += delta
        self.lastVM = virtualMem
        delta = delta or self.lastVMDelta
        self.lastVMDelta = delta
        dc = ['<color=0xff00ff00>', '<color=0xffff0000>'][delta > 0]
        tdc = ['<color=0xff00ff00>', '<color=0xffff0000>'][self.totalVMDelta > 0]
        try:
            dev = trinity.device
            iml = ''
            if blue.logInMemory.isActive:
                iml = 'In-memory logging <color=0xff00ff00>active</color> (%s / %s)' % (LOGTYPE_MAPPING.get(blue.logInMemory.threshold, ('Unknown', ''))[0], blue.logInMemory.capacity)
            fps = 'Fps: %.1f - %s' % (blue.os.fps, iml)
            if wnd.sr.fpsText.text != fps:
                wnd.sr.fpsText.text = fps
            vm = 'VM Size/D/TD: %sK / %s%sK<color=0xffffffff> / %s%sK<color=0xffb0b0b0> - totalVidMem: %sM' % (util.FmtAmt(virtualMem),
             dc,
             util.FmtAmt(delta),
             tdc,
             util.FmtAmt(self.totalVMDelta),
             self.totalVidMem)
            if wnd.sr.vmText.text != vm:
                wnd.sr.vmText.text = vm
            inUse = util.FmtAmt(blue.motherLode.memUsage / 1024)
            total = util.FmtAmt(blue.motherLode.maxMemUsage / 1024)
            num = blue.motherLode.size()
            vm = 'Resource Cache Usage: %sK / %sK - %s objects' % (inUse, total, num)
            if wnd.sr.cacheText.text != vm:
                wnd.sr.cacheText.text = vm
            spaceMgr = sm.StartService('space')
            mo = 'Lazy Queue: %s' % getattr(spaceMgr, 'lazyLoadQueueCount', 0)
            if session.role & service.ROLEMASK_ELEVATEDPLAYER:
                mo += ' - Preload Queue: %s' % getattr(spaceMgr, 'preloadQueueCount', 22)
            if wnd.sr.queueText.text != mo:
                wnd.sr.queueText.text = mo
        except Exception as e:
            print 'e', e
            self.uitimer = None
            sys.exc_clear()

    def GetTrace(self, item):
        trace = ''
        while item.parent:
            trace = '/' + item.name + trace
            item = item.parent

        return trace

    def UpdateTimers(self):
        wnd = self.GetWnd()
        if not wnd or wnd.destroyed:
            return
        scrolllist = []
        for timer in base.AutoTimer.autoTimers.iterkeys():
            label = str(timer.method)
            label = label[1:]
            label = label.split(' ')
            label = ' '.join(label[:3])
            scrolllist.append(uicls.ScrollEntryNode(decoClass=uicls.SE_Generic, label='%s<t>%s<t>%s' % (label, timer.interval, timer.run)))

        wnd.sr.scroll.Load(contentList=scrolllist, headers=['method', 'interval', 'run'], fixedEntryHeight=18)

    def UpdateLogs(self):
        self.logRunning = True
        wnd = self.GetWnd()
        if wnd is None:
            return
        try:
            while 1:
                loggingToWindow = not (not wnd or wnd.destroyed or self.tabs.GetSelectedArgs() != 'logs')
                if not loggingToWindow and self.logSaveHandle is None or not self.logRunning:
                    return
                self.DoUpdateLogs(loggingToWindow)
                blue.pyos.synchro.SleepWallclock(LOGUPDATETIME)

        finally:
            self.logRunning = False

    def DoUpdateLogs(self, loggingToWindow = True):
        wnd = self.GetWnd()
        scrolllist = []
        entries = blue.logInMemory.GetEntries()
        logsToFile = []
        if entries:
            for i, e in enumerate(entries):
                if e == self.lastLogEntry:
                    break
                s = LOGTYPE_MAPPING.get(e[2], ('Unknown', '0xffeeeeee'))
                lineno = 0
                for line in e[4].split('\n'):
                    label = '%s<t>%s<t>%s::%s<t><color=%s>%s</color><t>%s' % (str(e[3] + lineno)[-15:],
                     util.FmtDate(e[3], 'nl'),
                     e[0],
                     e[1],
                     s[1],
                     s[0],
                     line.replace('<', '&lt;'))
                    scrolllist.append(uicls.ScrollEntryNode(decoClass=uicls.SE_Generic, label=label))
                    lineno += 1

                txt = '%s\t%s::%s\t%s\t%s\n' % (util.FmtDate(e[3], 'nl'),
                 e[0],
                 e[1],
                 s[0],
                 e[4])
                logsToFile.append(txt)

            if self.logSaveHandle:
                logsToFile.reverse()
                for l in logsToFile:
                    self.logSaveHandle.Write(l)

            self.lastLogEntry = entries[0]
            if scrolllist and loggingToWindow:
                wnd.sr.scroll.AddEntries(-1, scrolllist)
        MAXENTRIES = 5000
        if len(wnd.sr.scroll.GetNodes()) > MAXENTRIES * 2:
            self.LogInfo('Reached', len(wnd.sr.scroll.GetNodes()), 'log entries. Truncating down to %d' % MAXENTRIES)
            wnd.sr.scroll.RemoveEntries(wnd.sr.scroll.GetNodes()[:-MAXENTRIES])

    def StartLogInMemory(self):
        blue.logInMemory.Start()
        if not self.logRunning:
            uthread.new(self.UpdateLogs)

    def StopLogInMemory(self):
        blue.logInMemory.Stop()
        if self.logSaveHandle:
            self.logSaveHandle.Close()
            self.logSaveHandle = None
        self.logRunning = False

    def ClearLogInMemory(self):
        blue.logInMemory.Clear()
        self.StopLogInMemory()
        blue.pyos.synchro.SleepWallclock(LOGUPDATETIME * 2)
        self.StartLogInMemory()

    def OnLogThresholdRadioButtons(self, button):
        threshold = button.data['value']
        blue.logInMemory.threshold = int(threshold)

    def OnLogCapacityEdit(self, value):
        if value:
            blue.logInMemory.capacity = min(int(value), MAX_LOG_CAPACITY)

    def GetInMemoryLogs(self):
        txt = 'Time\tFacility\tType\tMessage\r\n'
        entries = blue.logInMemory.GetEntries()
        entries.reverse()
        for e in entries:
            s = LOGTYPE_MAPPING.get(e[2], ('Unknown', ''))
            for line in e[4].split('\n'):
                try:
                    txt += '%s\t%s::%s\t%s\t%s\r\n' % (util.FmtDate(e[3], 'nl'),
                     e[0],
                     e[1],
                     s[0],
                     line)
                except:
                    txt += '***Error writing out logline***\r\n'

        return txt

    def ExportLogInMemory(self, *args):
        blue.pyos.SetClipboardData(self.GetInMemoryLogs())
        uicore.Message('CustomInfo', {'info': 'Logs copied to clipboard.'})

    def GetMethodCalls(self):
        txt = 'Time\tMethod\tDuration [ms]\n'
        entries = base.methodCallHistory
        for e in entries:
            txt += '%s\t%s\t%s\n' % (util.FmtDate(e[1], 'sl'), e[0], e[2] / const.MSEC)

        return txt

    def ExportMethodCalls(self, *args):
        blue.pyos.SetClipboardData(self.GetMethodCalls())
        uicore.Message('CustomInfo', {'info': 'Method calls copied to clipboard.'})

    def AttachToLogServer(self):
        blue.AttachToLogServer()
        uicore.Message('CustomInfo', {'info': 'Done attaching to Log Server.'})

    def SaveLogsToFile(self):
        filename = 'evelogs.log'
        self.logSaveHandle = blue.classes.CreateInstance('blue.ResFile')
        directory = blue.win32.SHGetFolderPath(blue.win32.CSIDL_PERSONAL) + '\\EVE\\logs\\'
        path = directory + filename
        self.logSaveHandle.Create(path)
        if not self.logRunning:
            blue.logInMemory.Start()
            uthread.new(self.UpdateLogs)
        uicore.Message('CustomInfo', {'info': 'Saving logs directly to file at %s' % path})

    def UpdateOutstanding(self):
        wnd = self.GetWnd()
        if not wnd or wnd.destroyed:
            return
        scrolllist = []
        for ct in base.outstandingCallTimers:
            method = ct[0]
            t = ct[1]
            label = '%s<t>%s<t>%s' % (method, util.FmtDate(t, 'nl'), util.FmtTime(blue.os.GetWallclockTimeNow() - t))
            scrolllist.append(uicls.ScrollEntryNode(decoClass=uicls.SE_Generic, label=label))

        wnd.sr.scroll.Load(contentList=scrolllist, headers=['method', 'time', 'dt'])

    def UpdateMethodCalls(self):
        wnd = self.GetWnd()
        if not wnd or wnd.destroyed:
            return
        scrolllist = []
        history = list(base.methodCallHistory)
        history.reverse()
        for ct in history[:100]:
            method = ct[0]
            t = ct[1]
            label = '%s<t>%s<t>%s' % (method, util.FmtDate(t, 'nl'), ct[2] / const.MSEC)
            scrolllist.append(uicls.ScrollEntryNode(decoClass=uicls.SE_Generic, label=label))

        wnd.sr.scroll.Load(contentList=scrolllist, headers=['method', 'time', 'ms'])
        wnd.sr.scroll.sr.notSortableColumns = ['method']

    def UpdateData(self):
        wnd = self.GetWnd()
        if not wnd or wnd.destroyed:
            return
        try:
            self.ticker += self.intvals[0]
            if self.ticker > self.intvals[-1]:
                self.ticker = self.intvals[0]
            stats = sm.GetService('machoNet').GetConnectionProperties()
            if self.laststats == {}:
                self.laststats = stats
            if self.lastresetstats != {}:
                for key in stats.iterkeys():
                    stats[key] = stats[key] - self.lastresetstats[key]

            props = [('Packets out', 'packets_out', 0),
             ('Packets in', 'packets_in', 0),
             ('Kilobytes out', 'bytes_out', 1),
             ('Kilobytes in', 'bytes_in', 1)]
            for i in xrange(len(self.counter) - 1):
                self.counter[i].append([ stats[key] - self.laststats[key] for header, key, K in props ])
                self.counter[i] = self.counter[i][-(self.intvals[i] / 1000):]

            self.counter[-1].append([ stats[key] - self.laststats[key] for header, key, K in props ])
            if wnd.state != uiconst.UI_NORMAL:
                self.laststats = stats
                return
            valueIdx = 0
            for header, key, K in props:
                statusstr = '%s' % header
                for intvals in self.counter:
                    value = reduce(operator.add, [ intval[valueIdx] for intval in intvals ], 0)
                    if not value:
                        statusstr += '<t><right>-'
                    else:
                        statusstr += '<t><right>%s' % [value, '%.1f' % (value / 1024.0)][K]

                wnd.statusLabels[valueIdx].text = statusstr
                valueIdx += 1

            wnd.statusLabels[valueIdx].text = 'Outstanding<t><right>%s' % stats['calls_outstanding']
            valueIdx += 1
            wnd.statusLabels[valueIdx].text = 'Blocking Calls<t><right>%s' % stats['blocking_calls']
            valueIdx += 1
            block_time = stats['blocking_call_times']
            if block_time >= 0:
                secs = util.SecsFromBlueTimeDelta(block_time)
                wnd.statusLabels[valueIdx].text = 'Blocking time<t><right>%sH<t><right>%sM<t><right>%sS' % util.HoursMinsSecsFromSecs(secs)
            elif not hasattr(self, 'warnedBlockingTimeNegative'):
                self.warnedBlockingTimeNegative = True
                log.LogTraceback('Blocking time is negative?')
            self.laststats = stats
        except:
            self.timer = None
            raise 

    def GetGraphType(self):
        if self.tabs and hasattr(self.tabs, 'GetSelectedArgs'):
            return {'memory': GRAPH_MEMORY,
             'performance': GRAPH_PERFORMANCE,
             'heap': GRAPH_HEAP}.get(self.tabs.GetSelectedArgs(), None)

    def GetObjects(self, num = 1000000, drill = None, textDrill = None, b = 0, e = 100):
        wnd = self.GetWnd()
        if not wnd or wnd.destroyed:
            return
        dict = {}
        import weakref
        for object in gc.get_objects():
            tp = type(object)
            if not isinstance(object, weakref.ProxyType):
                try:
                    tp = object.__class__
                except AttributeError:
                    sys.exc_clear()

            dict[tp] = dict.get(tp, 0) + 1

        dict2 = {}
        for k, v in dict.iteritems():
            n = k.__module__ + '.' + k.__name__
            dict2[n] = dict2.get(n, 0) + v

        scrolllist = []
        items = dict2.items()
        items.sort()
        for tp, inst in items:
            scrolllist.append(uicls.ScrollEntryNode(decoClass=uicls.SE_Generic, OnDblClick=self.ClickEntry, instType=tp, label='%s<t>%s' % (tp, util.FmtAmt(inst))))

        wnd.sr.scroll.Load(contentList=scrolllist, headers=['type', 'instances'], fixedEntryHeight=18)

    def GetHeapGraph(self):
        if self.GetGraphType() != GRAPH_HEAP:
            return
        fontSize = 7.5
        fontFace = 'arial.ttc'
        wnd = self.GetWnd()
        wnd.sr.graph.Flush()
        w, h = wnd.sr.graph.absoluteRight - wnd.sr.graph.absoluteLeft, wnd.sr.graph.absoluteBottom - wnd.sr.graph.absoluteTop
        width = w
        height = h
        c = chart.XYChart(width, height, bgColor=chart.Transparent)
        c.setColors(chart.whiteOnBlackPalette)
        c.setBackground(chart.Transparent)
        c.setTransparentColor(-1)
        c.setAntiAlias(1, 1)
        offsX = 60
        offsY = 17
        canvasWidth = width - 1 * offsX - 50
        canvasHeight = height - offsY * 2.5
        plotArea = c.setPlotArea(offsX, offsY, canvasWidth, canvasHeight, 1711276032, -1, -1, 5592405)
        import random
        c.addLegend(85, 18, 0, fontFace, fontSize).setBackground(chart.Transparent)
        random.seed(1001)
        for k, lst in self.heaphistory.iteritems():
            name = 'monitor_setting_heap_%s' % k
            if not settings.user.ui.Get(name, 1):
                continue
            memData = []
            timeData = []
            for t, n in lst:
                memData.append(n / 1024 / 1024)
                year, month, wd, day, hour, minutes, sec, ms = util.GetTimeParts(t)
                timeData.append(chart.chartTime(year, month, day, hour, minutes, sec))

            lines = c.addLineLayer()
            l = (random.randint(0, 15), random.randint(0, 255), random.randint(0, 255))
            l = '0x%X%X%Xee' % (l[0], l[1], l[2])
            lines.addDataSet(memData, int(l, 16), '#%s' % k).setLineWidth(1)
            lines.setXData(timeData)

        c.xAxis().setDateScale3('{value|hh:nn}')
        leftAxis = c.yAxis()
        leftAxis.setTitle('Heap Size (MB)')
        buf = c.makeChart2(chart.PNG)
        hostBitmap = trinity.Tr2HostBitmap(w, h, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
        hostBitmap.LoadFromPngInMemory(buf)
        linegr = uicls.Sprite(parent=wnd.sr.graph, align=uiconst.TOALL)
        linegr.GetMenu = self.GetHeapGraphMenu
        linegr.texture.atlasTexture = uicore.uilib.CreateTexture(width, height)
        linegr.texture.atlasTexture.CopyFromHostBitmap(hostBitmap)

    def GetGraph(self):
        isPerf = False
        if self.GetGraphType() == GRAPH_PERFORMANCE:
            isPerf = True
        fontSize = 7.5
        fontFace = 'arial.ttc'
        wnd = self.GetWnd()
        wnd.sr.graph.Flush()
        w, h = wnd.sr.graph.absoluteRight - wnd.sr.graph.absoluteLeft, wnd.sr.graph.absoluteBottom - wnd.sr.graph.absoluteTop
        minutes = settings.user.ui.Get('monitor_setting_memory_time', 60)
        trend = blue.pyos.cpuUsage[-minutes * 60 / 10:]
        memCounters = {}
        perfCounters = {}
        mega = 1.0 / 1024.0 / 1024.0
        timeData = []
        memData = []
        pymemData = []
        bluememData = []
        othermemData = []
        workingsetData = []
        ppsData = []
        fpsData = []
        threadCpuData = []
        procCpuData = []
        lastT = lastpf = 0
        t1 = 0
        if len(trend) > 1:
            t, cpu, mem, sched = trend[0]
            lastT = t
            lastpf = mem[-1]
            t1 = trend[0][0]
        benice = blue.pyos.BeNice
        for t, cpu, mem, sched in trend:
            benice()
            elap = t - t1
            t1 = t
            mem, pymem, workingset, pagefaults, bluemem = mem
            fps, nr_1, ny, ns, dur, nr_2 = sched
            fpsData.append(fps)
            memData.append(mem * mega)
            pymemData.append(pymem * mega)
            bluememData.append(bluemem * mega)
            othermem = (mem - bluemem) * mega
            if othermem < 0:
                othermem = 0
            othermemData.append(othermem)
            workingsetData.append(workingset * mega)
            thread_u, proc_u, kernel_u, process_kernel_u = cpu
            if elap:
                thread_cpupct = thread_u / float(elap) * 100.0
                proc_cpupct = proc_u / float(elap) * 100.0
            else:
                thread_cpupct = proc_cpupct = 0.0
            threadCpuData.append(thread_cpupct)
            procCpuData.append(proc_cpupct)
            dt = t - lastT
            lastT = t
            pf = pagefaults - lastpf
            lastpf = pagefaults
            pps = pf / (dt * 1e-07) if dt else 0
            ppsData.append(pps)
            year, month, wd, day, hour, minutes, sec, ms = util.GetTimeParts(t)
            timeData.append(chart.chartTime(year, month, day, hour, minutes, sec))

        if len(ppsData) > 1:
            ppsData[0] = ppsData[1]
        memCounters['blue_memory'] = (False,
         bluememData,
         3377390,
         1,
         False)
        memCounters['other_memory'] = (False,
         othermemData,
         16776960,
         1,
         False)
        memCounters['python_memory'] = (False,
         pymemData,
         65280,
         1,
         False)
        memCounters['total_memory'] = (False,
         memData,
         16711680,
         2,
         False)
        memCounters['working_set'] = (False,
         workingsetData,
         65535,
         1,
         False)
        memCounters['thread_cpu'] = (True,
         threadCpuData,
         6749952,
         1,
         True)
        memCounters['fps'] = (True,
         fpsData,
         16711680,
         1,
         False)
        width = w
        height = h
        c = chart.XYChart(width, height, bgColor=chart.Transparent)
        c.setColors(chart.whiteOnBlackPalette)
        c.setBackground(chart.Transparent)
        c.setTransparentColor(-1)
        c.setAntiAlias(1, 1)
        offsX = 60
        offsY = 17
        canvasWidth = width - 1 * offsX - 50
        canvasHeight = height - offsY * 2.5
        plotArea = c.setPlotArea(offsX, offsY, canvasWidth, canvasHeight, 1711276032, -1, -1, 5592405)
        c.addLegend(85, 18, 0, fontFace, fontSize).setBackground(chart.Transparent)
        if len(timeData) > 1:
            c.xAxis().setDateScale3('{value|hh:nn}')
        lines = c.addLineLayer()
        lines2 = c.addLineLayer2()
        lines2.setUseYAxis2()
        leftAxis = c.yAxis()
        rightAxis = c.yAxis2()
        if isPerf:
            leftAxis.setTitle('Frames per second')
            rightAxis.setTitle('CPU (%)')
        else:
            leftAxis.setTitle('Memory (MB)')
        for i, k in enumerate(memCounters.keys()):
            if settings.user.ui.Get('monitor_setting_%s' % k, 1):
                title = k.replace('_', ' ').capitalize()
                if isPerf == memCounters[k][0]:
                    data = memCounters[k][1]
                    col = memCounters[k][2]
                    lineWidth = memCounters[k][3]
                    if not memCounters[k][4]:
                        l = lines
                    else:
                        l = lines2
                    l.addDataSet(data, col, title).setLineWidth(lineWidth)

        lines.setXData(timeData)
        lines2.setXData(timeData)
        if trend:
            pf = trend[-1][2][-1]
            label = 'Working set: %iMB, Virtual mem: %iMB, Page faults: %s' % (workingsetData[-1], memData[-1], util.FmtAmt(pf))
            c.addText(offsX, 2, label)
        buf = c.makeChart2(chart.PNG)
        hostBitmap = trinity.Tr2HostBitmap(w, h, 1, trinity.PIXEL_FORMAT.B8G8R8A8_UNORM)
        hostBitmap.LoadFromPngInMemory(buf)
        linegr = uicls.Sprite(parent=wnd.sr.graph, align=uiconst.TOALL)
        linegr.GetMenu = self.GetGraphMenu
        linegr.texture.atlasTexture = uicore.uilib.CreateTexture(width, height)
        linegr.texture.atlasTexture.CopyFromHostBitmap(hostBitmap)

    def ClickEntry(self, entry, *args):
        typeName = entry.sr.node.instType.__name__
        inst = gc.get_objects()
        alldict = {}
        for object in inst:
            s = type(object)
            alldict.setdefault(s, []).append(object)

        attrs = {'BlueWrapper': ['__typename__', '__guid__'],
         'instance': ['__class__', '__guid__'],
         'class': ['__guid__', '__class__', '__repr__']}
        attr = attrs.get(typeName, None)
        if attr is None:
            return
        dict = {}
        for i in alldict[entry.sr.node.instType]:
            stringval = ''
            for a in attr:
                stringval += str(getattr(i, a, None))[:24] + '<t>'

            dict.setdefault(stringval, []).append(i)

        scrolllist = []
        for tp, inst in dict.iteritems():
            if tp == 'None<t>' * len(attr):
                continue
            scrolllist.append(uicls.ScrollEntryNode(decoClass=uicls.SE_Generic, label='%s%s' % (tp, util.FmtAmt(len(inst)))))

        wnd = self.GetWnd()
        if not wnd or wnd.destroyed:
            return
        wnd.wnd.sr.scroll.Load(contentList=scrolllist, headers=attr + ['instances'], fixedEntryHeight=18)

    def CloseWnd(self, *args):
        self.settingsinited = 0
        self.showing = None
        self.rotinited = 0
        self.uitimer = None
        self.modeltimer = None
        self.graphtimer = None
        self.timer = None
        self.lastVM = None
        self.lastVMDelta = 0
        self.totalVMDelta = 0


class MonitorWnd(uicls.Window):
    __guid__ = 'uicls.MonitorWnd'
    default_windowID = 'MonitorWnd'
    default_topParentHeight = 0

    def ApplyAttributes(self, attributes):
        uicls.Window.ApplyAttributes(self, attributes)
        self.scope = 'all'
        self.SetCaption('Monitor')