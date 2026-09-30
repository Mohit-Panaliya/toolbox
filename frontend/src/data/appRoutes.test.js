import { readFileSync } from 'node:fs'
import path from 'node:path'

import { describe, expect, it } from 'vitest'

import { APP_PAGES, ROUTE_PREFIX, appRoutes, serviceWorkerRoutes } from '../../build/appRoutes.js'
import { readAppRoutes } from '../../build/pwaBuildPlugin.js'
import { tools } from './toolRegistry'

// Four places have to agree on what the app serves, and none of them imports the others:
//
//   1. `toolRegistry.js` — the source of truth for the routes.
//   2. `toolbox/routes.py` — the Frappe route rules. These are an explicit list rather than a
//      catch-all, because a catch-all would swallow pages belonging to the other apps on the site.
//   3. `frontend/build/appRoutes.js` — the prefix those routes are published under.
//   4. The service worker's route set, injected at build time.
//
// A tool added to the registry without a rule in routes.py 404s on a hard refresh, while the SPA
// still navigates to it fine from inside the app. A prefix that disagrees between the router, the
// manifest and the worker is worse: the app loads and then 404s every navigation.
const routesPy = readFileSync(
  path.resolve(import.meta.dirname, '../../../toolbox/routes.py'),
  'utf8',
)

function pythonTuple(name) {
  const block = routesPy.match(new RegExp(`${name} = \\(([\\s\\S]*?)\\)`))
  if (!block) throw new Error(`${name} not found in toolbox/routes.py`)
  return [...block[1].matchAll(/"([^"]+)"/g)].map((match) => match[1])
}

function pythonString(name) {
  const match = routesPy.match(new RegExp(`${name} = "([^"]+)"`))
  if (!match) throw new Error(`${name} not found in toolbox/routes.py`)
  return match[1]
}

describe('app routes agree across the registry, Frappe, and the service worker', () => {
  it('routes.py lists exactly the registry tools', () => {
    expect(pythonTuple('TOOL_ROUTES').sort()).toEqual(
      tools.map((tool) => tool.route.slice(1)).sort(),
    )
  })

  it('routes.py and the build agree on the pages that are not tools', () => {
    // `all-tools` is absent, because the All Tools page is the root of the application.
    expect(pythonTuple('APP_PAGES')).toEqual(['about', 'data-sources', 'settings'])
    expect(APP_PAGES).toEqual(['/', ...pythonTuple('APP_PAGES').map((page) => `/${page}`)])
  })

  it('the prefix is the one Frappe publishes the routes under', () => {
    expect(ROUTE_PREFIX).toBe(pythonString('ROUTE_PREFIX'))
  })

  it('the routes the app speaks stay free of the prefix', async () => {
    // The client router, the content files and the registry are the application's own vocabulary.
    // Prefixing them here would put a prefix in three places that must not know about one.
    for (const route of await appRoutes()) {
      expect(route.startsWith(ROUTE_PREFIX)).toBe(false)
    }
  })

  it('the service worker claims every app route and nothing of the host site', async () => {
    const swRoutes = await readAppRoutes()

    for (const route of await appRoutes()) {
      expect(swRoutes).toContain(route === '/' ? ROUTE_PREFIX : `${ROUTE_PREFIX}${route}`)
    }

    // Claiming these would hand the other apps on this site the Toolbox shell.
    for (const reserved of ['/app', '/login', '/api', '/assets', '/files', '/', '/desk']) {
      expect(swRoutes).not.toContain(reserved)
    }
  })

  it('the worker route set is the application routes under the prefix', async () => {
    const routes = await appRoutes()

    expect(await serviceWorkerRoutes()).toEqual(
      routes.map((route) => (route === '/' ? ROUTE_PREFIX : `${ROUTE_PREFIX}${route}`)),
    )
  })
})
