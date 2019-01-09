# This file is part of Tryton.  The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.
from trytond.pool import Pool, PoolMeta
from trytond.i18n import gettext
from trytond.exceptions import UserError


__all__ = ['ShipmentOut']


class ShipmentOut(metaclass=PoolMeta):
    __name__ = 'stock.shipment.out'

    @classmethod
    def check_outgoing_quantity(cls, shipments):
        pool = Pool()
        Uom = pool.get('product.uom')
        for shipment in shipments:
            # Sum all outgoing quantities
            outgoing_qty = {}
            for move in shipment.outgoing_moves:
                if move.state == 'cancel':
                    continue
                quantity = Uom.compute_qty(move.uom, move.quantity,
                        move.product.default_uom, round=False)
                outgoing_qty.setdefault(move.product.id, 0.0)
                outgoing_qty[move.product.id] += quantity

            for move in shipment.inventory_moves:
                if move.state == 'cancel':
                    continue
                qty_default_uom = Uom.compute_qty(move.uom, move.quantity,
                    move.product.default_uom, round=False)
                qty = outgoing_qty.get(move.product.id, 0.0)
                # If it exist, decrease the sum
                if qty_default_uom <= qty:
                    outgoing_qty[move.product.id] -= qty_default_uom
                    continue
                else:
                    raise UserError(gettext(
                        'stock_prevent_exceding_quantities.exceding_quantity',
                            move=move.rec_name,
                            product=move.product.rec_name,
                            quantity=qty_default_uom - qty,
                            unit=move.product.default_uom.rec_name))

    @classmethod
    def assign(cls, shipments):
        cls.check_outgoing_quantity(shipments)
        return super(ShipmentOut, cls).assign(shipments)
