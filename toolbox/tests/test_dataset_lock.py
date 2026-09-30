# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# License: GNU Affero General Public License v3

from contextlib import contextmanager
from unittest.mock import patch

import frappe
from frappe.tests import UnitTestCase

from toolbox import dataset_lock, dictionary_data, hsn_data, india_business_data
from toolbox.dataset_lock import LOCK_TIMEOUT, dataset_import_lock

IMPORT_MODULES = (dictionary_data, hsn_data, india_business_data)

# Frappe 17 has `frappe.db.advisory_lock`; Frappe 16 does not. `create=True` lets this suite pin
# the helper on a version that lacks it, so the rules below are tested on both.
ADVISORY_LOCK = {"create": True}


@contextmanager
def recorded_lock(events, key, timeout=None):
	"""Stand in for the advisory lock and record when it is taken and given back."""
	events.append(("acquire", key, timeout))
	try:
		yield
	finally:
		events.append(("release", key, None))


class TestDatasetImportLock(UnitTestCase):
	"""An importer holds its lock until its rows are committed.

	A lock released before the commit leaves the rows uncommitted and still holding their row
	locks, so a second import takes the lock, believes it is alone, and blocks on them.
	"""

	def run_lock(self, body):
		events = []

		def fake_lock(key, timeout=None):
			return recorded_lock(events, key, timeout)

		with patch.object(frappe.db, "advisory_lock", side_effect=fake_lock, **ADVISORY_LOCK):
			with patch.object(frappe.db, "commit", side_effect=lambda: events.append(("commit", None, None))):
				body(events)
		return [event[0] for event in events]

	def test_the_commit_happens_before_the_lock_is_released(self):
		def body(events):
			with dataset_import_lock("toolbox:test-dataset-import"):
				events.append(("work", None, None))

		self.assertEqual(self.run_lock(body), ["acquire", "work", "commit", "release"])

	def test_a_failing_import_commits_nothing_here(self):
		"""The importer records its own failure and commits that. This adds no second commit."""

		def body(events):
			with self.assertRaises(ValueError):
				with dataset_import_lock("toolbox:test-dataset-import"):
					raise ValueError("the dataset contains no valid records")

		self.assertEqual(self.run_lock(body), ["acquire", "release"])

	def test_the_lock_carries_a_timeout(self):
		"""Without one, a second import waits forever rather than reporting that it cannot run."""
		captured = []

		@contextmanager
		def fake_lock(key, timeout=None):
			captured.append(timeout)
			yield

		with patch.object(frappe.db, "advisory_lock", side_effect=fake_lock, **ADVISORY_LOCK):
			with patch.object(frappe.db, "commit"):
				with dataset_import_lock("toolbox:test-dataset-import"):
					pass

		self.assertEqual(captured, [LOCK_TIMEOUT])


class TestDatasetImportLockWithoutTheHelper(UnitTestCase):
	"""The same lock, taken from MariaDB, for a Frappe that has no `advisory_lock`.

	Frappe 16 has no `frappe.db.advisory_lock`, and the helper is the only thing upstream uses, so
	without this the import raises `AttributeError` and no dataset is ever loaded.
	"""

	def run_without_the_helper(self, body, acquired=1):
		events = []

		def sql(statement, values=()):
			# The statement is parameterised, so its verb carries the placeholder list with it.
			# `GET_LOCK(%s,` is the verb `GET_LOCK`; the values are asserted separately.
			verb = statement.split()[1].upper().split("(")[0]
			events.append(("sql", verb, values))
			return ((acquired,),) if "GET_LOCK" in statement else ()

		with patch.object(dataset_lock, "_framework_lock", return_value=None):
			with patch.object(frappe.db, "sql", side_effect=sql):
				with patch.object(frappe.db, "commit", side_effect=lambda: events.append(("commit", None, None))):
					body(events)
		return events

	def test_it_commits_while_the_lock_is_held_and_releases_it_after(self):
		def body(events):
			with dataset_import_lock("toolbox:test-dataset-import", timeout=7):
				events.append(("work", None, None))

		events = self.run_without_the_helper(body)

		self.assertEqual(
			[(event[0], event[1]) for event in events],
			[("sql", "GET_LOCK"), ("work", None), ("commit", None), ("sql", "RELEASE_LOCK")],
		)
		self.assertEqual(events[0][2], ("toolbox:test-dataset-import", 7))
		self.assertEqual(events[-1][2], ("toolbox:test-dataset-import",))

	def test_a_lock_it_cannot_take_says_so_rather_than_importing_anyway(self):
		def body(events):
			with dataset_import_lock("toolbox:test-dataset-import", timeout=1):
				events.append(("work", None, None))

		with self.assertRaises(TimeoutError):
			self.run_without_the_helper(body, acquired=0)

	def test_a_failing_import_gives_the_lock_back(self):
		def body(events):
			with self.assertRaises(ValueError):
				with dataset_import_lock("toolbox:test-dataset-import"):
					raise ValueError("the dataset contains no valid records")

		events = self.run_without_the_helper(body)

		self.assertEqual([event[0] for event in events], ["sql", "sql"])
		self.assertEqual(events[-1][1], "RELEASE_LOCK")


class TestEveryImporterTakesTheLock(UnitTestCase):
	"""Five importers, one rule. A new one that takes the raw lock is the regression."""

	def test_no_importer_holds_the_raw_advisory_lock(self):
		for module in IMPORT_MODULES:
			with self.subTest(module=module.__name__):
				source = frappe.read_file(module.__file__)
				self.assertNotIn("frappe.db.advisory_lock", source)
				self.assertIn("dataset_import_lock", source)
