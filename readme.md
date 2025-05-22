## 1. Funkcjonalność Lama

Lama jest narzędziem służącym do wykrywania nietypowych zdarzeń wykorzystującym metodę nauczania maszynowego. Źródłem informacji są logi urządzeń. Efektem działania jest alarm w postaci maila do administratora.
Aplikacja jest przeznaczona dla środowisk generujących bardzo dużą ilość logów. Na tyle dużą, że ich manualna analiza jest niemożliwa do wykonania.
Rdzeniem aplikacji jest biblioteka [Drain3]. Realizuje ona zadania związane z uczeniem maszynowym. Polecam zapoznanie się z dokumentacją tej biblioteki.

> Termin "False Positive"  -  w kontekście tej aplikacji termin ten oznacza alarmy, które nie informują o awarii. Przeznaczeniem tej aplikacji jest wyfiltrowanie zdarzeń, które są na prawdę ważne.

## 2. Elementy aplikacji

### 2.1. Źródło logów
Danymi wejściowymi dla aplikacji są pliki z bieżącymi logami. Powinny być one przygotowane przez serwer Syslog, taki jak Syslog-ng, Graylog i wiele innych. Dobrym rozwiązaniem będzie wstępne filtrowanie logów, np. w oparciu o **severity** (poziom ważności). Chodzi o to, aby trafiały do analizy tylko logi na prawdę istotne. Aplikacja zakłada, że dla każdego producenta urządzeń będziemy mieli oddzielne pliki z logami. Każdy z posiadanych przez nas typ urządzeń otrzyma charakterystyczną dla niego etykietę (tag). Na przykład jeśli chcemy analizować logi z urządzeń od trzech producentów Cisco, Palo Alto oraz F5, to możemy przyjąć etykiety 'cisco', 'palo', 'f5'. Te etykiet będą przewijać się w wielu miejscach konfiguracji. Natomiast jeśli chodzi o nazwy źródeł logów, czyli nazwy plików syslog'a, to powinny zgodne ze schematem _syslog-**tag**.log_ np. syslog-cisco.log.
###### Dlaczego warto separować logi w zależności od producenta urządzenia?
Każdy producent generuje logi dla swoich urządzeń według pewnego ogólnego schematu. Dzięki temu proces uczenia przebiega sprawniej. Generowana jest również mniejsza ilość False Positive.
*Uwaga*: Separacja logów nie jest bezwzględnie konieczna i być może w waszym środowisku nie będzie miała dużego znaczenia. Jeśli chcemy ograniczyć działanie aplikacji do jednego pliku, który zawiera logi wszystkich urządzeń, to możemy przyjąć jedną etykietę np. 'all'.

### 2.2. Analizator
Plik z bieżącymi logami (live logs), generowanymi przez serwis syslog, jest wejściem dla procesu analizatora.  
Analizator pracuje jako serwis Linux, którego plikiem wykonywalnym jest skrypt `lama_log_analizer.py`. Parametrem skryptu jest przyjęty wcześniej _tag_ oznaczający typ urządzenia (producenta). Jeśli chcemy na przykład analizować logi 3 producentów, to potrzebujemy utworzyć 3 serwisy.
 Przykład pliku konfiguracyjnego dla serwisu analizującego logi z urządzeń Cisco:
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
### 2.3. Alarmowanie
Powiadaminaiem administratorów o wykrytych anomaliach w logach zajmuje się skrypt _raport.py_. Skrypt powinien być uruchamiany co pewien czas z Crona. Ten czas powinien być odpowiednio krótki. Jedna minuta wydaje się optymalna. Mail zawiera log lub kilka logów, które zostały zinterpretowane jako anomalia. Skrypt _raport.py_ zawiera kilka mechanizmów chroniących skrzynkę pocztową administratora przed zalaniem:
- Ograniczenie wielkości maila do *max_lines* linijek.
- Maile są wysyłane nie częściej niż raz na minutę
- Każdy log umieszczony w mailu jest zapamiętywany pomiędzy kolejnymi wykonaniami skryptu. Nawet gdy pojawia się ciągle, to nie jest umieszczany w kolejnych mailach przez 1 godzinę. Jeśli po godzinie okaże się, że pojawia się nadal, to powyższa sekwencja powtarza się.

