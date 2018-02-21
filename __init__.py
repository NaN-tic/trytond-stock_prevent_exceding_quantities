# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.pool import Pool
from . import shipment


def register():
    Pool.register(
        shipment.ShipmentOut,
        module='stock_prevent_exceding_quantities', type_='model')
