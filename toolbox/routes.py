# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# License: GNU Affero General Public License v3
"""The app routes Toolbox serves, and the prefix it serves them under.

Upstream, Toolbox owns the whole site and its tools sit directly under `/`: `/calculator`, not
`/toolbox/calculator`. On a site that also runs ERPNext that is not an option: the root is the
site's home page, and `/all-tools`, `/weather` and the rest would answer for a host application
that has no idea they exist. So everything here is namespaced under `ROUTE_PREFIX`, and the
site keeps its own root.

A route is named twice below, and the two forms are not interchangeable:

- the *route* (`calculator`, and `/calculator` once `seo` has normalised it) is the application's
  own identity. The tool registry, the content files, the page metadata and the client router all
  speak it, and none of them knows a prefix exists.
- the *path* (`/toolbox/calculator`) is where that route is published. Only this module, the
  Vite base, the manifest and the service worker deal in paths.

`routes.py` is the one place the two are joined, by `route_path` and `strip_prefix`.

The list is explicit on purpose. `resolve_from_map` rewrites a path before any renderer is
chosen (`frappe/website/path_resolver.py`), so a catch-all rule under the prefix would still be
the wrong answer for anything the app does not name. Naming each route keeps Frappe's own pages
reachable, and a tool that is added to the registry without a rule here 404s on a hard refresh.

`frontend/src/data/appRoutes.test.js` fails when this list and the frontend registry disagree,
so adding a tool to one without the other cannot ship.
"""

WEB_PAGE = "toolbox"

# The one path the application owns at the site root: `/toolbox`. Nothing outside it is claimed,
# and `website_user_home_page` is deliberately not set, so the host site keeps its home page.
ROUTE_PREFIX = "/toolbox"

# Pages that are not tools. `all-tools` is absent on purpose: the prefix root *is* the All Tools
# page, so `/toolbox/all-tools` redirects to it rather than serving a second copy.
APP_PAGES = ("about", "data-sources", "settings")

TOOL_ROUTES = (
	"area-converter",
	"audio-editor",
	"audio-recorder",
	"bmi-calculator",
	"bmr-calculator",
	"break-even-calculator",
	"cagr-calculator",
	"calculator",
	"compound-interest-calculator",
	"countdown-timer",
	"currency-converter",
	"data-storage-converter",
	"dictionary",
	"emi-calculator",
	"fuel-consumption-converter",
	"future-value-calculator",
	"gst-calculator",
	"hsn-sac-lookup",
	"ifsc-code-search",
	"length-converter",
	"pace-calculator",
	"pin-code-search",
	"script-conversion",
	"sip-calculator",
	"speed-converter",
	"stopwatch",
	"tdee-calculator",
	"temperature-converter",
	"time-unit-converter",
	"time-zone-converter",
	"timer",
	"volume-converter",
	"weight-converter",
)

APP_ROUTES = (*APP_PAGES, *TOOL_ROUTES)

# A route that no longer exists, and the tool a visitor arriving there should land on instead.
# Most were a tab strip that became separate tools. These are published URLs, so they keep
# working rather than 404.
#
# Each retired route is redirected straight to its replacement, in one hop. A chain of redirects
# costs every old link two round trips, and a search engine discounts a chain.
RETIRED_ROUTES = {
	"financial-calculators": "emi-calculator",
	"unit-converter": "length-converter",
	"health-calculators": "bmi-calculator",
	"india-business-lookup": "pin-code-search",
	# World Clock was removed in #283. The converter reads the same cities and opens on the
	# current moment, so a visitor who saved the clock lands on what they were looking at.
	"world-clock": "time-zone-converter",
}

# A tool that was removed rather than replaced. The site is published, so its URL keeps answering
# rather than turning into a 404 for anyone who saved it. There is no equivalent tool to land on,
# so it goes to All Tools, which is where a visitor can see what is there instead.
REMOVED_ROUTES = ("weather",)


def route_path(route: str) -> str:
	"""Return where `route` is published. A route of `""` is the prefix root itself.

	`PAGES` keys a route with a leading slash and a request path is stripped of one, so both
	shapes arrive here and a route is trimmed before the prefix is put in front of it. Publishing
	`/toolbox//dictionary` would be a URL that answers, and a canonical link and a sitemap entry
	that disagree with the address bar.
	"""
	return f"{ROUTE_PREFIX}/{route.strip('/')}".rstrip("/") or ROUTE_PREFIX


def strip_prefix(path: str) -> str:
	"""Return the route a requested path names, whichever shape the path arrives in.

	Frappe drops the leading slash for a route rule, a visitor's trailing slash names the same
	page, and `toolbox.py` is handed the raw request path. All three land on the same route here,
	and a path outside the prefix is left alone rather than guessed at.
	"""
	prefix = ROUTE_PREFIX.strip("/")
	route = (path or "").strip().strip("/")
	if route == prefix:
		return ""
	if route.startswith(f"{prefix}/"):
		return route[len(prefix) + 1 :]
	return route


def owns_path(path: str) -> bool:
	"""Whether a requested path belongs to Toolbox rather than to the rest of the site.

	The service worker and the security headers both need this: each is registered for the whole
	origin, and a site that also runs ERPNext has paths here that Toolbox has never heard of.
	"""
	if not (path or "").strip().strip("/").startswith(ROUTE_PREFIX.strip("/")):
		# The host site's own root reduces to the same empty route `/toolbox` does, so the prefix
		# has to be what a path is asked for under. `/` belongs to the host application.
		return False
	return route_path(strip_prefix(path)) in SERVED_PATHS


# Every path the application answers for, as it is published. `/toolbox` is the All Tools page and
# is therefore a route like any other, not a prefix that falls through to the home page.
SERVED_PATHS = (ROUTE_PREFIX, *(route_path(route) for route in APP_ROUTES))


def website_route_rules() -> list[dict[str, str]]:
	"""Route every app path to the single web page that boots the client app."""
	return [{"from_route": path, "to_route": WEB_PAGE} for path in SERVED_PATHS]


def website_redirects() -> list[dict[str, object]]:
	"""Keep every published URL working, retired ones included.

	Only paths under the prefix are claimed. The same rules at the site root would redirect a host
	application's pages, which is the one thing namespacing exists to prevent.
	"""

	def permanent(source: str, target: str) -> dict[str, object]:
		return {
			"source": source,
			"target": target,
			"redirect_http_status": 308,
			"forward_query_parameters": True,
		}

	redirects = [permanent(route_path("all-tools"), ROUTE_PREFIX)]

	for retired, replacement in RETIRED_ROUTES.items():
		redirects.append(permanent(route_path(retired), route_path(replacement)))

	for removed in REMOVED_ROUTES:
		redirects.append(permanent(route_path(removed), ROUTE_PREFIX))

	return redirects
