import unittest
from app.LogicEntities.Player import Player
from app.LogicEntities.PlayerGame import PlayerGame  # Adjust import paths as needed
from app.main import context

class TestPlayerGame(unittest.TestCase):

    def setUp(self):
        # Create a mock Player instance
        self.mock_player = Player(name="TestPlayer", id=1, context=context)
        self.player_game = PlayerGame(self.mock_player)  # Instantiate PlayerGame with mock player

    def test_initial_state(self):
        """Test the initial state of PlayerGame."""
        # Check that player is set correctly
        self.assertEqual(self.player_game.player.id, 1)
        self.assertEqual(self.player_game.player.name, "TestPlayer")

    def test_month_start_increments(self):
        """Test that the month increments correctly when start_new_month is called."""
        self.player_game.time_manager.advance_day(31)
        self.assertGreater(self.player_game.time_manager.current_month, self.player_game.time_manager.old_month)
        
    def test_player_pay_salaries(self):
        """Test that the player pays salaries when start_new_month is called."""
        salaries_total = 250
        expected_remain_budget = self.player_game.player.budget - salaries_total
        self.player_game.player.salaries_to_pay = salaries_total
        self.player_game.time_manager.advance_day(31) 

        self.player_game.launch_new_month_actions()
        self.assertEqual(self.player_game.player.budget, expected_remain_budget)
        
    def test_player_get_products_from_modifiers(self):
        """Test that the player gets products from modifiers when start_new_month is called."""
        self.player_game.player.hire_resource("1", self.player_game.time_manager.current_month, self.player_game.time_manager.current_month)
        self.player_game.player.buy_project("1", self.player_game.time_manager.current_month, self.player_game.time_manager.current_month + 1)
        self.player_game.time_manager.advance_day(151)
        
        self.player_game.launch_new_month_actions()
        self.assertEqual(len(self.player_game.player.products),19  )

if __name__ == '__main__':
    unittest.main()
