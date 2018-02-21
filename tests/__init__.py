# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
try:
    from trytond.modules.stock_prevent_exceding_quantities.tests.test_stock_prevent_exceding_quantities import suite
except ImportError:
    from .test_stock_prevent_exceding_quantities import suite

__all__ = ['suite']
