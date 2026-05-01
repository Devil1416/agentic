import unittest
from src import analyzer, utils
import pandas as pd
from colorama import Fore

class TestCli(unittest.TestCase):
    def setUp(self):
        self.analyzer = analyzer.Analyzer()
        self.utils = utils.Utils()

    def test_csv_load(self):
        df = pd.read_csv('data/sample_events.csv')
        self.assertFalse(df.empty)

    def test_json_load(self):
        df = pd.read_json('data/sample_events.json')
        self.assertFalse(df.empty)

    def test_total_events(self):
        df = pd.read_csv('data/sample_events.csv')
        total_events = self.analyzer.calculate_total_events(df)
        self.assertEqual(total_events, len(df))

    def test_unique_users(self):
        df = pd.read_csv('data/sample_events.csv')
        unique_users = self.analyzer.calculate_unique_users(df)
        self.assertEqual(unique_users, len(df['user_id'].unique()))

    def test_top_actions(self):
        df = pd.read_csv('data/sample_events.csv')
        top_actions = self.analyzer.calculate_top_actions(df)
        self.assertEqual(top_actions, df['action'].mode().iloc[0])

    def test_colorama_output(self):
        colored_text = self.utils.colored_print('Test text', Fore.RED)
        self.assertIn('Test text', colored_text)

if __name__ == '__main__':
    unittest.main()