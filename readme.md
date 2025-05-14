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

### Źródło logów dla aplikacji
Danymi wejściowymi dla aplikacji są pliki z bieżącymi logami. Powinny być one przygotowane przez serwer Syslog, taki jak Syslog-ng, Graylog i wiele innych. Dobrym rozwiązaniem będzie wstępne filtrowanie logów, np. w oparciu o **severity** (poziom ważności). Chodzi o to, aby trafiały do analizy tylko logi na prawdę istotne. Aplikacja zakłada, że dla każdego producenta urządzeń będziemy mieli oddzielne pliki z logami. Każdy z posiadanych przez nas typ urządzeń otrzyma charakterystyczną dla niego etykietę (tag). Na przykład jeśli chcemy analizować logi z urządzeń od trzech producentów Cisco, Palo Alto oraz F5, to możemy przyjąć etykiety 'cisco', 'palo', 'f5'. Te etykiet będą przewijać się w wielu miejscach konfiguracji. Natomiast jeśli chodzi o nazwy źródeł logów, czyli nazwy plików syslog'a, to powinny zgodne ze schematem *syslog_<tag>.log* np. syslog_cisco.log.
##### Dlaczego warto separować logi w zależności od producenta urządzenia?
Każdy producent generuje logi dla swoich urządzeń według pewnego ogólnego schematu. Dzięki temu proces uczenia przebiega sprawniej. Generowana jest również mniejsza ilość False Positive.
*Uwaga*: Nie jest to konieczne i być może w waszym środowisku nie będzie to miało znaczenia. Jeśli chcemy ograniczyćdziałanie aplikacji do jednego pliku, który zawiera logi wszystkich urządzeń, to możemy przyjąć jednąetykietęnp. 'all'.

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
