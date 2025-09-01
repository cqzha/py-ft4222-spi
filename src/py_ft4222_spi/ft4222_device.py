from ctypes import *
from .ft4222_types import *
from enum import IntEnum
LibD2XX = cdll.LoadLibrary("C:\\Windows\\System32\\ftd2xx.dll")
LibFT4222 = cdll.LoadLibrary("./LibFT4222-64.dll")


class FT2xxDeviceError(Exception):
    __ftd2xx_msgs = [
        "FT_OK",
        "FT_INVALID_HANDLE",
        "FT_DEVICE_NOT_FOUND",
        "FT_DEVICE_NOT_OPENED",
        "FT_IO_ERROR",
        "FT_INSUFFICIENT_RESOURCES",
        "FT_INVALID_PARAMETER",
        "FT_INVALID_BAUD_RATE",
        "FT_DEVICE_NOT_OPENED_FOR_ERASE",
        "FT_DEVICE_NOT_OPENED_FOR_WRITE",
        "FT_FAILED_TO_WRITE_DEVICE",
        "FT_EEPROM_READ_FAILED",
        "FT_EEPROM_WRITE_FAILED",
        "FT_EEPROM_ERASE_FAILED",
        "FT_EEPROM_NOT_PRESENT",
        "FT_EEPROM_NOT_PROGRAMMED",
        "FT_INVALID_ARGS",
        "FT_NOT_SUPPORTED",
        "FT_OTHER_ERROR"
    ]

    def __init__(self, msg_code: int) -> None:
        self.msg = self.__ftd2xx_msgs[msg_code]

    def __str__(self) -> str:
        return self.msg


class FT4222DeviceError(FT2xxDeviceError):
    __ft4222_msgs = [
        "FT4222_DEVICE_NOT_SUPPORTED",
        "FT4222_CLK_NOT_SUPPORTED",
        "FT4222_VENDER_CMD_NOT_SUPPORTED",
        "FT4222_IS_NOT_SPI_MODE",
        "FT4222_IS_NOT_I2C_MODE",
        "FT4222_IS_NOT_SPI_SINGLE_MODE",
        "FT4222_IS_NOT_SPI_MULTI_MODE",
        "FT4222_WRONG_I2C_ADDR",
        "FT4222_INVAILD_FUNCTION",
        "FT4222_INVALID_POINTER",
        "FT4222_EXCEEDED_MAX_TRANSFER_SIZE",
        "FT4222_FAILED_TO_READ_DEVICE",
        "FT4222_I2C_NOT_SUPPORTED_IN_THIS_MODE",
        "FT4222_GPIO_NOT_SUPPORTED_IN_THIS_MODE",
        "FT4222_GPIO_EXCEEDED_MAX_PORTNUM",
        "FT4222_GPIO_WRITE_NOT_SUPPORTED",
        "FT4222_GPIO_PULLUP_INVALID_IN_INPUTMODE",
        "FT4222_GPIO_PULLDOWN_INVALID_IN_INPUTMODE",
        "FT4222_GPIO_OPENDRAIN_INVALID_IN_OUTPUTMODE",
        "FT4222_INTERRUPT_NOT_SUPPORTED",
        "FT4222_GPIO_INPUT_NOT_SUPPORTED",
        "FT4222_EVENT_NOT_SUPPORTED",
        "FT4222_FUN_NOT_SUPPORT"
    ]

    def __init__(self, msg_code: int) -> None:
        if msg_code >= FT4222_DEVICE_NOT_SUPPORTED:
            self.msg = self.__ft4222_msgs[(msg_code - 1000)]
        else:
            super().__init__(msg_code)

    def __str__(self) -> str:
        return self.msg


def check_ft_status(status_code):
    if status_code != FT_OK:
        raise FT4222DeviceError(status_code)


def list_ft_usb_devices():
    devices = []
    device_cnt = DWORD(0)
    check_ft_status(LibD2XX.FT_CreateDeviceInfoList(byref(device_cnt)))
    for i in range(device_cnt.value):
        idx = DWORD(i)
        f = pointer(DWORD(0))
        t = pointer(DWORD(0))
        id = pointer(DWORD(0))
        lid = pointer(DWORD(0))
        sn = pointer((CHAR*16)())
        d = pointer((CHAR*64)())
        h = pointer(FT_HANDLE(0))
        check_ft_status(
            LibD2XX.FT_GetDeviceInfoDetail(idx, f, t, id, lid, sn, d, h)
        )

        if h.contents.value is None:
            handle = 0
        else:
            handle = h.contents.value

        print(f"""Dev {idx.value}:
            Flags= {hex(f.contents.value)}
            Type= {hex(t.contents.value)}
            ID= {hex(id.contents.value)}
            LocId= {hex(lid.contents.value)}
            SerialNumber= {sn.contents.value.decode()}
            Description= {d.contents.value.decode()}
            ftHandle= {hex(handle)}""")
        devices.append(
            FT_DEVICE_LIST_INFO_NODE(
                f.contents.value,
                t.contents.value,
                id.contents.value,
                lid.contents.value,
                sn.contents.value,
                d.contents.value,
                handle
            )
        )
    return devices


