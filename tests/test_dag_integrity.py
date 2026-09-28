import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dags")))


class TestDAGIntegrity(unittest.TestCase):
    def test_dag_loaded_properly(self):
        from transport_stats_dag import dag

        self.assertIsNotNone(dag)
        self.assertEqual(dag.dag_id, "cambodia_trade_and_transport_monthly")
        self.assertEqual(len(dag.tasks), 12)

        # Check all 4 task groups exist
        group_ids = list(dag.task_group.children.keys())
        self.assertIn("transport_mode", group_ids)
        self.assertIn("partner_country", group_ids)
        self.assertIn("sitc_sectors", group_ids)
        self.assertIn("hs_chapters", group_ids)

        # Verify task dependencies in transport_mode
        t_scrape = dag.get_task("transport_mode.scrape_transport")
        t_transform = dag.get_task("transport_mode.transform_transport")
        t_load = dag.get_task("transport_mode.load_transport")
        self.assertIn(t_transform, t_scrape.downstream_list)
        self.assertIn(t_load, t_transform.downstream_list)

        # Verify task dependencies in partner_country
        c_scrape = dag.get_task("partner_country.scrape_country")
        c_transform = dag.get_task("partner_country.transform_country")
        c_load = dag.get_task("partner_country.load_country")
        self.assertIn(c_transform, c_scrape.downstream_list)
        self.assertIn(c_load, c_transform.downstream_list)


if __name__ == "__main__":
    unittest.main()
