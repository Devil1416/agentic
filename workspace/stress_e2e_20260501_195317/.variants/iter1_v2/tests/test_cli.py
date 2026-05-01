import unittest
from src import analyzer, utils
import pandas as pd
from colorama import Fore

class TestCli(unittest.TestCase):
    def setUp(self):
        self.analyzer = analyzer.Analyzer()
        self.utils = utils.Utils()

    def test_load_csv(self):
        df = self.analyzer.load('data/sample_events.csv')
        self.assertIsInstance(df, pd.DataFrame)

    def test_load_json(self):
        df = self.analyzer.load('data/sample<｜begin▁of▁sentence｜>ample_events.json')
        self.assertIsInstance(df, pd.DataFrame)

    def test_total_events(self):
        df = self.analyzer.load('data/sample_events.csv')
        total_events = self.analyzer.total_events(df)
        self.assertEqual(total_events, len(df))

    def test_unique_users(self):
        df = self.analyzer.load('data/sample_events.csv')
        unique_users = self.analyzer.unique_users(df)
        self.assertEqual(unique_users, df['user_id'].nunique())

    def test_top_actions(self):
        df = self.analyzer.load('data/sample_events.csv')
        top_actions = self.analyzer.top_actions(df)
        self.assertEqual(top_actions, df['action'].mode().iloc[0])

    def test_colorize(self):
        colored_text = self.utils.colorize('Test text', Fore.RED)
        self.assertIn("\x1b[31m", colored_text)
        self.assertIn("Test text", colored_text)

if __name__ == '__main__':
    unittest.main()