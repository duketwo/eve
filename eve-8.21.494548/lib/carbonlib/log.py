#Embedded file name: c:\depot\games\branches\release\EVE-TRANQUILITY\carbon\common\lib\log.py
import blue
import sys
import traceback2
import __builtin__
import zlib
from cStringIO import StringIO
import os
LGINFO = 1
LGNOTICE = 32
LGWARN = 2
LGERR = 4
channelDict = {}
stackFileNameSubPaths = ()
msgWindowStreamToMsgWindowFunc = None
uiMessageFunc = None

def SuppressAllChannels():
    global channelDict
    channelDict = {LGINFO: 0,
     LGNOTICE: 0,
     LGWARN: 0,
     LGERR: 0}


def UnsuppressAllChannels():
    global channelDict
    channelDict = {LGINFO: 1,
     LGNOTICE: 1,
     LGWARN: 1,
     LGERR: 1}


UnsuppressAllChannels()
try:
    role = boot.role
    isExefile = True
except:
    isExefile = False

if isExefile:
    if prefs.HasKey('logInfo'):
        channelDict.update({LGINFO: prefs.logInfo})
    if prefs.HasKey('logNotice'):
        channelDict.update({LGNOTICE: prefs.logNotice})
    if prefs.HasKey('logWarning'):
        channelDict.update({LGWARN: prefs.logWarning})
    if prefs.HasKey('logError'):
        channelDict.update({LGERR: prefs.logError})
else:
    prefs = None

def Suppress(logflag):
    channelDict[logflag] = 0


def Unsuppress(logflag):
    channelDict[logflag] = 1


class ChannelWrapper(blue.LogChannel):

    def IsOpen(self, logflag):
        return channelDict.get(logflag, 1) and blue.LogChannel.IsOpen(self, logflag)

    def IsLogChannelOpen(self, logflag):
        return blue.LogChannel.IsOpen(self, logflag)

    def Log(self, value, flag = LGINFO, backstack = 0, force = False):
        if channelDict.get(flag, 1) or force:
            blue.LogChannel.Log(self, value, flag, backstack)

    def open(self, flag = LGINFO, bufsize = -1):
        return LogChannelStream(self, flag, bufsize)


Channel = ChannelWrapper
for f in Channel.flags:
    globals()[f] = Channel.flags[f]
    globals()[f.lower()] = Channel.flags[f]

def MsgWindowStreamToMsgWindow():
    if hasattr(session, 'userid') and session.userid and settings.generic:
        return settings.generic.Get('exceptionPopups', 0)
    if prefs:
        return prefs.GetValue('exceptionPopups', 0)
    return 0


def SetUiMessageFunc(func):
    global uiMessageFunc
    uiMessageFunc = func


def SetMsgWindowStreamToMsgWindowfunc(func):
    global msgWindowStreamToMsgWindowFunc
    msgWindowStreamToMsgWindowFunc = func


def SetStackFileNameSubPaths(filePaths):
    global stackFileNameSubPaths
    stackFileNameSubPaths = filePaths


def DefaultUIMessage(*args):
    print args


def __init__():
    AddGlobalChannels(['UI',
     'General',
     'MethodCalls',
     'Unittest'])
    SetMsgWindowStreamToMsgWindowfunc(MsgWindowStreamToMsgWindow)
    SetStackFileNameSubPaths(('/server/', '/client/', '/common/'))
    SetUiMessageFunc(DefaultUIMessage)
    if prefs and prefs.GetValue('logstderr', 0):
        for name, flag, nobuf in [('stderr', WARN, True)]:
            old = getattr(sys, name, None)
            bufsize = 1 if nobuf else -1
            stream = LogChannelStream(GetChannel('sys.' + name), flag, bufsize)
            if old:
                m = Multiplex([old, stream])
            else:
                m = stream
            setattr(sys, name, m)


def AddGlobalChannels(channels):
    g = globals()
    for channel in channels:
        if channel.lower() not in g:
            g[channel.lower()] = GetChannel(channel)


traceID = 1L
baseName = ''
if isExefile:
    baseName = '%s' % boot.role
channels = {}

