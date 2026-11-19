"""Ícone do Arquithon desenhado em código, só com a biblioteca padrão.

Sem arquivo de imagem no repositório nem Pillow: o desenho (quadrado roxo
arredondado com uma pasta branca) é calculado pixel a pixel e codificado em
PNG à mão. O mesmo desenho serve para a janela (`iconphoto`) e para gerar o
`.ico` usado pelo PyInstaller no executável.
"""

import base64
import struct
import zlib

_TOP = (0x8B, 0x6D, 0xFF)
_BOTTOM = (0x5B, 0x3C, 0xE0)
_SS = 3  # supersampling por eixo, para suavizar as bordas


def _in_round_rect(x, y, x0, y0, x1, y1, r):
    if not (x0 <= x <= x1 and y0 <= y <= y1):
        return False
    cx = min(max(x, x0 + r), x1 - r)
    cy = min(max(y, y0 + r), y1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def _sample(u, v):
    """Cor (r, g, b, a) no ponto (u, v) do quadrado unitário."""
    if not _in_round_rect(u, v, 0.0, 0.0, 1.0, 1.0, 0.22):
        return (0, 0, 0, 0)
    if _in_round_rect(u, v, 0.20, 0.42, 0.80, 0.76, 0.06):  # corpo da pasta
        return (255, 255, 255, 255)
    if _in_round_rect(u, v, 0.20, 0.27, 0.50, 0.46, 0.05):  # aba da pasta
        return (221, 212, 255, 255)
    if _in_round_rect(u, v, 0.20, 0.34, 0.80, 0.70, 0.06):  # fundo da pasta
        return (221, 212, 255, 255)
    return tuple(round(a + (b - a) * v) for a, b in zip(_TOP, _BOTTOM)) + (255,)


def render(size):
    """Linhas de pixels RGBA (bytes) do ícone em `size` x `size`."""
    rows = []
    n = _SS * _SS
    for py in range(size):
        row = bytearray()
        for px in range(size):
            acc = [0, 0, 0, 0]
            for sy in range(_SS):
                for sx in range(_SS):
                    r, g, b, a = _sample((px + (sx + 0.5) / _SS) / size, (py + (sy + 0.5) / _SS) / size)
                    acc[0] += r * a
                    acc[1] += g * a
                    acc[2] += b * a
                    acc[3] += a
            alpha = acc[3]
            if alpha:
                row += bytes((acc[0] // alpha, acc[1] // alpha, acc[2] // alpha, alpha // n))
            else:
                row += b'\0\0\0\0'
        rows.append(bytes(row))
    return rows


def png_bytes(size):
    raw = b''.join(b'\0' + row for row in render(size))

    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xFFFFFFFF)

    return (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9))
            + chunk(b'IEND', b''))


def photo(master, size):
    """tk.PhotoImage do ícone (o Tk 8.6 lê PNG direto)."""
    import tkinter as tk
    return tk.PhotoImage(master=master, data=base64.b64encode(png_bytes(size)))


def write_ico(path, sizes=(16, 24, 32, 48, 64, 128, 256)):
    """Gera um .ico com as imagens em PNG (aceito pelo Windows Vista em diante)."""
    imagens = [png_bytes(s) for s in sizes]
    header = struct.pack('<HHH', 0, 1, len(sizes))
    offset = 6 + 16 * len(sizes)
    entradas = b''
    for s, img in zip(sizes, imagens):
        entradas += struct.pack('<BBBBHHII', s % 256, s % 256, 0, 0, 1, 32, len(img), offset)
        offset += len(img)
    with open(path, 'wb') as f:
        f.write(header + entradas + b''.join(imagens))
