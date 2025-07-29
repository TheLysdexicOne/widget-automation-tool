import win32gui
import win32process
import time

target_title = "WidgetInc"  # Use a partial window title

# Sliding cache (2 second timeout)
pid_cache = {}
CACHE_TTL = 2  # seconds


def find_pid_by_window_title(title_part):
    def enum_callback(hwnd, result):
        if win32gui.IsWindowVisible(hwnd):
            window_title = win32gui.GetWindowText(hwnd)
            if title_part.lower() in window_title.lower():
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                result.append((pid, window_title))

    results = []
    win32gui.EnumWindows(enum_callback, results)
    return results


# Cache lookup: refresh cache and TTL on every access
def get_pid_with_cache(title_part):
    now = time.time()
    cache_entry = pid_cache.get(title_part)

    if cache_entry:
        pid, last_used = cache_entry
        if now - last_used < CACHE_TTL:
            # Refresh TTL
            pid_cache[title_part] = (pid, now)
            return pid

    # Cache miss or expired: re-fetch
    results = find_pid_by_window_title(title_part)
    if results:
        pid = results[0][0]
        pid_cache[title_part] = (pid, now)
        return pid
    return None


# --- Measure Uncached ---
start = time.perf_counter()
uncached_result = find_pid_by_window_title(target_title)  # NO cache update
elapsed_uncached = time.perf_counter() - start

# --- Measure Cached ---
start = time.perf_counter()
cached_pid = get_pid_with_cache(target_title)
elapsed_cached = time.perf_counter() - start

# --- Output ---
if uncached_result:
    print(f"Uncached PID lookup: {uncached_result[0][0]} in {elapsed_uncached:.6f} sec")
else:
    print("Uncached PID lookup: Not found")

if cached_pid:
    print(f"Cached PID lookup:   {cached_pid} in {elapsed_cached:.6f} sec")
else:
    print("Cached PID lookup: Not found")