def GetChannel(name):
    if '.' not in name:
        name = baseName + '.' + name
    if name not in channels:
        s = name.split('.')
        facility = '.'.join(s[:-1])
        obj = s[-1]
        channels[name] = Channel(facility.encode('utf-8'), obj.encode('utf-8'))
    return channels[name]


getStackFileNames = {}

def GetStackFileName(filename):
    if filename not in getStackFileNames:
        filename2 = filename.lower().replace('\\', '/')
        for subpath in stackFileNameSubPaths:
            f = filename2.rfind(subpath)
            if f >= 0:
                filename2 = filename2[f:]
                break

        if '/carbon/' in filename and '/carbon/' not in filename2:
            filename2 = '/../carbon' + filename2
        getStackFileNames[filename] = (strx(filename2), not (filename.endswith('/effectcode.py') or filename.endswith('/log.py')))
    return getStackFileNames[filename]


def GetStack(exception_list, caught_list = None, show_locals = 0, show_lines = True):
    s = GetStackOnly(exception_list, caught_list, show_locals, show_lines)
    id = GetStackID(exception_list, caught_list)
    return (s, id)


def GetStackID(exception_list, caught_list = None):
    stack = GetStackOnly(exception_list, caught_list, show_locals=0, show_lines=False)
    stack = ''.join(stack)[-4000:]
    return (zlib.adler32(stack), stack)


def GetStackOnly(exception_list, caught_list = None, show_locals = 0, show_lines = True):
    if caught_list is not None:
        stack = ['Caught at:\n']
        stack += FormatList(caught_list, show_locals=False, show_lines=show_lines)
        stack.append('Thrown at:\n')
    else:
        stack = []
    stack += FormatList(exception_list, show_locals=show_locals, show_lines=show_lines)
    return stack


def FormatList(extracted_list, show_locals = 0, show_lines = True):
    l = []
    for line in extracted_list:
        l2 = list(line)
        l2[0] = GetStackFileName(l2[0])[0]
        if not show_lines:
            l2[3] = ''
        l.append(l2)

    lines = traceback2.format_list(l, show_locals, format=traceback2.FORMAT_LOGSRV | traceback2.FORMAT_SINGLE)
    return lines


logExceptionLevel = 0

def LogException(extraText = '', channel = 'general', toConsole = 1, toLogServer = 1, toAlertSvc = None, toMsgWindow = 1, exctype = None, exc = None, tb = None, severity = None, show_locals = 1):
    global logExceptionLevel
    if logExceptionLevel > 0:
        return
    _tmpctx = blue.pyos.taskletTimer.EnterTasklet('Logging::LogException')
    logExceptionLevel += 1
    if not exctype:
        exctype, exc, tb = sys.exc_info()
    try:
        try:
            _LogException((exctype, exc, tb), extraText, channel, toConsole, toLogServer, toAlertSvc, toMsgWindow, severity, show_locals)
            return
        except Exception:
            try:
                traceback2.print_exc(show_locals=3)
                stream = LogChannelStream(GetChannel('general'))
                traceback2.print_exc(show_locals=3, file=stream)
                stream.close()
            except Exception:
                pass

        try:
            traceback2.print_exception(exctype, exc, tb, file=sys.stdout, show_locals=show_locals)
            stream = LogChannelStream(GetChannel(channel), ERR)
            print >> stream, 'retrying traceback log, got an error in _LogException'
            traceback2.print_exception(exctype, exc, tb, file=stream, show_locals=show_locals)
            stream.close()
        except Exception:
            try:
                traceback2.print_exc(show_locals=3)
            except:
                pass

    finally:
        del tb
        logExceptionLevel -= 1
        blue.pyos.taskletTimer.ReturnFromTasklet(_tmpctx)


