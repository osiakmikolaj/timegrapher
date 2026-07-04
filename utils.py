"""
utils.py
Funkcje pomocnicze niezwiązane bezpośrednio z GUI ani komunikacją szeregową.
"""


def delta_us(t1, t2):
    """Oblicza różnicę czasu w mikrosekundach, obsługując przepełnienie licznika 32-bit."""
    if t2 >= t1:
        return t2 - t1
    else:
        return (0xFFFFFFFF - t1) + t2 + 1
