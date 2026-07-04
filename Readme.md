# Wibroakustyczny System Pomiarowy - Timegrapher (Projekt Inżynierski)

Projekt składa się z dwóch integralnych części:
1. **Firmware** - oprogramowanie dla mikrokontrolera Raspberry Pi Pico, odpowiedzialne za akwizycję sygnałów z analogowego toru pomiarowego (czujnik piezoelektryczny). Pełny kod źródłowy dostępny jest w osobnym repozytorium: [osiakmikolaj/timegrapher_firmware](https://github.com/osiakmikolaj/timegrapher_firmware).
2. **Aplikacja PC (Python)** - interfejs graficzny użytkownika (GUI) do odbioru, analizy i wizualizacji danych pomiarowych z mechanizmów zegarkowych.

---

## 🛠 Wymagania wstępne (Prerequisites)

Dostarczone oprogramowanie mikrokontrolera jest już skompilowane. Aby uruchomić interfejs PC, wymagane jest jedynie:
* **Dla aplikacji PC:** Środowisko `Python 3.10` (lub nowszy).

---

## 💻 1. Uruchomienie części sprzętowej (Katalog: `timegrapher_firmware`)

W tym katalogu znajduje się gotowy, skompilowany plik z oprogramowaniem (format `.uf2`) dla mikrokontrolera Raspberry Pi Pico. 

*Uwaga: Osobny kod źródłowy (C/C++) oraz konfiguracja środowiska CMake dla mikrokontrolera znajdują się w repozytorium na GitHubie: [https://github.com/osiakmikolaj/timegrapher_firmware](https://github.com/osiakmikolaj/timegrapher_firmware).*

**Wgrywanie na urządzenie (Flashing):**
1. Odłącz Raspberry Pi Pico od komputera.
2. Wciśnij i przytrzymaj biały przycisk **BOOTSEL** na płytce Pico.
3. Trzymając przycisk, podłącz Pico do komputera kablem USB, a następnie zwolnij przycisk. Pico pojawi się w systemie jako dysk masowy (np. `RPI-RP2`).
4. Skopiuj plik z rozszerzeniem `.uf2` (`timegrapher_firmware.uf2`) bezpośrednio na dysk Pico. Urządzenie zrestartuje się automatycznie i będzie gotowe do pracy.

---

## 🐍 2. Uruchomienie aplikacji analizującej (Katalog: `timegrapher`)

W tym katalogu znajduje się aplikacja okienkowa napisana w języku Python. Zastosowano środowisko wirtualne w celu izolacji zależności.

**Instalacja i uruchomienie (Terminal / Wiersz poleceń):**

1. Przejdź do folderu z aplikacją:
   ```bash
   cd timegrapher