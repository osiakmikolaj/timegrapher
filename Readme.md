# Wibroakustyczny System Pomiarowy - Timegrapher (Projekt Inżynierski)

Projekt składa się z dwóch integralnych części:
1. **Firmware (C/C++)** - oprogramowanie dla mikrokontrolera Raspberry Pi Pico, odpowiedzialne za akwizycję sygnałów z analogowego toru pomiarowego (czujnik piezoelektryczny).
2. **Aplikacja PC (Python)** - interfejs graficzny użytkownika (GUI) do odbioru, analizy i wizualizacji danych pomiarowych z mechanizmów zegarkowych.

---

## 🛠 Wymagania wstępne (Prerequisites)

Aby skompilować i uruchomić projekt na nowym komputerze, wymagane są:
* **Dla części sprzętowej:** 
  * Narzędzia budowania: `CMake`, `Ninja`
  * Kompilator ARM: `arm-none-eabi-gcc`
  * Skonfigurowane środowisko: `pico-sdk`
* **Dla aplikacji PC:**
  * Środowisko `Python 3.10` (lub nowszy)

---

## 💻 1. Uruchomienie części sprzętowej (Katalog: `Pico_test`)

W tym katalogu znajduje się kod w C/C++ dla mikrokontrolera Raspberry Pi Pico.

**Kompilacja za pomocą VS Code:**
1. Otwórz folder `Pico_test` w edytorze Visual Studio Code.
2. Upewnij się, że masz zainstalowane rozszerzenie **CMake Tools**.
3. Rozszerzenie powinno automatycznie wykryć plik `CMakeLists.txt` i zapytać o konfigurację (wybierz zestaw kompilatorów dla `arm-none-eabi`).
4. Kliknij przycisk **Build** (na dolnym pasku VS Code). Zostanie wygenerowany folder `build`.

**Wgrywanie na urządzenie (Flashing):**
1. Odłącz Raspberry Pi Pico od komputera.
2. Wciśnij i przytrzymaj biały przycisk **BOOTSEL** na płytce Pico.
3. Trzymając przycisk, podłącz Pico do komputera kablem USB, a następnie zwolnij przycisk. Pico pojawi się w systemie jako dysk masowy (np. `RPI-RP2`).
4. Wejdź do wygenerowanego folderu `build` i skopiuj plik z rozszerzeniem `.uf2` (np. `timegrapher_firmware.uf2`) bezpośrednio na dysk Pico. Urządzenie zrestartuje się automatycznie.

---

## 🐍 2. Uruchomienie aplikacji analizującej (Katalog: `timegrapher`)

W tym katalogu znajduje się aplikacja okienkowa napisana w języku Python. Zastosowano środowisko wirtualne w celu izolacji zależności.

**Instalacja i uruchomienie (Terminal / Wiersz poleceń):**

1. Przejdź do folderu z aplikacją:
   ```bash
   cd timegrapher