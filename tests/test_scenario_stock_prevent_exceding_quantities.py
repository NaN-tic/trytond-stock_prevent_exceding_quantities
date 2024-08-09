import unittest
from decimal import Decimal

from proteus import Model
from trytond.exceptions import UserError
from trytond.modules.company.tests.tools import create_company, get_company
from trytond.tests.test_tryton import drop_db
from trytond.tests.tools import activate_modules


class Test(unittest.TestCase):

    def setUp(self):
        drop_db()
        super().setUp()

    def tearDown(self):
        drop_db()
        super().tearDown()

    def test(self):

        # Install stock_prevent_exceding_quantities
        config = activate_modules('stock_prevent_exceding_quantities')

        # Create company
        _ = create_company()
        company = get_company()

        # Create parties
        Party = Model.get('party.party')
        customer = Party(name='Customer')
        customer.save()

        # Create product
        ProductUom = Model.get('product.uom')
        unit, = ProductUom.find([('name', '=', 'Unit')])
        ProductTemplate = Model.get('product.template')
        Product = Model.get('product.product')
        product = Product()
        template = ProductTemplate()
        template.name = 'product'
        template.default_uom = unit
        template.type = 'goods'
        template.list_price = Decimal('10')
        template.cost_price = Decimal('5')
        template.cost_price_method = 'fixed'
        template.save()
        product.template = template
        product.save()

        # Get locations
        Location = Model.get('stock.location')
        storage, = Location.find([('code', '=', 'STO')])
        outgoing_loc, = Location.find([('code', '=', 'OUT')])
        customer_loc, = Location.find([('code', '=', 'CUS')])

        # Create an Inventory
        Inventory = Model.get('stock.inventory')
        InventoryLine = Model.get('stock.inventory.line')
        inventory = Inventory()
        inventory.location = storage
        inventory.save()
        inventory_line = InventoryLine(product=product, inventory=inventory)
        inventory_line.quantity = 100.0
        inventory_line.expected_quantity = 0.0
        inventory.save()
        inventory_line.save()
        Inventory.confirm([inventory.id], config.context)
        self.assertEqual(inventory.state, 'done')

        # Try to send exceding quantities with one move
        ShipmentOut = Model.get('stock.shipment.out')
        shipment = ShipmentOut()
        shipment.customer = customer
        move = shipment.outgoing_moves.new()
        move.product = product
        move.from_location = outgoing_loc
        move.to_location = customer_loc
        move.quantity = 5.0
        move.unit_price = Decimal(0)
        move.currency = company.currency
        shipment.save()
        shipment.click('wait')

        for move in shipment.inventory_moves:
            move.quantity = 6.0

        shipment.save()
        with self.assertRaises(UserError):
            ShipmentOut.assign_try([shipment.id], config.context)

        for move in shipment.inventory_moves:
            move.quantity = 5.0

        shipment.save()
        ShipmentOut.assign_try([shipment.id], config.context)
        shipment.click('pick')
        shipment.click('pack')
        shipment.click('do')
        self.assertEqual(shipment.state, 'done')

        # Try to send exceding quantities with more than one move
        ShipmentOut = Model.get('stock.shipment.out')
        shipment = ShipmentOut()
        shipment.customer = customer
        move = shipment.outgoing_moves.new()
        move.product = product
        move.from_location = outgoing_loc
        move.to_location = customer_loc
        move.quantity = 5.0
        move.unit_price = Decimal(0)
        move.currency = company.currency
        shipment.save()
        shipment.click('wait')
        move = shipment.inventory_moves.new()
        move.product = product
        move.from_location = storage
        move.to_location = outgoing_loc
        move.quantity = 1.0
        shipment.save()
        with self.assertRaises(UserError):
            ShipmentOut.assign_try([shipment.id], config.context)
