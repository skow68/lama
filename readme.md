## Funkcjonalność Lama

Lama jest narzędziem służącym do wykrywania nietypowych zdarzeń wykorzystującym metodę nauczania maszynowego. Źródłem informacji są logi urządzeń. Efektem działania jest alarm w postaci maila do administratora.
Aplikacja jest przeznaczona dla środowisk generujących bardzo dużą ilość logów. Na tyle dużą, że ich manualna analiza jest niemożliwa do wykonania.
Rdzeniem aplikacji jest biblioteka [Drain3]. Realizuje ona zadania związane z uczeniem maszynowym. Polecam zapoznanie się z dokumentacją tej biblioteki.

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
Powiadaminaiem administratorów o wykrytych anomaliach w logach zajmuje się skrypt _raport.py_. Skrypt powinien być uruchamiany co pewien czas z Crona. Ten czas powinien być odpowiednio krótki. Jedna minuta wydaje się optymalna. Mail zawiera log lub kilka logów, które zostały zinterpretowane jako anomalia. Skrypt _raport.py_ zawiera kilka mechanizmów chroniących skrzynkę pocztową administratora przed zalaniem:
- Ograniczenie wielkości maila do *max_lines* linijek.
- Maile są wysyłane nie częściej niż raz na minutę
- Każdy log umieszczony w mailu jest zapamiętywany pomiędzy kolejnymi wykonaniami skryptu. Nawet gdy pojawia się ciągle, to nie jest umieszczany w kolejnych mailach przez 1 godzinę. Jeśli po godzinie okaże się, że pojawia się nadal, to powyższa sekwencja powtarza się.

Z powyższego wynika, że nie wszystkie logi są umieszczane w mailach. Ale też nie takie jest zadanie tych maili. Ich celem jest powiadamianie o nietypowych zdarzeniach. Szczegółowa naliza logów powinna być wykonywana za pomocą narzędzi do tego wyspecjalizowanych.

>Uwaga: Istnieje jeden przypadek, w którym skrzynka pocztowa będzie ochroniona tylko przez dwa pierwsze mechanizmy. Mianowicie jeśli urządzenie zacznie wysyłać w dużej ilości logi spełniające dwa warunki:
> -zawierają jakiś element zmienny np. identyfikator procesu, który zmienia się w każdym logu
> -są anomalią
> Czyli w konsekwencji co jedną minutę będą wysyłane maile aż do momentu rozwiązania problemu.



### Trenowanie
Algorytm wykrywania anomalii jest oparty na nauczaniu maszynowym. Wymagane jest więc trenowanie systemu. W przypadku metodologii przyjętej w tej aplikacji, trenowanie polega na informowaniu algorytmu nauczania maszynowego, które logi są normą, nie są anomalią. Za proces trenowania odpowiada skrypt *train*. Skrypt wymaga podania dwów argumentów. Pierwszy to plik z logami, który uznaliśmy za normalne. Drugi argument to wcześniej przyjęty tag oznaczający typ urządzeń, które wyprodukowały obrabiane logi.
Sekwencja komend:
```
sudo systemctl stop lama_cisco
./train file_with_cisco_logs.log cisco
sudo systemctl start lama_cisco
```
gdzie:
*lama_cisco* - nazwa serwisu systemd analizującego logi Cisco
*my_file.txt* - plik z logami urządzeń Cisco, które uznajemy za normę

###### Strategia dla pierwszej operacji trenowania
Jak wcześniej wspomniano aplikacja jest przeznaczona dla środowisk, które generują bardzo dużą ilość logów. Zdecydowana większość z nich nie świadczy o awarii. Mogą to być logi świadczące o pewnych niedomaganiach, błędach konfiguracyjnych, błedach w oprogramowaniu, ale nie o awariach. Logi świadczące o awariach zdarzają się stosunkowo rzadko. Pierwsza porcja logów, którymi musimy wytrenować system będzie więc bardzo duża. Jaką strategię powinniśmy przyjąć, aby ten proces był w miarę prosty i jednocześnie skuteczny? Zapewne może być ich wiele. Koncepcja, ktorą ja zastosowałem i która w moim przypadku okazała się skuteczna jest następująca:
1. Zarchiwizować pliki z logami z całego dnia roboczego (w sensie nie weekend-owego)
2. Odczekać jeden dzień, w którym oczekujemy na sygnały o podejrzanych zdarzeniach i sami szukamy takich zdarzeń w systemach monitorujących
3. Jeśli nie pojawiły się sygnały o niepokojących zdarzeniach, wykonać operację pierwszego trenowania używając do tego celu zarchiwizowane wcześniej logi

W następnych dniach zapewne pojawią się alarmy, które okażą się False Positive'ami. Należy wykonywać na nich operację trenowania. Z każdym dniem takich False Positive'ów będzie mniej, aż do ustabilizowania systemu. 

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

## Krótka instrukcja instalacji

1. 

## Schemat działania systemu
![Alt Text](schema.jpg)

[//]: # (Biblioteka linków)

[Drain3]: <https://github.com/logpai/Drain3>
