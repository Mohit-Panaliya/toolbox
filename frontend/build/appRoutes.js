// Every route the application serves, in one place on the JavaScript side.
//
// Two build steps need it and neither should own it: the service worker claims an exact route set,
// and the content build rejects a link that points at a route nobody serves. `toolbox/routes.py`
// holds the same list for Frappe, and `frontend/src/data/appRoutes.test.js` fails when the two
// disagree.
//
// These are the application's own routes, not the paths they are published at. The client router
// and the Markdown content files both speak routes, and neither knows a prefix exists. The
// service worker matches on URLs, so it takes `serviceWorkerRoutes` instead.

// The pages that are not tools. `all-tools` is absent on purpose: the All Tools page is the root
// of the application.
export const APP_PAGES = ['/', '/about', '/data-sources', '/settings']

// Where those routes are published. `toolbox/routes.py` owns this value; `appRoutes.test.js` fails
// when the two disagree, and the service worker is wrong on every request when they do.
export const ROUTE_PREFIX = '/toolbox'

export async function appRoutes() {
  const { tools } = await import('../src/data/toolRegistry.js')
  return [...APP_PAGES, ...tools.map((tool) => tool.route)]
}

// The same routes as paths under the prefix, which is the only form a service worker can match.
export async function serviceWorkerRoutes() {
  const routes = await appRoutes()
  return routes.map((route) => (route === '/' ? ROUTE_PREFIX : `${ROUTE_PREFIX}${route}`))
}
