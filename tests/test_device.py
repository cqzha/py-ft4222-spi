import unittest
from py_ft4222_spi import FT4222, FT4222_ClockRate


class TestDevice(unittest.TestCase):
    def test_get_clock(self):
        ft4222 = FT4222()
        self.assertEqual(ft4222.get_clock(), 2)
        pass

    def test_set_clock(self):
        ft4222 = FT4222()
        ft4222.set_clock(FT4222_ClockRate(1))
        self.assertEqual(ft4222.get_clock(), 1)
        pass


if __name__ == '__main__':
    unittest.main()