def get_ft4222_device():
    usb_devices = list_ft_usb_devices()
    if len(usb_devices) == 0:
        raise FT4222DeviceError(FT_DEVICE_NOT_FOUND)
    for node in usb_devices:
        desc = node.Description.decode()
        print(desc)
        if desc == "FT4222 A" or desc == "FT4222":
            return node


def open_device_byloc(location, handle):
    location_p = c_void_p(location)
    handle_p = pointer(handle)
    return LibD2XX.FT_OpenEx(location_p, FT_OPEN_BY_LOCATION, handle_p)


def open_device_bydesc(desc, handle):
    desc_p = pointer((CHAR*64)(*desc))
    handle_p = pointer(handle)
    return LibD2XX.FT_OpenEx(desc_p, FT_OPEN_BY_DESCRIPTION, handle_p)


class Device:
    def __init__(self, node: FT_DEVICE_LIST_INFO_NODE) -> None:
        self._handle = FT_HANDLE(0)
        if self._curr_status(node.Flags) == 0:
            self._open(node)
        pass

    def _curr_status(self, flag: int):
        # 0 closed
        # 1 open
        return flag & 0x1

    def _open(self, node: FT_DEVICE_LIST_INFO_NODE):
        check_ft_status(open_device_bydesc(node.Description, self._handle))

    def _close(self):
        check_ft_status(LibD2XX.FT_Close(self._handle))

    def set_timeout(self, read_timeout: int, write_timeout: int):
        check_ft_status(
            LibD2XX.FT_SetTimeouts(
                self._handle,
                read_timeout,
                write_timeout
            )
        )

    def reset(self):
        check_ft_status(LibD2XX.FT_ResetDevice(self._handle))

    def __del__(self):
        self._close()


class FT4222(Device):
    __chip_rev_map = {
        0x42220100: "Rev. A",
        0x42220200: "Rev. B",
        0x42220300: "Rev. C",
        0x42220400: "Rev. D"
    }

    __chip_rev_min_lib = {
        0x42220100: 0,
        0x42220200: 0x01020000,
        0x42220300: 0x01030000,
        0x42220400: 0x01040000
    }

    def __init__(self) -> None:
        d = get_ft4222_device()
        if d is None:
            raise FT2xxDeviceError(FT_DEVICE_NOT_FOUND)
        self._d = d
        super().__init__(self._d)
        self._chip_version = 0
        self._dll_version = 0
        self._get_version()

    @property
    def chip_version(self):
        return self._chip_version

    @property
    def dll_version(self):
        return self._dll_version

    @property
    def handle(self):
        return self._handle

    @property
    def chip_revision(self):
        try:
            return self.__chip_rev_map[self._chip_version]
        except KeyError:
            return "Rev. Unknown"

    def _get_version(self):
        ver = FT4222_Version()
        check_ft_status(LibFT4222.FT4222_GetVersion(self._handle, byref(ver)))
        self._chip_version = ver.chipVersion
        self._dll_version = ver.dllVersion

    def set_clock(self, clk: int):
        check_ft_status(LibFT4222.FT4222_SetClock(self._handle, clk))

    def get_clock(self):
        clk = c_int(0)
        check_ft_status(LibFT4222.FT4222_GetClock(self._handle, pointer(clk)))
        return FT4222_ClockRate(clk.value).name

    def set_wakeup_interrupt(self, enable: bool):
        check_ft_status(
            LibFT4222.FT4222_SetWakeUpInterrupt(
                self._handle,
                enable
            )
        )

    def set_interrupt_trigger(self, trigger: int):
        check_ft_status(
            LibFT4222.FT4222_SetInterruptTrigger(
                self._handle,
                trigger
            )
        )

    def set_suspend_out(self, enable: bool):
        check_ft_status(LibFT4222.FT4222_SetSuspendOut(self._handle, enable))

    def get_max_transfer_size(self):
        max_size = c_uint16(0)
        check_ft_status(
            LibFT4222.FT4222_GetMaxTransferSize(
                self._handle,
                byref(max_size)
            )
        )
        return max_size.value

    def get_chip_mode(self):
        chip_mode = c_uint8(0)
        check_ft_status(
            LibFT4222.FT4222_GetChipMode(
                self._handle,
                byref(chip_mode)
            )
        )
        return chip_mode.value

    def chip_reset(self):
        check_ft_status(LibFT4222.FT4222_ChipReset(self._handle))

    def __del__(self):
        check_ft_status(LibFT4222.FT4222_UnInitialize(self._handle))
        return super().__del__()


