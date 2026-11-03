import unittest
from pathlib import Path

from backend.erp import (
    UnifiedStockItem,
    get_group_inventory,
    load_dk_inventory,
    load_no_inventory,
    load_se_inventory,
)


class TestERPAdapters(unittest.TestCase):
    def test_load_dk_inventory(self):
        items = load_dk_inventory()
        self.assertGreater(len(items), 1000)
        self.assertTrue(all(isinstance(i, UnifiedStockItem) for i in items))
        self.assertTrue(all(i.country == "DK" for i in items))
        self.assertTrue(all(i.available_quantity == max(0, i.quantity_on_hand - i.reserved_quantity) for i in items))
        whs = {i.warehouse_id for i in items}
        self.assertIn("DK-DC-01", whs)
        self.assertIn("DK-BR-01", whs)

    def test_load_se_inventory(self):
        items = load_se_inventory()
        self.assertGreater(len(items), 1000)
        self.assertTrue(all(isinstance(i, UnifiedStockItem) for i in items))
        self.assertTrue(all(i.country == "SE" for i in items))
        self.assertTrue(all(i.available_quantity == max(0, i.quantity_on_hand - i.reserved_quantity) for i in items))
        whs = {i.warehouse_id for i in items}
        self.assertIn("SE-DC-01", whs)
        self.assertIn("SE-BR-01", whs)

    def test_load_no_inventory(self):
        items = load_no_inventory()
        self.assertGreater(len(items), 1000)
        self.assertTrue(all(isinstance(i, UnifiedStockItem) for i in items))
        self.assertTrue(all(i.country == "NO" for i in items))
        self.assertTrue(all(i.available_quantity == max(0, i.quantity_on_hand - i.reserved_quantity) for i in items))
        whs = {i.warehouse_id for i in items}
        self.assertIn("NO-DC-01", whs)
        self.assertIn("NO-BR-01", whs)

    def test_get_group_inventory_and_cross_border_integrity(self):
        group_items = get_group_inventory()
        self.assertEqual(len(group_items), 3315)

        # Swedish exclusive rare item: TIM-SE-PINE45
        se_rare_sku = "TIM-SE-PINE45"
        dk_stock = [i for i in group_items if i.sku == se_rare_sku and i.country == "DK"]
        no_stock = [i for i in group_items if i.sku == se_rare_sku and i.country == "NO"]
        se_stock = [i for i in group_items if i.sku == se_rare_sku and i.country == "SE"]

        self.assertEqual(sum(i.quantity_on_hand for i in dk_stock), 0)
        self.assertEqual(sum(i.quantity_on_hand for i in no_stock), 0)
        self.assertGreater(sum(i.quantity_on_hand for i in se_stock), 0)

        # Norwegian exclusive rare item: ROOF-NO-SLATE
        no_rare_sku = "ROOF-NO-SLATE"
        dk_stock = [i for i in group_items if i.sku == no_rare_sku and i.country == "DK"]
        se_stock = [i for i in group_items if i.sku == no_rare_sku and i.country == "SE"]
        no_stock = [i for i in group_items if i.sku == no_rare_sku and i.country == "NO"]

        self.assertEqual(sum(i.quantity_on_hand for i in dk_stock), 0)
        self.assertEqual(sum(i.quantity_on_hand for i in se_stock), 0)
        self.assertGreater(sum(i.quantity_on_hand for i in no_stock), 0)

        # Danish exclusive rare item: BRK-DK-CPHRED
        dk_rare_sku = "BRK-DK-CPHRED"
        se_stock = [i for i in group_items if i.sku == dk_rare_sku and i.country == "SE"]
        no_stock = [i for i in group_items if i.sku == dk_rare_sku and i.country == "NO"]
        dk_stock = [i for i in group_items if i.sku == dk_rare_sku and i.country == "DK"]

        self.assertEqual(sum(i.quantity_on_hand for i in se_stock), 0)
        self.assertEqual(sum(i.quantity_on_hand for i in no_stock), 0)
        self.assertGreater(sum(i.quantity_on_hand for i in dk_stock), 0)


if __name__ == "__main__":
    unittest.main()