def _LogException(exc_info, extraText, channel, toConsole, toLogServer, toAlertSvc, toMsgWindow, severity, show_locals):
    global traceID
    exctype, exc, tb = exc_info
    exception_list = traceback2.extract_tb(tb, extract_locals=show_locals)
    if tb:
        caught_list = traceback2.extract_stack(tb.tb_frame)
    else:
        caught_list = traceback2.extract_stack(up=2)
    formatted_exception = traceback2.format_exception_only(exctype, exc)
    stack, stackID = GetStack(exception_list, caught_list, show_locals=show_locals)
    if severity is None:
        severity = (ERR, WARN)[isinstance(exc, UserError)]
    if toAlertSvc is None:
        toAlertSvc = severity in (ERR,)
    if toMsgWindow and isinstance(exc, UserError) and boot.role == 'client':
        toMsgWindow = 0
        uiMessageFunc(*exc.args)
    out = GetMultiplex(channel, severity, [toConsole, 0][toLogServer == 1], toLogServer, toMsgWindow, toAlertSvc, stackID)
    pre = ('', 'REMOTE')[channel == 'remote.exc']
    tmpTraceID = traceID
    traceID += 1
    print >> out, '%sEXCEPTION #%d logged at ' % (pre, tmpTraceID), blue.os.FormatUTC()[0], blue.os.FormatUTC()[2], extraText
    for line in stack:
        print >> out, line,

    for line in formatted_exception:
        print >> out, line,

    if exctype is MemoryError:
        try:
            DumpMemoryStatus(out)
            DumpMemHistory(out)
        except:
            pass

    try:
        _LogThreadLocals(out)
    except MemoryError:
        pass

    try:
        print >> out, 'Stackhash:%s\n' % stackID[0]
    except Exception:
        pass

    print >> out
    if boot.role != 'client':
        try:
            nodeID = getattr(sm.services['machoNet'], 'nodeID', None)
            ram = blue.win32.GetProcessMemoryInfo()['PagefileUsage'] / 1024 / 1024
            cpuLoad = sm.GetService('machoNet').GetCPULoad()
            m = blue.win32.GlobalMemoryStatus()
            memLeft = m['AvailPhys'] / 1024 / 1024
            txt = 'System Information: '
            txt += ' Node ID: %s' % sm.GetService('machoNet').GetNodeID()
            if boot.role == 'server':
                txt += ' | Node Name: %s' % sm.GetService('machoNet').GetNodeName()
            txt += ' | Total CPU load: %s%%' % int(cpuLoad)
            txt += ' | Process memory in use: %s MB' % ram
            txt += ' | Physical memory left: %s MB' % memLeft
            print >> out, txt
        except Exception as e:
            sys.exc_clear()

    print >> out, '%sEXCEPTION END' % (pre,)
    out.flush()
    if toConsole:
        if toLogServer:
            print >> sys.stderr, 'An exception has occurred.  It has been logged in the log server as exception #%d' % tmpTraceID
        else:
            print >> sys.stderr, 'There is no useful information accompanying this exception in the log server'


def DumpMemHistory(out):
    try:
        if boot.role != 'client':
            import blue, cPickle
            fname = blue.paths.ResolvePath(u'root:/') + 'logs/memhist.b%d.%s.pikl' % (boot.build, blue.os.pid)
            print >> out, 'dumping cpu and memory history in ' + fname
            f = file(fname, 'w')
            cPickle.dump(blue.pyos.cpuUsage, f)
            f.close()
            print >> out, 'dump done.'
    except StandardError:
        pass


def LogTraceback(extraText = '', channel = 'general', toConsole = 1, toAlertSvc = None, toLogServer = 1, nthParent = 0, daStack = None, severity = ERR, show_locals = 1, limit = None):
    global traceID
    if logExceptionLevel > 0:
        return
    _tmpctx = blue.pyos.taskletTimer.EnterTasklet('Logging::LogTraceback')
    try:
        if daStack is None:
            daStack = traceback2.extract_stack(limit=limit, up=nthParent + 1, extract_locals=show_locals)
        if toAlertSvc is None:
            toAlertSvc = severity in (ERR,)
        stack, stackID = GetStack(daStack, None, show_locals, True)
        out = GetMultiplex(channel, severity, [toConsole, 0][toLogServer == 1], toLogServer, 0, toAlertSvc, stackID)
        tmpTraceID = traceID
        traceID += 1
        logMessage = StringIO()
        logMessage.write('STACKTRACE #%d logged at %s %s' % (tmpTraceID, blue.os.FormatUTC()[0], blue.os.FormatUTC()[2]))
        logMessage.write('\n')
        if extraText:
            logMessage.write(extraText)
            logMessage.write('\n')
        for line in stack:
            logMessage.write(line)

        _LogThreadLocals(logMessage)
        logMessage.write('STACKTRACE END')
        print >> out, logMessage.getvalue()
        out.flush()
        if toConsole:
            if toLogServer:
                if '/jessica' in blue.pyos.GetArg():
                    print >> sys.stderr, logMessage.getvalue()
                else:
                    print >> sys.stderr, 'A traceback has been generated.  It has been logged in the log server as stacktrace #%d' % tmpTraceID
            else:
                print >> sys.stderr, 'There is no useful information accompanying this traceback in the log server'
    finally:
        blue.pyos.taskletTimer.ReturnFromTasklet(_tmpctx)


