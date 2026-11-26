"""Apply a process memory cap before starting an experiment CLI."""
import os


def limit_process_memory(max_bytes):
    if os.name != "nt":
        import resource
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        bounds = [bound for bound in (max_bytes, soft, hard) if bound != resource.RLIM_INFINITY]
        limit = min(bounds)
        resource.setrlimit(resource.RLIMIT_AS, (limit, hard))
        return "RLIMIT_AS"

    import ctypes
    from ctypes.wintypes import BOOL, DWORD, HANDLE

    size = ctypes.c_size_t

    class BasicLimits(ctypes.Structure):
        _fields_ = [
            ("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
            ("flags", DWORD), ("min_working_set", size), ("max_working_set", size),
            ("active_processes", DWORD), ("affinity", size),
            ("priority", DWORD), ("scheduling", DWORD),
        ]

    class ExtendedLimits(ctypes.Structure):
        _fields_ = [
            ("basic", BasicLimits), ("io", ctypes.c_uint64 * 6),
            ("process_memory", size), ("job_memory", size),
            ("peak_process", size), ("peak_job", size),
        ]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    kernel.CreateJobObjectW.restype = HANDLE
    kernel.SetInformationJobObject.argtypes = [HANDLE, ctypes.c_int, ctypes.c_void_p, DWORD]
    kernel.SetInformationJobObject.restype = BOOL
    kernel.GetCurrentProcess.restype = HANDLE
    kernel.AssignProcessToJobObject.argtypes = [HANDLE, HANDLE]
    kernel.AssignProcessToJobObject.restype = BOOL
    kernel.CloseHandle.argtypes = [HANDLE]
    kernel.CloseHandle.restype = BOOL
    job = kernel.CreateJobObjectW(None, None)
    if not job:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        limits = ExtendedLimits()
        limits.basic.flags = 0x100  # JOB_OBJECT_LIMIT_PROCESS_MEMORY
        limits.process_memory = max_bytes
        if not kernel.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())
        if not kernel.AssignProcessToJobObject(job, kernel.GetCurrentProcess()):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        kernel.CloseHandle(job)
    return "Windows Job Object process commit limit"
