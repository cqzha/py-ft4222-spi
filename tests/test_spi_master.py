import unittest
from py_ft4222_spi import (
    FT4222DeviceError,
    FT4222,
    FT4222_SPI,
    FT4222_SpiMode,
    FT4222_SpiClock,
    FT4222_SpiCpha,
    FT4222_SpiCpol
)


class TestSpiMaster(unittest.TestCase):
    def setUp(self):
        self.ft4222 = FT4222()
        self.spi_master = FT4222_SPI(
            self.ft4222.handle,
            "master",
            FT4222_SpiMode.SPI_IO_QUAD,
            FT4222_SpiClock.CLK_DIV_64,
            FT4222_SpiCpol.CLK_IDLE_LOW,
            FT4222_SpiCpha.CLK_LEADING,
            0x01
        )

    def assertNotRaises(self, expected_exception, callable, *args, **kwargs):
        try:
            callable(*args, **kwargs)
        except expected_exception:
            raise self.failureException(
                f"Unexpected exception {expected_exception} raised"
            )

    def test_spi_write(self):
        # assume addr = 0x12345678
        # write 0x5a to addr
        cmd = [0x02, 0x12, 0x34, 0x56, 0x78, 0x5a]
        self.assertNotRaises(
            FT4222DeviceError,
            self.spi_master.master_multi_rw,
            cmd,
            0,
            0,
            len(cmd)
        )

    def test_spi_read(self):
        # assume addr = 0x12345678
        # dummy cycle count = 4
        # read 4 bytes from addr
        cmd = [0x0b, 0x12, 0x34, 0x56, 0x78, 0xff, 0xff, 0xff, 0xff]
        self.assertNotRaises(
            FT4222DeviceError,
            self.spi_master.master_multi_rw,
            cmd,
            4,
            0,
            len(cmd)
        )

    def tearDown(self):
        self.ft4222.__del__()


if __name__ == '__main__':
    unittest.main()
