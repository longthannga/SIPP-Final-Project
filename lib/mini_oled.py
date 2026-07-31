import busio

_CHARS = " :%0123456789ACDEFHIKLMNOPRSTUY."
_FONT = (
    b'\x00\x00\x00\x00\x00\x00\x36\x36\x00\x00\x62\x64\x08\x13\x23'
    b'\x3e\x51\x49\x45\x3e\x00\x42\x7f\x40\x00\x62\x51\x49\x49\x46'
    b'\x22\x41\x49\x49\x36\x18\x14\x12\x7f\x10\x27\x45\x45\x45\x39'
    b'\x3c\x4a\x49\x49\x30\x01\x71\x09\x05\x03\x36\x49\x49\x49\x36'
    b'\x06\x49\x49\x29\x1e\x7e\x11\x11\x11\x7e\x3e\x41\x41\x41\x22'
    b'\x7f\x41\x41\x22\x1c\x7f\x49\x49\x49\x41\x7f\x09\x09\x09\x01'
    b'\x7f\x08\x08\x08\x7f\x00\x41\x7f\x41\x00\x7f\x08\x14\x22\x41'
    b'\x7f\x40\x40\x40\x40\x7f\x02\x0c\x02\x7f\x7f\x04\x08\x10\x7f'
    b'\x3e\x41\x41\x41\x3e\x7f\x09\x09\x09\x06\x7f\x09\x19\x29\x46'
    b'\x26\x49\x49\x49\x32\x01\x01\x7f\x01\x01\x3f\x40\x40\x40\x3f'
    b'\x07\x08\x70\x08\x07\x00\x60\x60\x00\x00'
)


class MiniOLED:
    def __init__(self, scl, sda, addr=0x3C):
        self.addr = addr
        self.i2c = busio.I2C(scl, sda)
        while not self.i2c.try_lock():
            pass
        self.buf = bytearray(1024)
        for c in (0xAE,0xD5,0x80,0xA8,0x3F,0xD3,0x00,0x40,0x8D,0x14,
                  0x20,0x00,0xA1,0xC8,0xDA,0x12,0x81,0xCF,0xD9,0xF1,
                  0xDB,0x40,0xA4,0xA6,0xAF):
            self._cmd(c)

    def _cmd(self, c):
        self.i2c.writeto(self.addr, bytes([0x00, c]))

    def pixel(self, x, y, color):
        if 0 <= x < 128 and 0 <= y < 64:
            idx = x + (y // 8) * 128
            bit = 1 << (y % 8)
            if color:
                self.buf[idx] |= bit
            else:
                self.buf[idx] &= (~bit & 0xFF)

    def fill(self, color):
        v = 0xFF if color else 0x00
        for i in range(len(self.buf)):
            self.buf[i] = v

    def text(self, s, x, y):
        cx = x
        for ch in s:
            p = _CHARS.find(ch)
            if p >= 0:
                base = p * 5
                for col in range(5):
                    b = _FONT[base + col]
                    for row in range(7):
                        if b & (1 << row):
                            self.pixel(cx + col, y + row, 1)
            cx += 6

    def show(self):
        self._cmd(0x21); self._cmd(0); self._cmd(127)
        self._cmd(0x22); self._cmd(0); self._cmd(7)
        for i in range(0, 1024, 16):
            self.i2c.writeto(self.addr, bytes([0x40]) + bytes(self.buf[i:i+16]))