Z powyższego wynika, że nie wszystkie logi są umieszczane w mailach. Ale też nie takie jest zadanie tych powiadomień. Ich celem jest alarmowanie o nietypowych zdarzeniach. Szczegółowa analiza logów powinna być wykonywana za pomocą narzędzi do tego wyspecjalizowanych.

>Uwaga: Istnieje przypadek, w którym skrzynka pocztowa będzie ochroniona tylko przez dwa pierwsze mechanizmy. Mianowicie jeśli urządzenie zacznie wysyłać w dużej ilości logi spełniające następujące warunki:
> 1.Zawierają jakiś element zmienny np. identyfikator procesu, który zmienia się w każdym logu
> 2.Stanowią anomalię
> W konsekwencji co jedną minutę będą wysyłane maile aż do momentu rozwiązania problemu.

### 2.4. Trenowanie
Algorytm wykrywania anomalii jest oparty na nauczaniu maszynowym. Wymagane jest więc trenowanie systemu. W przypadku metodologii przyjętej w tej aplikacji, trenowanie polega na informowaniu algorytmu nauczania maszynowego, które logi są normą, nie są anomalią. Za proces trenowania odpowiada skrypt *train*. Skrypt wymaga podania dwów argumentów. Pierwszy to plik z logami, który uznaliśmy za normalne. Drugi argument to wcześniej przyjęty tag oznaczający typ urządzeń, które wyprodukowały obrabiane logi.
Sekwencja komend:
```
sudo systemctl <stop systemd_service_name>
./train <file_with_logs> <tag>
sudo systemctl start <systemd_service_name>
```
gdzie:
*systemd_service_name* - nazwa serwisu *systemd* analizującego logi danego typu urządzeń
*file_with_logs* - plik z logami urządzeń Cisco, które uznajemy za normę
*tag* - etykieta przyjęta dla danego typu urządzeń

###### Strategia dla pierwszej operacji trenowania
Jak wcześniej wspomniano aplikacja jest przeznaczona dla środowisk, które generują bardzo dużą ilość logów. Zdecydowana większość z nich nie świadczy o awarii. Mogą to być logi świadczące o pewnych niedomaganiach, błędach konfiguracyjnych, błedach w oprogramowaniu, ale nie o awariach. Logi świadczące o awariach zdarzają się stosunkowo rzadko. Pierwsza porcja logów, którymi musimy wytrenować system będzie więc bardzo duża. Jaką strategię powinniśmy przyjąć, aby ten proces był w miarę prosty i jednocześnie skuteczny? Zapewne może być ich wiele. Koncepcja, ktorą ja zastosowałem i która w moim przypadku okazała się skuteczna jest następująca:
1. Zarchiwizować pliki z logami z całego dnia roboczego (w sensie nie weekend-owego)
2. Odczekać jeden dzień, w którym oczekujemy na sygnały o podejrzanych zdarzeniach i sami szukamy takich zdarzeń w systemach monitorujących
3. Jeśli nie pojawiły się sygnały o niepokojących zdarzeniach, wykonać operację pierwszego trenowania używając do tego celu zarchiwizowane wcześniej logi

W następnych dniach zapewne pojawią się alarmy, które okażą się False Positive'ami. Należy wykonywać na nich operację trenowania. Z każdym dniem takich False Positive'ów będzie mniej, aż do ustabilizowania systemu. 