def LogMemoryStatus(extraText = '', channel = 'general'):
    out = GetMultiplex(channel, WARN, 0, 1, 0, 0, 0)
    print >> out, 'Logging memory status : ', extraText
    DumpMemoryStatus(out)


def WhoCalledMe(up = 3):
    try:
        trc = traceback2.extract_stack(limit=1, up=up)[0]
        fileName = os.path.basename(trc[0])
        lineNum = trc[1]
        funcName = trc[2]
        ret = '%s(%s) in %s' % (fileName, lineNum, funcName)
    except:
        ret = 'unknown'

    return ret


def DumpMemoryStatus(out):
    m = blue.win32.GlobalMemoryStatus()
    print >> out, 'GlobalMemoryStatus:'
    for k, v in m.items():
        print >> out, '%s : %r' % (k, v)

    print >> out, 'ProcessMemoryInfo:'
    m = blue.win32.GetProcessMemoryInfo()
    for k, v in m.items():
        print >> out, '%s : %r' % (k, v)

    print >> out, 'Python memory usage: %r' % sys.getpymalloced()
    try:
        print >> out, 'blue WriteStreams: %s, mem use: %s' % (blue.marshal.GetNWriteStreams(), blue.marshal.GetWriteStreamMem())
    except:
        pass

    print >> out, 'end of memory status'
    out.flush()


def StackTrace(channel = 'general', toConsole = 0, text = '', show_locals = 1, nthParent = 0):
    toConsole, toLogServer, toMsgWindow = [(0, 1, 0),
     (1, 1, 1),
     (1, 0, 1),
     (1, 1, 0)][toConsole]
    return LogTraceback('*** STACKTRACE IS NO LONGER SUPPORTED! Use LogTraceback instead *** ' + text, channel, toConsole, 1, toLogServer, show_locals=show_locals, nthParent=nthParent + 1)


__builtin__.StackTrace = StackTrace

def _LogThreadLocals(out):
    out.write('Thread Locals:')
    if hasattr(__builtin__, 'session'):
        out.write('  session was ')
        out.write(str(session))
    else:
        out.write('sorry, no session for ya.')
    try:
        ctk = GetLocalStorage().get('calltimer.key', None)
    except NameError:
        return

    if ctk:
        out.write('  calltimer.key was ')
        out.write(ctk)
    currentcall = GetLocalStorage().get('base.currentcall', None)
    if currentcall:
        try:
            currentcall = currentcall()
            out.write('  currentcall was: ')
            out.write(str(currentcall))
        except ReferenceError:
            pass

    out.write('\n')


def GetMultiplex(channel, mode, toConsole, toLogServer, toMsgWindow, toAlertSvc, stackID):
    to = []
    if toConsole:
        if mode == INFO:
            to.append(sys.stdout)
        else:
            to.append(sys.stderr)
    if toLogServer:
        to.append(LogChannelStream(GetChannel(channel), mode))
    if toMsgWindow and hasattr(__builtin__, 'session'):
        to.append(MsgWindowStream())
    if toAlertSvc and hasattr(__builtin__, 'sm') and 'machoNet' in sm.services:
        to.append(LogAlertServiceStream(GetChannel(channel), mode, stackID))
    return Multiplex(to)


