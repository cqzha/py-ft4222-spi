# py-ft4222-spi

py-ft4222-spi is a simple Python lib for FTDI FT4222 SPI function.<br>
It is based on FT4222 library from FTDI.

## Features

- FT4222 device control and configuartion
- SPI master mode operation: support for single & quad wire data transmission and reception 

## Installation

### 1. Prerequisites: Install FTDI D2XX Driver

This project relies on **FTDI D2XX Driver** to communicate with FT4222. you **must install this driver** before using this lib.

* **Download and Install the Driver**: Please refer the official page [FTDI](https://ftdichip.com/drivers/d2xx-drivers/)

* **Verify Installation**: Connect your FT4222 device and open Device Manager, you should see FTDI Device under Ports(COM & LPT).

### 2. Install this library

```bash
git clone https://github.com/cqzha/py-ft4222-spi.git
pip install -e .
```

## Quick Start


```python
from py_ft4222_spi import FT4222, FT4222_SPI, FT4222_SpiMode, FT4222_SpiClock, FT4222_SpiCpha,FT4222_SpiCpol

device = FT4222()
spi = FT4222_SPI(device.handle, "master",
            FT4222_SpiMode.SPI_IO_QUAD, # select spi mode
            FT4222_SpiClock.CLK_DIV_64, # select spi clock frequency
            FT4222_SpiCpol.CLK_IDLE_LOW, # select spi clock polarity
            FT4222_SpiCpha.CLK_LEADING # select spi clock phase
        )
# assume addr = 0x12345678
# write 0x5a to addr
cmd = [0x02, 0x12, 0x34, 0x56, 0x78, 0x5a]
spi.master_multi_rw(
    cmd,
    0,
    0,
    len(cmd)
)
```
