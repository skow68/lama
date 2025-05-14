# Lama

## Termin "False Positive"
W kontekście tej aplikacji termin ten oznacza alarmy, które nie informują o awarii.

## Dlaczego warto separować logi w zależności od producenta urządzenia?
Każdy producent generuje logi dla swoich urządzeń według pewnego ogólnego schematu.

Dzięki temu:
- Proces uczenia przebiega sprawniej.
- Generowana jest mniejsza ilość False Positive.

**Uwaga**: Nie jest to konieczne i być może w waszym środowisku nie będzie to miało znaczenia.

---

## Funkcjonalność Lama
Lama jest narzędziem służącym do:
- Wykrywania nietypowych zdarzeń.
- Powiadamiania administratora o nietypowym zdarzeniu.

**Ogólny cel**: Wyfiltrowanie logów z dużych zbiorów danych.

**Przeznaczenie**: Dla środowisk generujących bardzo dużą ilość logów, niemożliwych do manualnej analizy.

---

## Elementy aplikacji

### Źródło logów
Danymi wejściowymi dla aplikacji są pliki z bieżącymi logami.  
Powinny być one przygotowane przez serwer Syslog, taki jak:
- Syslog-ng
- Graylog
- Inne serwery zgodne z Syslog

Dobrym rozwiązaniem będzie wstępne filtrowanie logów, np. w oparciu o **severity** (poziom ważności).

### Analizator
Plik z bieżącymi logami (live logs), generowanymi przez serwis syslog, jest wejściem dla procesu analizatora.  
Analizator pracuje jako serwis Linux, którego rdzeniem jest program `lama_log_analizer.py`.

#### Przykład pliku konfiguracyjnego:
```plaintext
# Tu można dodać przykładowy plik konfiguracyjny
