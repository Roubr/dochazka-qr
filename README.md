# Docházkový systém pro QR čtečky (Proof of Concept)

Jednoduchá docházková webová aplikace postavená na frameworku Flask. Tento projekt momentálně slouží jako **Proof of Concept (PoC)** pro ověření integrace hardwarové USB QR čtečky (fungující jako emulátor klávesnice) se záznamovým webovým systémem.

## Funkce
* **Evidence příchodů a odchodů**: Rychlé logování stavu přes naskenovaný QR kód.
* **Sledování důvodů**: Možnost specifikovat důvod odchodu nebo příchodu.
* **Lokální databáze**: Bezbariérové ukládání do SQLite (databáze se vytvoří automaticky při prvním spuštění).
* **Responzivní UI**: Přehledné webové rozhraní pro kontrolu logů.

## Prerekvizity
* Python 3.8 a novější
* QR čtečka (podporující vstup jako standardní USB klávesnice)

## Instalace a spuštění (Linux/macOS)

1. **Naklonování repozitáře**
   ```bash
   git clone https://github.com/Roubr/dochazka-qr.git
   cd dochazka-qr
   ```

2. **Vytvoření virtuálního prostředí**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instalace závislostí**
   ```bash
   pip install -r requirements.txt
   ```

4. **Spuštění aplikace**
   ```bash
   python3 dochazka.py
   ```
   Aplikace standardně poběží na `http://127.0.0.1:5000` (případně na lokální IP adrese stroje v rámci vaší sítě, pokud je aplikace nastavená pro poslech na všech rozhraních).
