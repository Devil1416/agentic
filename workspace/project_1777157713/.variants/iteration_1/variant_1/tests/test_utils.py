import unittest
from lib.utils import fibonacci

class TestFibonacci(unittest.TestCase):
    def test_fibonacci_zero(self):
        self.assertEqual(fibonacci(0), 0)
        
    def test_fibonacci_one(self):
        self.assertEqual(fibonacci(1), 1)
        
    def test_fibonacci_positive(self):
        self.assertEqual(fibonacci(5), 5)
        self.assertEqual(fibonacci(7), 13)
        self.assertEqual(fibonacci(10), 55)
        
    def test_fibonacci_negative(self):
        with self.assertRaises(ValueError):
            fibonacci(-1)
            
if __name__ == '__main__':
    unittest.main()