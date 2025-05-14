## Funkcjonalność Lama
Lama jest narzędziem służącym do:
- Wykrywania nietypowych zdarzeń.
- Powiadamiania administratora o nietypowym zdarzeniu.

**Ogólny cel**: Wyfiltrowanie logów z dużych zbiorów danych.

**Przeznaczenie**: Dla środowisk generujących bardzo dużą ilość logów, niemożliwych do manualnej analizy.
---
## Termin "False Positive"
W kontekście tej aplikacji termin ten oznacza alarmy, które nie informują o awarii.

---

## Elementy aplikacji

### Źródło logów
Danymi wejściowymi dla aplikacji są pliki z bieżącymi logami. Powinny być one przygotowane przez serwer Syslog, taki jak Syslog-ng, Graylog i wiele innych. Dobrym rozwiązaniem będzie wstępne filtrowanie logów, np. w oparciu o **severity** (poziom ważności). Chodzi o to, aby trafiały do analizy tylko logi na prawdę istotne. Aplikacja przewiduje, że dla każdego producenta urządzeń będziemy mieli oddzielne pliki z logami.
# Dlaczego warto separować logi w zależności od producenta urządzenia?
Każdy producent generuje logi dla swoich urządzeń według pewnego ogólnego schematu. Dzięki temu proces uczenia przebiega sprawniej. Generowana jest również mniejsza ilość False Positive.
**Uwaga**: Nie jest to konieczne i być może w waszym środowisku nie będzie to miało znaczenia.

### Analizator
Plik z bieżącymi logami (live logs), generowanymi przez serwis syslog, jest wejściem dla procesu analizatora.  
Analizator pracuje jako serwis Linux, którego rdzeniem jest program `lama_log_analizer.py`. 

#### Przykład pliku konfiguracyjnego dla logów z urządzeń Cisco:
```plaintext
[Unit]
Description=Log Processor Service
After=network.target
[Service]
ExecStart=/opt/lama/log_processor.py cisco
WorkingDirectory=/opt/lama/
User=lamauser
Group=lamauser
Restart=on-failure
Environment=PYTHONUNBUFFERED=1
[Install]
WantedBy=multi-user.target
```
## Schemat działania systemu
![Alt Text](schema.jpg)
