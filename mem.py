from ctypes import *
from ctypes.wintypes import *
from collections import namedtuple

__all__ = ['query_working_set', 'working_set_size']

kernel32 = WinDLL('kernel32', use_last_error=True)
psapi = WinDLL('psapi', use_last_error=True)

PROCESS_VM_READ           = 0x0010
PROCESS_QUERY_INFORMATION = 0x0400

ERROR_ACCESS_DENIED = 0x0005
ERROR_BAD_LENGTH    = 0x0018

ULONG_PTR = WPARAM
SIZE_T = c_size_t

class PSAPI_WORKING_SET_BLOCK(Union):
    class _FLAGS(Structure):
        _fields_ = (('Protection',  ULONG_PTR,  5),
                    ('ShareCount',  ULONG_PTR,  3),
                    ('Shared',      ULONG_PTR,  1),
                    ('Reserved',    ULONG_PTR,  3),
                    ('VirtualPage', ULONG_PTR, 20))
    _anonymous_ = '_flags',
    _fields_ = (('Flags', ULONG_PTR),
                ('_flags', _FLAGS))

class PSAPI_WORKING_SET_INFORMATION(Structure):
    _fields_ = (('NumberOfEntries',  ULONG_PTR),
                ('_WorkingSetInfo', PSAPI_WORKING_SET_BLOCK * 1))
    @property
    def WorkingSetInfo(self):
        array_t = PSAPI_WORKING_SET_BLOCK * self.NumberOfEntries
        offset = PSAPI_WORKING_SET_INFORMATION._WorkingSetInfo.offset
        return array_t.from_buffer(self, offset)

PPSAPI_WORKING_SET_INFORMATION = POINTER(PSAPI_WORKING_SET_INFORMATION)

def errcheck_bool(result, func, args):
    if not result:
        raise WinError(get_last_error())
    return args

psapi.QueryWorkingSet.errcheck = errcheck_bool
psapi.QueryWorkingSet.argtypes = (
    HANDLE,                         # _In_  hProcess
    PPSAPI_WORKING_SET_INFORMATION, # _Out_ pv
    DWORD)                          # _In_  cb

kernel32.GetCurrentProcess.restype = HANDLE

kernel32.OpenProcess.errcheck = errcheck_bool
kernel32.OpenProcess.restype = HANDLE
kernel32.OpenProcess.argtypes = (
    DWORD, # _In_ dwDesiredAccess
    BOOL,  # _In_ bInheritHandle
    DWORD) # _In_ dwProcessId

def query_working_set(pid=None):
    """Return the PSAPI_WORKING_SET_BLOCK array for the target process."""
    if pid is None:
        hprocess = kernel32.GetCurrentProcess()
    else:
        access = PROCESS_VM_READ | PROCESS_QUERY_INFORMATION
        hprocess = kernel32.OpenProcess(access, False, pid)
    info = PSAPI_WORKING_SET_INFORMATION()
    base_size = sizeof(info)
    item_size = sizeof(PSAPI_WORKING_SET_BLOCK)
    overshoot = 0
    while True:
        overshoot += 4096
        n = info.NumberOfEntries + overshoot
        resize(info, base_size + n * item_size)
        try:
            psapi.QueryWorkingSet(hprocess, byref(info), sizeof(info))
            break
        except OSError as e:
            if e.winerror != ERROR_BAD_LENGTH:
                raise
    return info.WorkingSetInfo

class PERFORMANCE_INFORMATION(Structure):
    _fields_ = (('cb',                DWORD),
                ('CommitTotal',       SIZE_T),
                ('CommitLimit',       SIZE_T),
                ('CommitPeak',        SIZE_T),
                ('PhysicalTotal',     SIZE_T),
                ('PhysicalAvailable', SIZE_T),
                ('SystemCache',       SIZE_T),
                ('KernelTotal',       SIZE_T),
                ('KernelPaged',       SIZE_T),
                ('KernelNonpaged',    SIZE_T),
                ('PageSize',          SIZE_T),
                ('HandleCount',       DWORD),
                ('ProcessCount',      DWORD),
                ('ThreadCount',       DWORD))
    def __init__(self, *args, **kwds):
        super(PERFORMANCE_INFORMATION, self).__init__(*args, **kwds)
        self.cb = sizeof(self)

PPERFORMANCE_INFORMATION = POINTER(PERFORMANCE_INFORMATION)

psapi.GetPerformanceInfo.errcheck = errcheck_bool
psapi.GetPerformanceInfo.argtypes = (
    PPERFORMANCE_INFORMATION, # _Out_ pPerformanceInformation
    DWORD)                    # _In_  cb

WorkingSetSize = namedtuple('WorkingSetSize', 'total shared private')

def working_set_size(pid=None):
    """Return the total, shared, and private working set sizes
       for the target process.
    """
    wset = query_working_set(pid)
    pinfo = PERFORMANCE_INFORMATION()
    psapi.GetPerformanceInfo(byref(pinfo), sizeof(pinfo))
    pagesize = pinfo.PageSize        
    total = len(wset) * pagesize
    shared = sum(b.Shared for b in wset) * pagesize
    private = total - shared
    return WorkingSetSize(total, shared, private)