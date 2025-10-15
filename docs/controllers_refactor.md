# Refactoring guidance for `release/app/api/controllers.py`

This document captures observations about the current "hairiest" module and outlines
a plan for splitting responsibilities, increasing testability, and isolating side
effects.

## Current pain points

* **Mixed responsibilities in a single file:** `LogController`, `WebhookController`,
  `StreamController`, and `SystemInfoController` all live in the same module even
  though they touch unrelated domains such as database persistence, OS-level screen
  capture, and system metrics collection.【F:release/app/api/controllers.py†L27-L782】
* **`StreamController` combines window discovery, capture, and streaming loops:**
  The class is 500+ lines long and interleaves enumerating windows, applying game-
  specific masks, capturing frames, and handling streaming state transitions.【F:release/app/api/controllers.py†L190-L570】
* **Direct dependencies on global modules and functions:** Win32 API calls, OpenCV,
  and `psutil` usage are hard-coded, making it difficult to stub or mock them in
  tests.【F:release/app/api/controllers.py†L190-L711】
* **Duplication in window enumeration logic:** Enumerating visible windows to find
  processes is repeated in both `find_window_by_process_name` and
  `get_available_programs`, with mostly the same access/error-handling code.【F:release/app/api/controllers.py†L200-L265】【F:release/app/api/controllers.py†L604-L707】

## Suggested module split

1. **`app/controllers/logs.py`**
   * Keep `LogController` focused on orchestrating `LogDataManager` and return DTOs.
   * Move any DTO formatting helpers (e.g., `reverse()` logic) into this module for
     cohesion.【F:release/app/api/controllers.py†L27-L86】

2. **`app/controllers/webhooks.py`**
   * Host `WebhookController` and encapsulate persistence inside a collaborator,
     injected via the constructor so tests can pass an in-memory fake database.
   * Extract validation of required fields (`event`) into a helper to make the
     controller methods smaller.【F:release/app/api/controllers.py†L95-L169】

3. **`app/streaming/` package**
   * `window_finder.py`: Pure functions/classes for enumerating windows and filtering
     by process name. Reuse between finding a specific window and building a list of
     available programs.【F:release/app/api/controllers.py†L200-L265】【F:release/app/api/controllers.py†L604-L707】
   * `capture.py`: Contains `_capture_desktop` and `_capture_normal_window` logic,
     parameterized by dependencies (`win32gui`, `win32ui`, etc.) so tests can inject
     mocks. Keep mask calculation for `yuanshen.exe` separate so other games can
     plug different overlays.【F:release/app/api/controllers.py†L267-L482】
   * `streamer.py`: Focus on the streaming state machine (`generate_frames`,
     `start_stream`, `stop_stream`), delegating actual frame acquisition to the
     capture service and window lookup to the finder. This keeps a small public API
     that Flask views can wire into responses.【F:release/app/api/controllers.py†L484-L582】
   * `programs.py`: Provide the "available programs" listing built on top of the
     finder, returning deduplicated, filtered names.【F:release/app/api/controllers.py†L604-L707】

4. **`app/controllers/system_info.py`**
   * Keep `SystemInfoController`, but expose individual `get_cpu_usage` and
     `get_memory_usage` helpers that operate on a `psutil`-like interface passed in
     by tests.【F:release/app/api/controllers.py†L715-L782】

## Dependency injection & isolation

* Pass lightweight interfaces (protocols or callables) into constructors so that
  tests can supply fakes:
  * `WindowFinder` with `find(process_name)` and `list()` methods used by the
    streamer and the program-list endpoint.【F:release/app/api/controllers.py†L200-L265】【F:release/app/api/controllers.py†L604-L707】
  * `FrameCapture` with `capture(hwnd)` returning `np.ndarray`, hiding whether the
    source is desktop or a window.【F:release/app/api/controllers.py†L267-L482】
  * `SystemMetrics` providing `memory_percent()` and `cpu_percent(interval)` so the
    controller just formats the values.【F:release/app/api/controllers.py†L735-L775】

* Encapsulate global state like `self.hwnd` and `self.is_streaming` inside a small
  streaming session object that owns the generator. Returning a context manager or
  dedicated class makes lifecycle management easier to test.【F:release/app/api/controllers.py†L484-L570】

## Testing strategy

1. **Unit tests with mocks/stubs**
   * Use `pytest` to verify that `LogController` reverses log lists and handles error
     cases by patching a fake `LogDataManager` that raises exceptions.【F:release/app/api/controllers.py†L49-L86】
   * For `WebhookController`, supply a fake database manager and assert that
     validation errors and success paths return the expected dictionaries without
     touching SQLite.【F:release/app/api/controllers.py†L116-L169】
   * Test the mask calculation logic by injecting deterministic window sizes and
     asserting the computed rectangles are clamped correctly (move those calculations
     into pure helper functions first).【F:release/app/api/controllers.py†L433-L470】

2. **Integration-ish tests with dependency injection**
   * Create an in-memory `FrameCapture` stub that yields synthetic frames so the
     streaming generator can be iterated in tests without hitting Win32 APIs.【F:release/app/api/controllers.py†L484-L570】
   * Simulate window enumeration by having the finder return a queue of handles so
     you can test the "window lost, retry" path deterministically.【F:release/app/api/controllers.py†L529-L544】

3. **Contract/acceptance tests for Flask endpoints**
   * After controllers are slimmed down, wire them into Flask blueprints and use
     `FlaskClient` tests to validate JSON payloads and streaming endpoints. With
     injected fakes, these tests can run cross-platform and in CI.

## Incremental refactor steps

1. Move `SystemInfoController` into its own module first—few dependencies, low risk.
2. Extract a `window_utils.py` module containing shared enumeration helpers and make
   both `find_window_by_process_name` and `get_available_programs` call it.
3. Replace direct `win32*` imports with an adapter object passed into
   `StreamController`; migrate `_capture_desktop` and `_capture_normal_window` to the
   adapter.
4. Once the surface area is smaller, split the controllers into separate files and
   update imports in the Flask views.
5. Add `pytest` scaffolding with fixtures for fake managers, capturing 2-3 key
   behaviors per controller to lock in functionality before deeper rewrites.

Following this plan should shrink each module to a focused, testable unit while
keeping behavior unchanged for the API.
