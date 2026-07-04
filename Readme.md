# Wibroakustyczny System Pomiarowy - Timegrapher (Projekt Inżynierski)

Projekt składa się z dwóch integralnych części:
1. **Firmware** - oprogramowanie dla mikrokontrolera Raspberry Pi Pico, odpowiedzialne za akwizycję sygnałów z analogowego toru pomiarowego (czujnik piezoelektryczny).
2. **Aplikacja PC (Python)** - interfejs graficzny użytkownika (GUI) do odbioru, analizy i wizualizacji danych pomiarowych z mechanizmów zegarkowych.

---

## 🛠 Wymagania wstępne (Prerequisites)

Dostarczone oprogramowanie mikrokontrolera jest już skompilowane. Aby uruchomić interfejs PC, wymagane jest jedynie:
* **Dla aplikacji PC:** Środowisko `Python 3.10` (lub nowszy).

---

## 💻 1. Uruchomienie części sprzętowej (Katalog: `timegrapher_firmware`)

W tym katalogu znajduje się gotowy, skompilowany plik z oprogramowaniem (format `.uf2`) dla mikrokontrolera Raspberry Pi Pico.

**Wgrywanie na urządzenie (Flashing):**
1. Odłącz Raspberry Pi Pico od komputera[cite: 5].
2. Wciśnij i przytrzymaj biały przycisk **BOOTSEL** na płytce Pico[cite: 5].
3. Trzymając przycisk, podłącz Pico do komputera kablem USB, a następnie zwolnij przycisk[cite: 5]. Pico pojawi się w systemie jako dysk masowy (np. `RPI-RP2`)[cite: 5].
4. Wejdź do folderu `timegrapher_firmware` i skopiuj znajdujący się tam plik z rozszerzeniem `.uf2` (np. `timegrapher_firmware.uf2`) bezpośrednio na dysk Pico[cite: 5]. Urządzenie zrestartuje się automatycznie i będzie gotowe do pracy[cite: 5].

---

## 🐍 2. Uruchomienie aplikacji analizującej (Katalog: `timegrapher`)

W tym katalogu znajduje się aplikacja okienkowa napisana w języku Python[cite: 5]. Zastosowano środowisko wirtualne w celu izolacji zależności[cite: 5].

**Instalacja i uruchomienie (Terminal / Wiersz poleceń):**

1. Przejdź do folderu z aplikacją[cite: 5]:
   ```bash
   cd timegrapher