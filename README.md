<div align="center">

<img src="toolbox/public/pwa/toolbox-192.png" alt="" width="96" height="96" />

# Toolbox

Free online calculators, converters and lookups. No account, and nothing stored about you.

[**Upstream project**](https://github.com/frappe/toolbox) &nbsp;·&nbsp; [**frappe.tools**](https://frappe.tools) (upstream's live site) &nbsp;·&nbsp; [![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)

</div>

Toolbox is a Frappe Framework web application of small, focused utilities. Upstream it owns the
whole site, so each tool sat at the site root. **In this repository it is published under a
prefix**, so a tool answers at `/toolbox/calculator` rather than `/calculator`, and the site it is
deployed on keeps its own home page. See [This repository](#this-repository) for what that
required.

The site needs no account. There is no signup, no login, and no user record. Every visitor is a
Guest, and the page renders the same for all of them.

Results are deterministic, and Toolbox uses no AI. Most calculations run in the browser. Toolbox
also states the limits of its data. A fetch time is never shown as a source update time, and
reference data is never labeled "live".

A browser can install Toolbox as a PWA. Then 26 of the 33 tools work with no connection. The four
dataset lookups still need one, and the currency converter falls back to the rates it stored last.

## This repository

A deployment-ready fork of [frappe/toolbox](https://github.com/frappe/toolbox), taken from its
`develop` branch at commit `e332d9f` and modified for two things upstream does not target:

1. **Frappe 16**, where upstream expects Frappe 17.
2. **A site that also runs ERPNext**, so this app may not take the site root.

The `upstream` remote is kept, so `git fetch upstream` and a diff against `upstream/develop` show
exactly what this fork changes and nothing else.

### What changed, and why

| Area | Change | Reason |
|---|---|---|
| Route publication | Every path is published under `/toolbox`, from one list in `toolbox/routes.py` | The site root belongs to ERPNext. A tool answers at `/toolbox/calculator`, never at `/calculator` |
| Home page | `website_user_home_page` is gone; `/toolbox` is an ordinary route rule | That hook is what put the app at `/` upstream. On a shared site it would replace the home page for every user |
| App switcher entry | `app_home` instead of `app_route` | Frappe 16 reads `app_home` and silently ignores the Frappe 17 name |
| DocType controllers | `ToolboxPINRecord` and `ToolboxIFSCRecord` | See the warning below. Upstream's class names make `migrate` **delete both DocTypes** |
| Dataset imports | Falls back to MariaDB `GET_LOCK` / `RELEASE_LOCK` | `frappe.db.advisory_lock` does not exist in Frappe 16, so the import raised `AttributeError` and no dataset ever loaded |
| Content-Security-Policy | Attached only to paths this app serves | `after_request` runs for every response on the site, and a policy describing Toolbox's bundles says nothing true about ERPNext's |
| Sitemap | Toolbox routes **merged** with Frappe's own pages | Replacing the list, as upstream does, would drop every page the host site publishes |
| Service worker | Scope and route set are `/toolbox` | A scope of `/` puts this worker in front of every page on the site, and the first thing it breaks is the host's own offline story |
| Web manifest | `id`, `start_url` and `scope` are `/toolbox/` | A manifest that starts at `/` claims the host's home screen |
| SEO | Canonicals, JSON-LD, sitemap entries and tool links are all built through the prefix | Every published URL has to name the path a browser can actually open |

#### The DocType controller names are load-bearing

Frappe imports a DocType's controller and reads one attribute off it: the class named after the
DocType with its spaces removed. A controller that spells its class any other way is not a
controller as far as the framework is concerned, and the failure is not an error on the page that
needs the DocType. On the next `migrate`, `remove_orphan_doctypes` **deletes the DocType**, and the
table goes with it, and a dataset import then writes into nothing.

`Toolbox HSN Record` spells its class `ToolboxHSNRecord` and is spared, which is what makes this
easy to miss. `toolbox/tests/test_doctype_controllers.py` runs the framework's own check against
every DocType in the app, so a fourth mismatch fails the suite instead of a `migrate`.

### Verified on

Frappe 16.31.0 · ERPNext 16.32.3 · Python 3.14.7 · Node 24 · Yarn 1.22.22 · MariaDB · Redis.

- Frontend: **703 tests pass**.
- Python: **146 unit + 18 integration tests pass**.
- All 37 published routes answer 200, and all 19 assets the page references are served.
- All four datasets import at full size: PIN 165,616 · IFSC 181,719 · HSN 18,687 · Dictionary
  147,982 rows.

## Tools

Toolbox has 33 tools in seven categories. Each tool has its own URL.

| Category | Tools |
|---|---|
| **Calculate** (7) | Calculator · EMI Calculator · Compound Interest Calculator · SIP Calculator · CAGR Calculator · Future Value Calculator · Break-Even Calculator |
| **Convert** (11) | Length Converter · Area Converter · Volume Converter · Weight Converter · Temperature Converter · Speed Converter · Time Unit Converter · Data Storage Converter · Fuel Consumption Converter · Currency Converter · Time Zone Converter |
| **Health** (4) | BMI Calculator · BMR Calculator · TDEE Calculator · Pace Calculator |
| **India** (4) | GST Calculator · HSN & SAC Lookup · PIN Code Search · IFSC Code Search |
| **Time** (3) | Timer · Stopwatch · Countdown Timer |
| **Information** (2) | Dictionary · Script Conversion |
| **Media** (2) | Audio Recorder · Audio Editor |

## What Toolbox stores

Nothing on the server, and almost nothing in the browser.

Preferences use `sessionStorage`, so they end with the browser tab. No tool keeps a record of what
was worked out in it.

Two values use `localStorage`, and only two:

- The theme. It stops a returning dark-mode visitor from seeing a white page first.
- The European Central Bank rate table. It lets the currency converter work on the first offline
  visit of a session.

Both hold public data, and neither one names anybody.

## Data sources

Each dataset-backed tool ships its data through a versioned, checksum-verified manifest, and shows
the "last updated" date of the source itself. The live site lists the same information at
[frappe.tools/data-sources](https://frappe.tools/data-sources).

| Data | Source | License |
|---|---|---|
| PIN codes | Department of Posts, via [data.gov.in](https://www.data.gov.in/catalog/all-india-pincode-directory) | Government Open Data License – India |
| Bank IFSC codes | [Razorpay IFSC](https://github.com/razorpay/ifsc), derived from RBI and NPCI publications | Public domain |
| HSN & SAC codes | CBIC GST classification, compiled by [India Compliance](https://github.com/resilient-tech/india-compliance) | GNU General Public License v3 |
| Dictionary | [Princeton WordNet 3.1](https://wordnet.princeton.edu/) | WordNet License |
| Currency rates | [European Central Bank](https://www.ecb.europa.eu/stats/eurofxref/) | Reference rates, for information only |
| India map outline | [geoBoundaries](https://www.geoboundaries.org/) ADM1 | CC BY 2.5 IN |

The HSN and SAC lookup reads the release that Toolbox imports itself, so it needs no ERPNext or
India Compliance install. The India Compliance project compiles the dataset. It is not a runtime
dependency.

## Installation

The app publishes itself under `/toolbox` on whatever site it is installed on, and the rest of that
site keeps working. Run these from your bench root.

```bash
bench get-app https://github.com/Mohit-Panaliya/toolbox --branch develop
bench --site <site> install-app toolbox
bench --site <site> migrate
```

`migrate` queues `toolbox.dataset_sync.sync_datasets` on the `long` queue, which downloads and
imports all four datasets. On a fresh site that is roughly 21 MB and about 500,000 rows. Watch it
finish:

```bash
bench --site <site> execute toolbox.dataset_sync.sync_datasets
```

That call is safe to repeat. A dataset whose pinned version is already Active is skipped, so it
does no downloads, and running it by hand is the way to confirm the queue job succeeded:

```json
{"synced": [], "skipped": ["Dictionary", "HSN", "IFSC", "PIN"], "failed": []}
```

Then build the assets, so the app's bundle and icons are in Frappe's manifest:

```bash
bench build --app toolbox
```

### Restart the site after installing

Adding the app to `sites/apps.txt` is not enough for a bench that is already running. Frappe fixes
each process's import path at startup, so a web or worker process that predates the install cannot
import the app, and `get_boot_data()` imports the hooks of every installed app for every page
render. The symptom is **every** page on the site answering 500 with
`ModuleNotFoundError: No module named 'toolbox.hooks'`, ERPNext's own pages included.

Restart the web and worker processes after `install-app`. Sites that do not have the app installed
are unaffected, so a multi-site bench only needs the ones that do.

If pages start returning 404 straight after a restart, the earlier 500 window cached them. Clear it:

```bash
bench --site <site> clear-website-cache
```

## Development

Run these commands from `apps/toolbox`.

```bash
yarn install
yarn dev            # Vite dev server
yarn build          # production assets
yarn test           # frontend unit tests (Vitest)
yarn test:e2e       # browser tests (Playwright)
yarn verify         # Vitest, build, Python tests, then Playwright
```

Run the Python tests from the bench root, and read the next section first.

```bash
bench --site <site> run-tests --app toolbox
```

### Run the Python tests on a throwaway site, never on a site with data

This is not a style preference. The integration tests import small releases of their own into the
**same tables** the production datasets live in, and a test asserts that activating a release prunes
every other one. Run the suite against a site that holds an imported dataset and it will truncate
all four of them:

```bash
# On pd.localhost, after the integration tests: 0 rows in all four tables.
bench --site pd.localhost mariadb -e \
  "select (select count(*) from \`tabToolbox PIN Record\`) pin,
          (select count(*) from \`tabToolbox IFSC Record\`) ifsc;"
#   pin  ifsc
#     0     0
```

There is no undo. The import has to run again, and it is cheap only because the datasets are
publicly downloadable, checksum-verified releases.

Give the suite a site of its own:

```bash
bench new-site toolbox-test.localhost        # needs the hostname to resolve
bench --site toolbox-test.localhost install-app toolbox
bench --site toolbox-test.localhost migrate
bench --site toolbox-test.localhost run-tests --app toolbox
```

`sync_datasets` is idempotent, so restoring a site that was wiped is the same command as importing
it the first time. Let any queued import finish before running the tests either way: an import
holds row locks that the integration tests wait for, and the failure reads as
`QueryTimeoutError (1205) Lock wait timeout exceeded` after about 150 seconds.

### Smoke-testing a deployment

```bash
# Every published route answers, and the host site's own pages still do.
for p in /toolbox /toolbox/dictionary /login /; do
  printf "%-24s %s\n" "$p" "$(curl -s -o /dev/null -w '%{http_code}' -H "Host: <site>" "http://127.0.0.1:8000$p")"
done

# A public endpoint answers a guest with real data.
curl -s -H "Host: <site>" \
  "http://127.0.0.1:8000/api/method/toolbox.india_business.search_pin?query=110001"

# A write verb is refused.
curl -s -o /dev/null -w '%{http_code}\n' -X POST -H "Host: <site>" \
  "http://127.0.0.1:8000/api/method/toolbox.india_business.search_pin?query=110001"
```

The dataset-backed endpoints take their argument as `query`. `dictionary.lookup` takes `word`.
Asking for the wrong name returns a 500 `TypeError` from argument validation, not a 400.

Run the full Playwright matrix on its own. Two matrices at once, or one beside a build, starve the
single web server, and every test then fails on a navigation timeout that reads like a real
regression.

The application icons are generated, not drawn by hand. Run `python scripts/generate_icons.py`
after any change to the geometry, then `python scripts/build_og_card.py` to rebuild the social
card from the new 512px icon.

## Contributing

This app uses `pre-commit` for formatting and linting. [Install
pre-commit](https://pre-commit.com/#installation) and enable it:

```bash
cd apps/toolbox
pre-commit install
```

Ruff formats and lints the Python. ESLint checks the JavaScript and Vue files.

Do not run `pre-commit run --all-files`. It includes the Prettier hook, and the installed version
reformats the whole frontend against its own conventions. Run one hook at a time instead:

```bash
pre-commit run ruff --all-files
pre-commit run ruff-format --all-files
pre-commit run eslint --all-files
```

Write JavaScript and Vue with single quotes, no semicolons, and two-space indentation.

## License

[GNU Affero General Public License v3.0](license.txt)

Toolbox is the work of [Frappe Technologies](https://frappe.io) and its contributors, and this
repository is a fork of it rather than a new work. The original copyright headers and the license
are unchanged, and the source of every change is the `upstream` remote:

```bash
git fetch upstream
git diff upstream/develop...HEAD        # exactly what this fork changes
```

## Attribution

The datasets keep their own terms, and this fork does not change any of them. PIN codes are
Department of Posts data under the Government Open Data License – India. IFSC codes come from
[Razorpay IFSC](https://github.com/razorpay/ifsc), derived from RBI and NPCI publications, and are
public domain. HSN and SAC codes are the CBIC classification compiled by
[India Compliance](https://github.com/resilient-tech/india-compliance) under GPL v3. The dictionary
is [Princeton WordNet 3.1](https://wordnet.princeton.edu/) under the WordNet License. Currency
rates are European Central Bank reference rates, for information only.
