"""Test logic màn hình của cửa sổ chơi (chonoi.live, Ticket-02 mục 2): menu, intro giữ mô phỏng, input v1.1.
Không mở cổng mạng: gọi thẳng LiveGame. Chỉ dành cho starter Python.
"""

import unittest

from chonoi.contract import load_contract
from chonoi.live import LiveGame


def tuning():
    return load_contract()["tuning"]


class Screens(unittest.TestCase):
    def test_menu_holds_simulation_until_play(self):
        g = LiveGame("gather", tuning(), {}, 1, show_menu=True)
        for _ in range(5):
            g._tick_once()
        self.assertEqual(g.session.tick, 0, "menu đang hiện thì không bước mô phỏng")
        g.ui_action("play")
        self.assertIsNone(g.screen)
        g._tick_once()
        self.assertEqual(g.session.tick, 1)

    def test_day_intro_then_evening_intro_on_phase_change(self):
        g = LiveGame("day", tuning(), {"gather": {"hold": ["ca_loc"], "random_fish": False}}, 1, days=1, show_menu=True)
        g.ui_action("play")
        self.assertEqual(g.screen, "day_intro")
        g._tick_once()
        self.assertEqual(g.session.tick, 0)
        g.ui_action("continue")
        g.set_input({"interact": True})  # đang ở bến: cập bến ngay
        g._tick_once()
        self.assertEqual((g.session.sim.phase, g.screen), ("quan", "evening_intro"))
        self.assertEqual(g.stats["day"]["delivered"], {"ca_loc": 1})
        g._tick_once()
        self.assertEqual(g.session.tick, 1, "EveningIntro giữ mô phỏng")

    def test_menu_action_resets_and_quit(self):
        g = LiveGame("quan", tuning(), {}, 1)
        g._tick_once()
        g.ui_action("menu")
        self.assertEqual((g.screen, g.session.tick), ("menu", 0))
        g.ui_action("quit")
        self.assertEqual(g.screen, "quit")
        with self.assertRaises(ValueError):
            g.ui_action("hack")


class Inputs(unittest.TestCase):
    def test_v11_inputs_validated(self):
        g = LiveGame("day", tuning(), {}, 1, days=1)
        g.set_input({"pause": True, "shop_done": False, "buy": "oxygen"})
        for bad in ({"pause": 1}, {"buy": ""}, {"buy": 5}, {"buy": "x" * 40}):
            with self.assertRaises(ValueError):
                g.set_input(bad)


if __name__ == "__main__":
    unittest.main()
