# Historia Pojazdu dla Home Assistant

![Logo Historia Pojazdu](https://raw.githubusercontent.com/jarekgrzabel/ha-historia-pojazdu/main/custom_components/historia_pojazdu/brand/icon.png)

Nieoficjalna integracja odczytuje datę ważności OC i następnego badania technicznego z Historia Pojazdu. Nie wymaga MQTT, dodatku ani sterowania przeglądarką. Kod protokołu i parser powstały na podstawie [historia-pojazdu-sdk](https://github.com/Korea77/historia-pojazdu-sdk), commit `1f4c496ef728011903b308dfa90d74409da05740`; udostępniane są na licencji GPL-3.0 (plik LICENSE).

## Instalacja i konfiguracja

1. Utwórz kopię zapasową Home Assistant i zachowaj poprzednią wersję katalogu `custom_components/historia_pojazdu`, jeśli istnieje.
2. Zainstaluj katalog `custom_components/historia_pojazdu` z tego repozytorium w analogicznym katalogu konfiguracji Home Assistant, albo dodaj to repozytorium jako niestandardowe repozytorium integracji HACS. Przy pierwszej instalacji konieczne może być ponowne uruchomienie HA.
3. W Ustawieniach → Urządzenia i usługi → Dodaj integrację wybierz Historia Pojazdu. Dodaj osobny wpis dla każdego samochodu, podając nazwę, rejestrację, VIN i datę pierwszej rejestracji w formacie RRRR-MM-DD.
4. Sprawdź utworzone encje oraz ich stan pobierania. Odrębną automatyzację powiadomień skonfiguruj dopiero po sprawdzeniu nazw encji i dostępności właściwej akcji powiadomienia.

Integracja udostępnia sensory ważności OC, następnego badania technicznego, ostatniej w pełni udanej aktualizacji i stanu pobierania oraz przycisk Odśwież dane. Identyfikatory są stabilne w obrębie wpisu integracji. Wartości pobierane są podczas uruchomienia wpisu w tle i co 24 godziny, a także po naciśnięciu przycisku. Godzina aktualizacji zależy od działania HA; udane jednorazowe pobranie nie dowodzi działania całego dobowego harmonogramu.

Każdy sensor daty ma atrybut `aktualnosc`: `aktualne` po udanym pobraniu danej daty albo `zapisane lub nieaktualne`, gdy dane przywrócono z zapisu lub pobranie tej daty nie powiodło się. Sensor stanu opisuje problem. Czas ostatniej udanej aktualizacji oznacza pobranie obu dat; aktualizacja częściowa go nie zmienia. Nieznana data OC nie oznacza braku polisy. Zapisane daty są przechowywane w lokalnej pamięci HA po restarcie i nie są usuwane w razie błędu. Jeśli ostatnie zdarzenie badania nie zawiera jednoznacznego terminu, poprzedni termin nie zostanie potraktowany jako świeży.

## Bezpieczeństwo i ograniczenia

Połączenia HTTPS weryfikują certyfikat. Każda próba ma ograniczony czas, a kolejne próby są rozdzielone odstępami. Wpis integracji zawiera podane dane pojazdu; chroń dostęp do konfiguracji i kopii zapasowych HA. Do pamięci trwałej trafiają wyłącznie daty oraz czas aktualizacji. Integracja nie zapisuje pełnych raportów, tokenów ani VIN w zwykłych logach. Interfejs serwisu jest nieoficjalny i może ulec zmianie; nie należy traktować integracji jako jedynego potwierdzenia ważności dokumentów.

## Wycofanie

Wyłącz lub usuń automatyzację powiadomień utworzoną dla integracji, usuń wpisy Historia Pojazdu w ustawieniach HA, a następnie usuń katalog integracji lub przywróć jego poprzednią kopię. W razie potrzeby uruchom HA ponownie. Te kroki nie wymagają zmian w MyToyota ani automatyzacji serwisu producenta. Usunięcie wpisów usuwa ich urządzenia i encje; kopia zapasowa pozwala przywrócić wcześniejszy stan.

## Testy

`python -m unittest discover -s tests` (wymaga `aiohttp`). Zestaw obejmuje format odpowiedzi, wcześniejsze i późniejsze badania, brak lub niejednoznaczność dat oraz błędną odpowiedź. Konieczne są też testy w działającym HA, w tym przywrócenie zapisanych wartości i obsługa nieudanego pobrania.
