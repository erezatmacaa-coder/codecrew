import unittest

class TestHesapMakinesi(unittest.TestCase):
    def test_toplama(self):
        self.assertEqual(HesapMakinesi.toplama(2, 3), 5)

if __name__ == '__main__':
    unittest.main()