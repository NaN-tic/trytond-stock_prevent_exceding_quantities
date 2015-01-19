==========================================
Stock Prevent Exceding Quantities Scenario
==========================================

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from operator import attrgetter
    >>> from proteus import config, Model, Wizard
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install sale::

    >>> Module = Model.get('ir.module.module')
    >>> module, = Module.find([
    ...     ('name', '=', 'stock_prevent_exceding_quantities')
    ...     ])
    >>> Module.install([module.id], config.context)
    >>> Wizard('ir.module.module.install_upgrade').execute('upgrade')

Create company::

    >>> Currency = Model.get('currency.currency')
    >>> CurrencyRate = Model.get('currency.currency.rate')
    >>> currencies = Currency.find([('code', '=', 'USD')])
    >>> if not currencies:
    ...     currency = Currency(name='U.S. Dollar', symbol='$', code='USD',
    ...         rounding=Decimal('0.01'), mon_grouping='[3, 3, 0]',
    ...         mon_decimal_point='.', mon_thousands_sep=',')
    ...     currency.save()
    ...     CurrencyRate(date=today + relativedelta(month=1, day=1),
    ...         rate=Decimal('1.0'), currency=currency).save()
    ... else:
    ...     currency, = currencies
    >>> Company = Model.get('company.company')
    >>> Party = Model.get('party.party')
    >>> company_config = Wizard('company.company.config')
    >>> company_config.execute('company')
    >>> company = company_config.form
    >>> party = Party(name='Dunder Mifflin')
    >>> party.save()
    >>> company.party = party
    >>> company.currency = currency
    >>> company_config.execute('add')
    >>> company, = Company.find([])

Reload the context::

    >>> User = Model.get('res.user')
    >>> Group = Model.get('res.group')
    >>> config._context = User.get_preferences(True, config.context)

Create parties::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()

Create product::

    >>> ProductUom = Model.get('product.uom')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])
    >>> ProductTemplate = Model.get('product.template')
    >>> Product = Model.get('product.product')
    >>> product = Product()
    >>> template = ProductTemplate()
    >>> template.name = 'product'
    >>> template.default_uom = unit
    >>> template.type = 'goods'
    >>> template.list_price = Decimal('10')
    >>> template.cost_price = Decimal('5')
    >>> template.cost_price_method = 'fixed'
    >>> template.save()
    >>> product.template = template
    >>> product.save()


Get locations::

    >>> Location = Model.get('stock.location')
    >>> storage, = Location.find([('code', '=', 'STO')])
    >>> outgoing_loc, = Location.find([('code', '=', 'OUT')])
    >>> customer_loc, = Location.find([('code', '=', 'CUS')])


Create an Inventory::

    >>> Inventory = Model.get('stock.inventory')
    >>> InventoryLine = Model.get('stock.inventory.line')
    >>> inventory = Inventory()
    >>> inventory.location = storage
    >>> inventory.save()
    >>> inventory_line = InventoryLine(product=product, inventory=inventory)
    >>> inventory_line.quantity = 100.0
    >>> inventory_line.expected_quantity = 0.0
    >>> inventory.save()
    >>> inventory_line.save()
    >>> Inventory.confirm([inventory.id], config.context)
    >>> inventory.state
    u'done'

Try to send exceding quantities with one move::

    >>> ShipmentOut = Model.get('stock.shipment.out')
    >>> shipment = ShipmentOut()
    >>> shipment.customer = customer
    >>> move = shipment.outgoing_moves.new()
    >>> move.product = product
    >>> move.from_location = outgoing_loc
    >>> move.to_location = customer_loc
    >>> move.quantity = 5.0
    >>> shipment.save()
    >>> shipment.click('wait')
    >>> for move in shipment.inventory_moves:
    ...     move.quantity = 6.0
    >>> shipment.save()
    >>> ShipmentOut.assign_try([shipment.id], config.context)
    True
    >>> shipment.click('pack')
    Traceback (most recent call last):
        ...
    UserError: ('UserError', (u'Move 6.0u product makes inventory quantities of product "product" exceed outgoing quantities by 1.0 Unit.', ''))
    >>> shipment.click('wait')
    >>> ShipmentOut.assign_try([shipment.id], config.context)
    True
    >>> shipment.click('pack')
    >>> shipment.click('done')

Try to send exceding quantities with more than one move::

    >>> ShipmentOut = Model.get('stock.shipment.out')
    >>> shipment = ShipmentOut()
    >>> shipment.customer = customer
    >>> move = shipment.outgoing_moves.new()
    >>> move.product = product
    >>> move.from_location = outgoing_loc
    >>> move.to_location = customer_loc
    >>> move.quantity = 5.0
    >>> shipment.save()
    >>> shipment.click('wait')
    >>> move = shipment.inventory_moves.new()
    >>> move.product = product
    >>> move.from_location = storage
    >>> move.to_location = outgoing_loc
    >>> move.quantity = 1.0
    >>> shipment.save()
    >>> ShipmentOut.assign_try([shipment.id], config.context)
    True
    >>> shipment.click('pack')
    Traceback (most recent call last):
        ...
    UserError: ('UserError', (u'Move 5.0u product makes inventory quantities of product "product" exceed outgoing quantities by 1.0 Unit.', ''))
