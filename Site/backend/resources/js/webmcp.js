import { nextTick } from 'vue'

export function registerWorkspaceTools({ events, current, selectEvent, leftId, rightId, loadComparison, comparison }) {
  const context = document.modelContext
  if (!context?.registerTool) return () => {}
  const lifecycle = new AbortController()
  const register = tool => {
    try { Promise.resolve(context.registerTool(tool, { signal: lifecycle.signal })).catch(() => {}) } catch {}
  }
  register({
    name: 'read_prism_events', title: '讀取目前事件清單',
    description: 'Read the events in the currently selected real-news or demonstration dataset. Does not change the page.',
    inputSchema: {type: 'object', properties: {}, additionalProperties: false},
    annotations: {readOnlyHint: true, untrustedContentHint: true},
    execute: input => {
      if (!input || Object.keys(input).length) throw new Error('No arguments are accepted.')
      return events.value.map(e => ({id: e.id, title: e.title, articleCount: e.articles_count, isDemo: e.is_demo}))
    }
  })
  register({
    name: 'navigate_prism_comparison', title: '開啟同事件的文章比較',
    description: 'Select an event and two distinct articles in the current dataset, update the visible comparison, and return its result. Does not modify saved annotations.',
    inputSchema: {type: 'object', properties: {eventId: {type: 'integer'}, leftId: {type: 'integer'}, rightId: {type: 'integer'}}, required: ['eventId', 'leftId', 'rightId'], additionalProperties: false},
    annotations: {readOnlyHint: false, untrustedContentHint: true},
    async execute(input) {
      if (!input || !['eventId', 'leftId', 'rightId'].every(k => Number.isInteger(input[k])) || Object.keys(input).length !== 3 || input.leftId === input.rightId || !events.value.some(e => e.id === input.eventId)) throw new Error('Choose an existing event and two distinct article IDs.')
      // Validate membership before changing visible state.
      const response = await fetch(`/api/events/${input.eventId}`, {headers: {Accept: 'application/json'}})
      if (!response.ok) throw new Error('Event unavailable.')
      const event = await response.json()
      if (![input.leftId, input.rightId].every(id => event.articles.some(a => a.id === id))) throw new Error('Both articles must belong to this event.')
      await selectEvent(input.eventId)
      if (current.value?.id !== input.eventId) throw new Error('Event could not be loaded.')
      leftId.value = input.leftId; rightId.value = input.rightId
      await nextTick()
      await loadComparison()
      return {eventId: current.value.id, ...comparison.value}
    }
  })
  return () => lifecycle.abort()
}