class FT4222_SPI:
    def __init__(self, handle, tp: str, *args) -> None:
        self.handle = handle
        if tp == "master":
            self.master_init(*args)
        else:
            self.slave_init_ex(*args)
        pass

    def master_init(self,
                    mode: FT4222_SpiMode,
                    clock: FT4222_SpiClock,
                    cpol: FT4222_SpiCpol,
                    cpha: FT4222_SpiCpha,
                    ssomap: int):
        check_ft_status(
            LibFT4222.FT4222_SPIMaster_Init(
                self.handle,
                mode.value,
                clock.value,
                cpol.value,
                cpha.value,
                c_uint8(ssomap)
            )
        )
        pass

    def master_set_mode(self,
                        cpol: FT4222_SpiCpol,
                        cpha: FT4222_SpiCpha):
        check_ft_status(
            LibFT4222.FT4222_SPIMaster_SetMode(
                self.handle,
                cpol.value,
                cpha.value
            )
        )
        pass

    def master_set_cs(self, cs: Spi_ChipSelect):
        check_ft_status(
            LibFT4222.FT4222_SPIMaster_SetCS(
                self.handle,
                cs.value
            )
        )
        pass

    def master_set_lines(self, spi_mode: FT4222_SpiMode):
        check_ft_status(
            LibFT4222.FT4222_SPIMaster_SetLines(
                self.handle,
                spi_mode.value
            )
        )
        pass

    def master_single_r(self, r_len: int):
        r_buffer = (c_uint8*r_len)()
        size_transferred = c_uint16(0)
        check_ft_status(
            LibFT4222.FT4222_SPIMaster_SingleRead(
                self.handle,
                byref(r_buffer),
                c_uint16(r_len),
                byref(size_transferred),
                True
            )
        )
        return [n for n in r_buffer]

    def master_single_w(self, data):
        w_buffer = (c_uint8*len(data))(*data)
        size_transferred = c_uint16(0)
        check_ft_status(
            LibFT4222.FT4222_SPIMaster_SingleWrite(
                self.handle,
                byref(w_buffer),
                c_uint16(len(data)),
                byref(size_transferred),
                True
            )
        )

    def master_single_rw(self, data):
        w_buffer = (c_uint8*len(data))(*data)
        r_buffer = (c_uint8*len(data))()
        size_transferred = c_uint16(0)
        check_ft_status(
            LibFT4222.FT4222_SPIMaster_SingleReadWrite(
                self.handle,
                byref(r_buffer),
                byref(w_buffer),
                c_uint16(len(data)),
                byref(size_transferred),
                True
            )
        )
        return [n for n in r_buffer]

    def master_multi_rw(self, data, r_len: int, cmd_len: int, data_len: int):
        if r_len > 65535:
            raise ValueError("Maximum size is 65535")
        if cmd_len > 15:
            raise ValueError("Maximum size is 15")
        if data_len > 65535:
            raise ValueError("Maximum size is 65535")

        w_buffer = (c_uint8*len(data))(*data)
        r_buffer = (c_uint8*r_len)()
        size_transferred = c_uint16(0)
        check_ft_status(
            LibFT4222.FT4222_SPIMaster_MultiReadWrite(
                self.handle,
                byref(r_buffer),
                byref(w_buffer),
                c_uint8(cmd_len),
                c_uint16(data_len),
                c_uint16(r_len),
                byref(size_transferred)
            )
        )
        return [n for n in r_buffer]

    def slave_init(self):
        pass

    def slave_init_ex(self):
        pass

    def slave_set_mode(self):
        pass

    def slave_get_rx_status(self):
        pass

    def slave_r(self):
        pass

    def slave_w(self):
        pass

    def reset(self):
        check_ft_status(
            LibFT4222.FT4222_SPI_Reset(self.handle)
        )

    def reset_transaction(self, idx):
        check_ft_status(
            LibFT4222.FT4222_SPI_ResetTransaction(
                self.handle,
                c_uint8(idx)
            )
        )

    def set_driving_strength(
            self,
            clk_strength: SPI_DrivingStrength,
            io_strength: SPI_DrivingStrength,
            sso_strength: SPI_DrivingStrength
    ):
        check_ft_status(
            LibFT4222.FT4222_SPI_SetDrivingStrength(
                self.handle,
                clk_strength.value,
                io_strength.value,
                sso_strength.value
            )
        )