class LogChannelStream(object):
    encoding = 'utf8'

    def __init__(self, channel, mode, bufsize = -1):
        self.channel, self.mode, self.bufsize = channel, mode, bufsize
        self.buff = []

    def __del__(self):
        self.close()

    def write(self, text):
        self.buff.append(text)
        if self.bufsize == 1 and '\n' in text:
            self.lineflush()
        elif self.bufsize == 0:
            self.flush()

    def writelines(self, lines):
        for each in lines:
            self.write(each)

    def close(self):
        if self.buff is not None:
            self.flush()
            self.buff = None

    def __enter__(self):
        return self

    def __exit__(self, exc, val, tb):
        self.close()

    def flush(self):
        out = ''.join(self.buff)
        self.buff = []
        if out:
            self.outputlines(out)

    def lineflush(self):
        out = ''.join(self.buff)
        lines = out.split('\n')
        self.buff = lines[-1:]
        self.outputlines(lines[:-1])

    def outputlines(self, lines):
        mode = self.mode
        self.channel.Log(lines, mode)


class LogAlertServiceStream(object):

    def __init__(self, channel, mode, stackID):
        self.channel, self.mode, self.buff, self.stackID = (channel,
         mode,
         StringIO(),
         stackID)

    def write(self, what):
        self.buff.write(what.encode('utf-8'))

    def flush(self):
        if not self.buff.tell():
            return
        try:
            self.buff.seek(0)
            buff = self.buff.read()
            sm.GetService('alert').SendStackTraceAlert(self.stackID, buff, {ERR: 'Error',
             WARN: 'Warning',
             INFO: 'Info'}.get(self.mode, 'Unknown'))
        except:
            print 'Exception in LogAlertServiceStream'

        self.buff = StringIO()


class MsgWindowStream(object):
    __bad_to_good__ = [('<', '&lt;'),
     ('>', '&gt;'),
     ('\r', ''),
     ('\n', '<br>')]

    def __init__(self):
        self.buff = []

    def write(self, what):
        for bad, good in self.__bad_to_good__:
            what = what.replace(bad, good)

        self.buff.append(what)

    def flush(self):
        if not self.buff:
            return
        try:
            if not MsgWindowStreamToMsgWindow():
                return
            buff = ''.join(self.buff)
            if len(buff) > 10000:
                buff = buff[:10000] + '... [long traceback clipped; more info in the logger]'
            import uthread
            uthread.new(uiMessageFunc, 'ErrSystemError', {'text': buff})
        except:
            pass

        self.buff = []


class Multiplex(object):

    def __init__(self, streams):
        self.streams = streams

    def __del__(self):
        self.flush()

    def write(self, what):
        for each in self.streams:
            each.write(what)

    def flush(self):
        for each in self.streams:
            getattr(each, 'flush', lambda : None)()

    def close(self):
        for each in self.streams:
            getattr(each, 'close', lambda : None)()


postStackTraceAll = None

def RegisterPostStackTraceAll(func):
    global postStackTraceAll
    postStackTraceAll = func


def StackTraceAll(reason = '(no reason stated)'):
    import stackless, traceback2, os, time
    logsFolder = blue.paths.ResolvePath(u'root:') + 'logs'
    if not os.path.exists(logsFolder):
        os.mkdir(logsFolder)
    y, m, wd, d, h, m, s, ms = blue.os.GetTimeParts(blue.os.GetWallclockTime())
    args = (boot.build,
     y,
     m,
     d,
     h,
     m,
     s)
    filename = logsFolder + '/#stacktrace b%d %.4d.%.2d.%.2d %.2d.%.2d.%.2d.txt' % args
    GetChannel('General').Log('Writing out stacktrace at ' + filename, LGERR)
    out = open(filename, 'w')
    out.write('Stack trace of all tasklets as requested: %s\n' % reason)
    out.write('Node ID: %s\n' % getattr(sm.services['machoNet'], 'nodeID', 'unknown'))
    out.write(time.ctime() + '\n\n')
    t = stackless.getcurrent()
    first = t
    no = 1
    while t:
        out.write('Tasklet #%s -------------------------------------------------' % no + '\n')
        no += 1
        if str(t.frame).find('cframe') == -1:
            traceback2.print_stack(t.frame, file=out)
        else:
            out.write('%s\n' % t.frame)
        out.write('\n')
        t = t.next
        if t is None or t == first:
            break

    if postStackTraceAll:
        postStackTraceAll(out)


def Quit(reason = '(no reason stated)'):
    try:
        StackTraceAll(reason)
    except:
        try:
            LogTraceback('Exception in stack-trace-all, shutdown bombing')
        except:
            pass

    try:
        import bluepy
        bluepy.Terminate(reason)
    except ImportError:
        sys.exit(1)


__init__()