# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# License: GNU Affero General Public License v3

import frappe
from frappe.model.base_document import import_controller
from frappe.tests import UnitTestCase

DOCTYPES = (
	"Toolbox Dataset Release",
	"Toolbox Dictionary Entry",
	"Toolbox HSN Record",
	"Toolbox IFSC Record",
	"Toolbox PIN Record",
)


class TestDocTypeControllers(UnitTestCase):
	"""Every DocType in this app has the controller class Frappe looks for by name.

	Frappe imports a DocType's controller and reads one attribute off it: the class named after the
	DocType with its spaces removed (`frappe/model/base_document.py`, `import_controller`). A
	controller that spells its class any other way is not a controller as far as Frappe is
	concerned, and the failure is not an error on the page that needs the DocType. It is
	`remove_orphan_doctypes` deleting the DocType on the next migrate, which takes the table with
	it, and a dataset import that then writes into nothing.

	`Toolbox PIN Record` and `Toolbox IFSC Record` both ship a class that does not match
	(`ToolboxPinRecord`, `ToolboxIfscRecord`), and both were deleted from a Frappe 16 site this
	way. `Toolbox HSN Record` spells its class `ToolboxHSNRecord` and was spared, which is what
	makes this worth a test rather than a note.
	"""

	def controller_class_name(self, doctype):
		"""The name Frappe looks for. Copied from `import_controller` on purpose.

		A copy that drifts from the framework will fail this suite rather than pass it, which is the
		outcome worth having: the port is where the two have to be compared.
		"""
		return doctype.replace(" ", "").replace("-", "")

	def test_every_doctype_is_in_the_app(self):
		installed = set(frappe.get_all("DocType", filters={"module": "Toolbox"}, pluck="name"))

		for doctype in DOCTYPES:
			with self.subTest(doctype=doctype):
				self.assertIn(doctype, installed)

	def test_frappe_can_import_every_controller(self):
		"""The check `remove_orphan_doctypes` makes, run against the names the app declares."""
		for doctype in DOCTYPES:
			with self.subTest(doctype=doctype):
				controller = import_controller(doctype)

				self.assertEqual(controller.__name__, self.controller_class_name(doctype))
