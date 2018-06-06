# Distributed monitor

##### Projekt przygotowany w ramach przedmiotu NPR na Politechnice Poznańskiej

Projekt rozproszonego monitora z wykorzystaniem algorytmu Suzuki-Kasami.

## Wymagania
python 3.6

pyzmq  v17.0

`pip3 install zmq `

## Przykład wykorzystania prod.py i cons.py

Realizacja problemu producenta i konsumenta, startowany przez skrypt main.py.
Przykładowe wykonanie programu dla jednego producenta i dwóch konsumentów w pliku log.txt

Wywoływanie poszczególnych skryptów:
```shell
python3 	prod.py 	PROD_ID
python3 	cons.py 	CONS_ID
```
Identyfikatory muszą być unikalne dla każdego procesu.

Przed uruchomieniem należy także zmodyfikować odpowiednio plik configuration.py wprowadzając numery portów. Kolejność portów jest jednoznaczna z identyfikatorem procesu (PROD_ID = 0 => PORT = 12345).
```python
# determines number of nodes
PORTS = [
    12345,
    12346,
    12347,
    12348,
]
```

### Uruchomienie przykładu
`python3 main.py`
