# Refactoring plan for `website/app/webinfo/page.tsx`

## Pain points in the current implementation

* The page component maintains three separate slices of state (`state`, `streamState`, and `systemInfo`), each with bespoke request logic and notification handling. The network code is duplicated and tightly coupled to React rendering, which makes it hard to reuse and to exercise independently in tests. 【F:website/app/webinfo/page.tsx†L20-L198】
* Side-effects such as polling, visibility handling, and stream teardown live directly inside the page component, mixing control-flow with JSX and making it difficult to see the rendering structure at a glance. 【F:website/app/webinfo/page.tsx†L200-L338】
* The JSX tree interleaves business logic (e.g., selecting programs, formatting system information, producing error notifications) with layout concerns. This leads to a nearly 900-line component that is hard to maintain, change, or reason about. 【F:website/app/webinfo/page.tsx†L340-L752】

## Suggested decomposition

1. **Extract data hooks**
   * Create custom hooks in `website/hooks/` (or `website/app/webinfo/hooks/`) such as `useWebhookEvents(limit)`, `useProgramStream()`, and `useSystemMetrics()`. These hooks encapsulate fetching, polling, and notification throttling so that the page component only consumes their state. The duplicated try/catch branches collapse into helper utilities that the hooks can share (e.g., a `useApiRequest` wrapper that only fires notifications once per error type). 【F:website/app/webinfo/page.tsx†L56-L198】
   * Expose imperative actions (start/stop stream, refresh data) from the hooks, returning stable callbacks. The component then wires buttons or effects to these callbacks without needing to know about `apiService` details.

2. **Split presentation into focused components**
   * Move the streaming UI into `<VideoStreamPanel>` which accepts props like `{ state, onProgramSelect, onRefresh, onStop }`. This component can live under `website/app/webinfo/components/VideoStreamPanel.tsx` and contain all the layout and conditional rendering currently around lines 360–620. 【F:website/app/webinfo/page.tsx†L340-L620】
   * Encapsulate the right-hand sidebar (current status, filters) in `<WebInfoSidebar>` and the filters/search inputs in `<WebInfoFilters>` so they can be reused elsewhere and unit-tested in isolation. 【F:website/app/webinfo/page.tsx†L620-L752】
   * Extract reusable UI bits—`getEventIcon`, `getEventColor`, and `formatTimestamp`—into a dedicated utility module (`website/lib/webinfo-utils.ts`) to reduce the surface area of the page component and make the logic more discoverable. 【F:website/app/webinfo/page.tsx†L20-L110】

3. **Introduce a declarative streaming controller**
   * Replace the manual `isStreaming` bookkeeping with a reducer or a lightweight state machine (e.g., XState or a hand-rolled discriminated union) that covers `idle`, `connecting`, `streaming`, `error`, and `stopped` states. This will simplify the `start/stop` logic and avoid repeated `setStreamState` spreads across the component. 【F:website/app/webinfo/page.tsx†L120-L226】【F:website/app/webinfo/page.tsx†L340-L540】
   * Encapsulate notification deduplication (`errorShownRef`) inside the streaming hook or state machine so the component does not manage mutable refs directly. 【F:website/app/webinfo/page.tsx†L112-L138】

4. **Separate layout from data orchestration**
   * Keep `page.tsx` as a thin orchestrator that composes hooks and components. It should roughly look like:
     ```tsx
     export default function WebInfoPage() {
       const webhook = useWebhookEvents(limit)
       const stream = useProgramStream()
       const system = useSystemMetrics()

       return (
         <PageLayout>
           <VideoStreamPanel {...stream} system={system} />
           <WebInfoSidebar
             filters={webhook.filters}
             onFilterChange={webhook.setFilters}
             latestEvent={webhook.latestEvent}
           />
           <WebhookTable events={webhook.filteredEvents} />
         </PageLayout>
       )
     }
     ```
   * The extracted children handle their own markup, making it straightforward to understand where to edit layout or logic.

## Testing strategy

* **Hook-level tests**: Use `@testing-library/react`'s `renderHook` (or `@testing-library/react-hooks`) together with MSW to stub the API routes. Assert that each hook handles success, failure, and polling behavior correctly without involving DOM rendering. 【F:website/app/webinfo/page.tsx†L140-L248】
* **Component tests**: For components like `<VideoStreamPanel>`, render them with mocked props and verify conditional rendering (loading states, error banners, select options) using React Testing Library. This ensures layout and messaging stay consistent when styles change. 【F:website/app/webinfo/page.tsx†L360-L620】
* **Integration tests**: Write a happy-path test for the page that mounts the orchestrating component with MSW handlers to confirm the hooks and presentation integrate correctly (stream auto-start, filters updating the table, etc.).
* **End-to-end coverage**: If you have Playwright or Cypress, simulate user flows—changing program selections, tab visibility, and filter inputs—to verify that the lifecycle hooks (visibility listeners, cleanup) behave as expected. 【F:website/app/webinfo/page.tsx†L248-L338】

## Isolation and maintainability improvements

* Move the API client (`apiService`) usage behind a narrow interface exported by a `webinfo.service.ts` module so the hooks receive dependency-injected functions. This makes it trivial to substitute fakes in tests and to adopt caching libraries like React Query later.
* Centralize notification behavior in a `useOneShotNotification` helper that tracks which error categories have been shown, eliminating the need for the component-level `useRef` bookkeeping. 【F:website/app/webinfo/page.tsx†L112-L138】
* Define TypeScript types that model the domain (webhook event, system metrics, streaming session) in `website/types/` and import them into both hooks and components. This avoids circular dependencies on page-level types when more screens reuse the same data structures.

Following these steps should shrink `page.tsx` to a declarative wrapper, make side-effects testable, and pave the way for future features (e.g., alternate streaming sources, richer filtering) without ballooning the component further.