### 2.4. Wycofywanie wcześniej wytrenowanych logów
Algorytm Drain3 nie przewiduje wycofywania wcześniej wytrenowanych informacji. Aby uzyskać taką funkcjonalność aplikacja odkłada na boku logi, które zostały poddane procesowi treningu. Zapisywana jest przy tym kolejność w jakiej te logi zostały wytrenowane oraz odpowiadające im stany uczenia maszynowego.  Mając takie informacje można przeprowadzić powrót do stanu sprzed trenowania problematycznego logu. Operację taką wykonuje skrypt *revert*.
```
./revert.py <tag> "<text_to_find>"
```
gdzie:
*tag* - etykieta przyjęta dla danego typu urządzeń,
*text_to_find* - fragment logu, którego chcemy się pozbyć; powinien być na tyle długi i specyficzny, aby możliwe było precyzyjne wyszukanie dokładniego tego logu, o który nam chodzi.

### 2.5. Pamięć modelu
Wiedza na temat wyuczonych przez nauczanie maszynowe wzorców zachowywana jest w plikach _drain3\_state\_<tag>_.bin. Jest to swego rodzaju pamięć pamięć tego co model sięnauczył. Pliki te stanowią dużą wartość, ponieważ ich utrata lub uszkodzenie powoduje utratę całej wiedzy zebranej w trakcie nauki. Skrypt _lamarchive_ wykonuje archiwizację plików *.bin w katalogu wyspecyfikowanym w _config.ini_ jako wartość zmiennej _arch\_dir_. Liczbę utrzymywanych kopii ustawiamy w  _max\_copies_. Skrypt może być uruchamiany przez serwis _Cron_ np.
```
0 2 * * 1-5 lamauser /opt/lama/lamarchive
```
## 3. Konfiguracja systemu
#### 3.1. Plik config.ini
```
[persistance]
persistance_dir=/var/lama/
hash_dir=/var/lama/arch/hashes/
file_list=/var/lama/archlist
trained_dir=/var/lama/trained/
arch_dir=/var/lama/arch/
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
#### 3.2. Plik drain3.ini
Plik zawiera parametry definiujące działanie modułu Drain3. Sczegóły są opisane w dokumentacji modułu. Szczególnie interesujący jest segment MASKING. Definiuje on reguły maskowania tych fragmentów logów, które często się zmieniają, a przy tym nie są dla nas interesujące. Dzięki temu algorytm generuje mniej False Positive, ponieważ łatwiej jest podjąć decyzję, czy dany fragment ma być parametrem wzorca, czy częścią treści loga. Chodzi tu o maskowanie na etapie uczenia maszynowego, a konkretnie podczas tworzenia sparametryzowanych wzorców. Te wzorce są używane do rozpoznania, czy dany log jest anomalią. Nie jest to natomiast maskowanie treści logów, które przychodzą w alertach. Te są przesyłane z oryginalną treścią. Na przykład jeśli mamy kilka identycznych urządzeń, to dla modelu wykrywania anomalii nie będzie interesujące, dla którego urządzenia zostanie wykryta anomalia. Dlatego możemy zazwyczaj bez ryzyka zamaskować nazwy tych urządzeń. Plik drain3.ini dołączony do repozytorium uwzglęnia urządzenia F5, Cisco i Palo Alto. Należy jednak pamiętać, że w każdym środowisku te reguły będą miały swojąwłasną specyfikę.

## 4. Krótka instrukcja instalacji
1. Podziel twoje urządzenia na grupy i nadaj im tagi (np. cisco, paloalto, f5).
2. Zmodyfikuj config.ini zgodnie z własnymi wymaganiami i utwórz wymienione w nim katalogi.
3. Skonfiguruj Syslog tak, aby kierował komunikaty syslog do dedykowanych dla każdego typu urządzeń plików. Nazwy plików muszą być zgodne ze schematem _syslog-**tag**.log_
4. Utwórz serwisy _systemd_ dla każdego typu urządzeń.
5. Dodaj do Cron-a skrypt _raport.py_
6. Dodaj do Cron-a skrypt _lamarchive_
7. Wykonaj pierwszą operację trenowania uczenia maszynowego (skrypt *train*)

## 5. Schemat działania systemu
![Alt Text](schema.jpg)

[//]: # (Biblioteka linków)

[Drain3]: <https://github.com/logpai/Drain3>
