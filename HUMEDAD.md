# Humedad en el tostado: por qué usar humedad **absoluta** y no **relativa**

Guía sencilla para entender qué mide el PyRoaster y por qué, en el contexto de
tostar café, cacao, maní y otros granos.

## El problema en una frase

> La **humedad relativa (RH%)** cambia con la temperatura aunque el aire lleve
> exactamente la misma cantidad de agua. En un escape caliente, eso la vuelve
> **engañosa**. La **humedad absoluta** y el **punto de rocío** no tienen ese
> problema: miden el agua *de verdad*.

## La analogía del balde

Imagina el aire como un **balde que carga agua** — y el truco es:
**el balde se hace más grande cuando hace más calor.** El aire caliente "cabe"
mucha más agua que el frío.

- **Humedad relativa (RH%)** = qué tan **lleno** está el balde (en %).
- **Humedad absoluta (g/m³)** = cuánta agua **hay realmente** en el balde.
- **Punto de rocío (°C)** = a qué temperatura el balde se **llenaría al 100%**;
  otra forma de decir "cuánta agua hay", pero en grados.

Como el **tamaño del balde cambia con la temperatura**, el porcentaje (RH)
engaña. Los otros dos no: reflejan el agua real.

## El ejemplo que lo deja claro

Toma un aire a **20 °C y 55 % RH** (una lectura típica del sensor):

| Acción | Temp | RH % | Humedad absoluta | Punto de rocío |
|---|---|---|---|---|
| Aire original | 20 °C | **55 %** | ~9.5 g/m³ | ~10.7 °C |
| Lo calientas a 40 °C (misma agua) | 40 °C | **~17 %** | ~8.9 g/m³ | ~10.7 °C |

Fíjate: **la RH se desplomó de 55 % a 17 % solo por calentar**, aunque el agua es
la misma. El **punto de rocío no se movió nada** (10.7 °C) y la **humedad absoluta
apenas bajó** (9.5 → 8.9 g/m³, por la expansión del aire caliente). Los dos
reflejan que el agua es prácticamente la misma; **la RH la exagera**. Eso es justo
lo que pasa en el ducto de escape caliente: la RH% se ve baja aunque el aire lleve
mucha humedad del grano.

> **Matiz:** el **punto de rocío** es *estrictamente* independiente de la
> temperatura; la **humedad absoluta (g/m³)** varía un poquito (el aire caliente
> se expande), pero muchísimo menos que la RH. Ambos sirven de sobra; el punto de
> rocío es el más "limpio".

## Por qué importa MÁS al tostar distintos granos

Cada grano se tuesta a una temperatura distinta, así que el **aire de escape
sale a temperaturas distintas**:

| Grano | Temp típica de tostado |
|---|---|
| Café | ~200–230 °C |
| Maní | ~160–180 °C |
| Cacao | ~120–150 °C |

Si comparas la **RH%** entre un tueste de café (escape muy caliente → RH baja) y
uno de cacao (escape más fresco → RH más alta), **los números no son
comparables** aunque esté saliendo la misma cantidad de agua del grano. El calor
del escape distorsiona la RH de forma distinta en cada caso.

La **humedad absoluta** y el **punto de rocío** **normalizan** eso: te dicen
"cuánta agua está saliendo" sin importar a qué temperatura vaya el escape. Así
puedes:

- Comparar el secado **entre granos** (café vs cacao vs maní) con la misma vara.
- Comparar **tueste con tueste** del mismo grano, aunque la temperatura varíe.
- Repetir un perfil de tueste de forma consistente.

## Qué verás durante un tueste

El grano verde trae humedad (café ~10–12 %, cacao ~6–8 %, maní ~5–10 %). Al
tostar, esa agua se evapora y se va por el escape. Si graficas la **humedad
absoluta** (o el **punto de rocío**) contra el tiempo:

1. **Fase de secado**: la humedad absoluta **sube** — el grano está soltando agua.
2. **Pico**: máxima liberación de humedad.
3. **Caída**: el grano ya se secó; empiezan las reacciones de tostado (Maillard).

Ese "mapa" de humedad te ayuda a identificar el fin del secado y a repetir
perfiles. Con **RH% cruda** no lo verías bien, porque sube y baja con la
temperatura del escape, no solo con el agua.

## Qué expone el firmware

Cada evento `sensors` (SSE) y el JSON de sensores incluyen:

| Campo | Qué es | Úsalo para |
|---|---|---|
| `temperature` | °C del **tostado** (termocupla MAX6675) | control del tueste |
| `humidity` | **RH %** en el sensor (SHT31) | referencia rápida (ojo: engaña en caliente) |
| `exhaust_temp` | °C del **aire** en el sensor (SHT31) | vigilar temperatura del escape |
| `dew_point` | **punto de rocío** °C | seguir el secado (temperatura-independiente) |
| `abs_humidity` | **humedad absoluta** g/m³ | seguir/comparar el agua real que sale |

## En resumen

- Para **mostrar un número rápido**, la RH% está bien.
- Para **entender y comparar el tostado** (entre granos, entre tuestes), usa
  **humedad absoluta** o **punto de rocío** — no dependen de la temperatura del
  escape, así que reflejan el agua real que suelta el grano.
- El sensor cobra sentido de tueste cuando está en el **ducto de escape**; en
  ambiente, mide la humedad del cuarto.
