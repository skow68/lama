## Funkcjonalność Lama

Lama jest narzędziem służącym do wykrywania nietypowych zdarzeń wykorzystującym metodę nauczania maszynowego. Źródłem informacji są logi urządzeń. Efektem działania jest alarm w postaci maila do administratora.
Aplikacja jest przeznaczone dla środowisk generujących bardzo dużą ilość logów, niemożliwą do manualnej analizy.

> Termin "False Positive"  -  w kontekście tej aplikacji termin ten oznacza alarmy, które nie informują o awarii. Przeznaczeniem tej aplikacji jest wyfiltrowanie zdarzeń, które są na prawdę ważne.

## Elementy aplikacji

### Źródło logów
Danymi wejściowymi dla aplikacji są pliki z bieżącymi logami. Powinny być one przygotowane przez serwer Syslog, taki jak Syslog-ng, Graylog i wiele innych. Dobrym rozwiązaniem będzie wstępne filtrowanie logów, np. w oparciu o **severity** (poziom ważności). Chodzi o to, aby trafiały do analizy tylko logi na prawdę istotne. Aplikacja zakłada, że dla każdego producenta urządzeń będziemy mieli oddzielne pliki z logami. Każdy z posiadanych przez nas typ urządzeń otrzyma charakterystyczną dla niego etykietę (tag). Na przykład jeśli chcemy analizować logi z urządzeń od trzech producentów Cisco, Palo Alto oraz F5, to możemy przyjąć etykiety 'cisco', 'palo', 'f5'. Te etykiet będą przewijać się w wielu miejscach konfiguracji. Natomiast jeśli chodzi o nazwy źródeł logów, czyli nazwy plików syslog'a, to powinny zgodne ze schematem _syslog-**tag**.log_ np. syslog_cisco.log.
###### Dlaczego warto separować logi w zależności od producenta urządzenia?
Każdy producent generuje logi dla swoich urządzeń według pewnego ogólnego schematu. Dzięki temu proces uczenia przebiega sprawniej. Generowana jest również mniejsza ilość False Positive.
*Uwaga*: Separacja logów nie jest bezwzględnie konieczna i być może w waszym środowisku nie będzie miała dużego znaczenia. Jeśli chcemy ograniczyć działanie aplikacji do jednego pliku, który zawiera logi wszystkich urządzeń, to możemy przyjąć jedną etykietę np. 'all'.

### Analizator
Plik z bieżącymi logami (live logs), generowanymi przez serwis syslog, jest wejściem dla procesu analizatora.  
Analizator pracuje jako serwis Linux, którego plikiem wykonywalnym jest skrypt `lama_log_analizer.py`. Parametrem skryptu powien być tag producenta. Czyli dla przykładu jeśli chcemy analizować logi 3 producentów, to pottrzebujemy utworzyć 3 serwisy.
 Przykład pliku konfiguracyjnego dla logów z urządzeń Cisco:
```
[Unit]
Description=Lama Log Processor Service
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
### Alarmowanie
Powiadaminaiem administratorów o wykrytych anomaliach w logach zajmuje się skrypt _raport.py_. Skrypt powinien być uruchamiany co pewien czas z Crona. Ten czas powinien być odpowiednio krótki. Jedna minuta wydaje się optymalna. Skrypt _raport.py_ zawiera kilka mechanizmów chroniących skrzynkę pocztową administratora przed zalaniem:
- Mechanizm 1
- Mechanizm 2
- Mechanizm 3

### Trenowanie
Algorytm wykrywania anomalii jest oparty na nauczaniu maszynowym. Wymagane jest więc wytrenowanie systemu
Sekwencja komend:
```
sudo systemctl stop lama_cisco
./train my_file.txt cisco
sudo systemctl start lama_cisco
```
gdzie:
*lama_cisco* - nazwa serwisu systemd analizującego logi Cisco
*my_file.txt* - plik z logami, które uznajemy za nie interesujące

###### Strategia dla pierwszej operacji trenowania
Jak wcześniej wspomniano aplikacja jest przeznaczona dla środowisk, które generują bardzo dużą ilość logów.

### Wycofywanie wcześniej nauczonych logów

## Konfiguracja systemu
#### Plik config.ini
```
[persistance]
persistance_dir=/var/lama/
arch_dir=/var/lama/arch/
hash_dir=/var/lama/arch/hashes/
file_list=/var/lama/archlist
trained_dir=/var/lama/trained/
max_copies=30
 
[files]
alarm_cache=/var/log/lama/
day_alarm_cache=/var/log/lama/day_alarm_cache.log
lama_log=/var/log/lama/lama.log
shelf_file=/var/lama/hashes.shlv
 
[email]
sender=lama@example.com
receiver=soemone@example.com
subject=Alarm
smtp_server=smtp.example.com
smtp_port=25
max_lines=100
 
[syslog]
syslog_dir=/var/log/
```
#### Plik drain3.ini
Plik zawiera parametry definiujące działanie modułu Drain3. Sczegóły są opisane w dokumentacji modułu. W załączonym przykładzie ...

## Schemat działania systemu
![Alt Text](schema.jpg)
