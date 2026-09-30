# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# License: GNU Affero General Public License v3
"""One import at a time, from the first row to the commit.

The lock is a MariaDB `GET_LOCK`. It belongs to the database session, not to the transaction, so it
is released the moment the `with` block ends. An importer that returns without committing
therefore drops the lock while its rows are still uncommitted and still holding their row locks. A
second import then takes the lock, believes it is alone, and blocks on rows the first import has
not finished writing.

Holding the lock until the commit closes that window. Every dataset importer takes its lock through
this, so the rule has one home rather than five.

Frappe 17 wraps `GET_LOCK` as `frappe.db.advisory_lock`. Frappe 16 has no such helper, so this
module asks MariaDB directly when it is missing. Both paths are the same lock on the same session,
and the importer cannot tell which one it got.
"""

from contextlib import contextmanager

import frappe

# Long enough that a second import waits through a slow batch, short enough that a caller learns
# quickly rather than hanging.
LOCK_TIMEOUT = 30


@contextmanager
def dataset_import_lock(key: str, timeout: int = LOCK_TIMEOUT):
	"""Hold `key` until the work inside has been committed.

	The commit runs on the way out, so it happens while the lock is still held. A failing import
	commits nothing here: it raises through this, and the importer has already recorded the
	failure and committed that.
	"""
	advisory_lock = _framework_lock()
	if advisory_lock is not None:
		with advisory_lock(key, timeout=timeout):
			yield
			frappe.db.commit()
		return

	if not _acquire(key, timeout):
		raise TimeoutError(
			f"Another dataset import holds {key}. Waited {timeout}s and gave up rather than "
			"importing two releases at once."
		)

	try:
		yield
		frappe.db.commit()
	finally:
		frappe.db.sql("SELECT RELEASE_LOCK(%s)", (key,))


def _framework_lock():
	"""Frappe's own wrapper around `GET_LOCK`, on a Frappe that has one.

	One function so the version check is a single place, and so a test can stand in for a Frappe
	that does not have it without reaching into the framework to delete an attribute.
	"""
	return getattr(frappe.db, "advisory_lock", None)


def _acquire(key: str, timeout: int) -> bool:
	"""Take the named MariaDB lock, and report whether it was taken.

	`GET_LOCK` answers 1 when the lock was granted, 0 when it timed out, and NULL on an error, so
	the answer is read as one. The lock lives on the connection, which is the connection the release
	goes back through, so this is one lock and not two.
	"""
	(acquired,) = frappe.db.sql("SELECT GET_LOCK(%s, %s)", (key, timeout))[0]
	return bool(acquired)
