import frappe
from frappe.website.router import get_pages

from toolbox import seo

no_cache = 1
base_template_path = "www/sitemap.xml"


def get_context(context):
	"""List every Toolbox page a crawler should fetch, and the host site's own pages.

	Upstream, this replaced Frappe's sitemap outright, because on a site that is all Toolbox
	exists the stock `/about` and `/contact` are worse than nothing. Here it shares an origin with
	ERPNext, so replacing the list would drop every page the host application publishes. The two
	are therefore merged: Toolbox's routes first, then Frappe's own pages, each URL once.

	There is no `lastmod`. Frappe's sitemap stamps every entry with today's date, which tells a
	crawler that all of these pages changed today, every day. A date that is always wrong is
	worse than no date: a crawler that stops trusting it discounts the real ones later.
	"""
	base_url = frappe.utils.get_url()
	links = [seo.route_url(base_url, route) for route in seo.indexable_routes()]
	seen = set(links)

	for page in get_pages().values():
		if not page.sitemap:
			continue
		link = frappe.utils.get_url(frappe.utils.quote(page.name.encode("utf-8")))
		if link not in seen:
			seen.add(link)
			links.append(link)

	return {"links": links}
