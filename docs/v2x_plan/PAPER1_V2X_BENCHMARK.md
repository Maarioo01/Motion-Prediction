# Primer paper: un benchmark unificado de predicción de trayectorias V2X

*Mario · noviembre 2026 · resumen para comentar con el tutor y compañeros. El detalle está en el [informe completo](INFORME_PLAN_DE_RUTA_V2X.md).*

## La idea en una frase

Re-entrenar los principales métodos de predicción cooperativa (V2X) con **un mismo protocolo, sobre datos reales**. Después, medir no solo cuánto aciertan, sino también **si su confianza es fiable, cuánto aguantan cuando la comunicación falla y en qué casos ayuda de verdad la infraestructura**.

## El problema: hoy no se puede saber qué método V2X es mejor

Cada paper usa su protocolo y copia cifras de los demás sin re-entrenarlos. En V2X-Seq, el dataset de referencia (vehículo + infraestructura, real):

| Modelo | Cifra (minADE / minFDE / MR) | Quién la da |
| --- | --- | --- |
| V2X-Graph | 1.05 / 1.79 / 0.25 | su propio paper (NeurIPS 2024) |
| V2X-Graph | 1.17 / 2.03 / 0.29 | Co-MTP, CoPAD y V2X-RECT, al citarlo |
| HiVT | entre 1.12 y 1.29 de minADE | según quién lo reporte |
| V2X-RECT | 0.53 / 0.80 / 0.09 | su paper; sin código público |

Además, Co-MTP usa otra ventana de tiempo (3 s → 5 s a 5 Hz) y la trayectoria futura real del coche como "plan", que es información que en la realidad no se tiene.

Tampoco se mide nada más que el error de posición. Ningún paper V2X, salvo V2INet, comprueba si las probabilidades que da el modelo son fiables. Ninguno usa un protocolo común de retrasos y pérdidas de mensajes.

## Qué haríamos

1. **Datos (solo reales):** V2X-Seq-TFD (unos 51k escenarios coche + infraestructura) y V2X-Traj (unos 10k escenarios, con 2 coches + infraestructura). V2V4Real como extra para el caso V2V.
2. **Métodos con código disponible:** HiVT (base sin cooperación y cooperativa), V2X-Graph, V2INet, Co-MTP, la parte de predicción de CMP y un QCNet adaptado a V2X. Los que no tienen código (CoPAD, V2X-RECT, I2XTraj) se citan y se explica por qué no están.
3. **Un único protocolo:**
    - mismo split, horizonte, frecuencia y entradas;
    - nada de información privilegiada;
    - varias semillas por método;
    - configuraciones y Docker publicados.
4. **Cinco ejes de análisis:**
    - **Precisión:** minADE, minFDE y MR.
    - **Calibración:** brier-minFDE y NLL. ¿La probabilidad que da el modelo se corresponde con lo que pasa?
    - **Robustez de la comunicación:** retraso de 0 a 500 ms, pérdidas de mensajes del 10 al 50 % y ruido de posición.
    - **Coste:** milisegundos, parámetros y bytes por mensaje.
    - **Dónde ayuda la cooperación:** resultados separados por dificultad (con un filtro de Kalman como referencia) y por agentes ocluidos o visibles para el coche.

## Qué esperamos encontrar (las preguntas del paper)

- ¿El ranking de minADE se mantiene al medir calibración o robustez, o el "mejor" deja de serlo?
- ¿La infraestructura mejora también la fiabilidad de las probabilidades, o solo el error medio?
- Con retraso y pérdidas, ¿se degrada antes la calibración que el error? Si es así, el modelo se vuelve "seguro de sí mismo y equivocado" justo cuando la comunicación falla.
- ¿La mejora de cooperar se concentra en los casos difíciles u ocluidos? Si es así, la media de minADE la esconde.

Para que el paper funcione basta con que **una** de estas preguntas tenga una respuesta clara. Es la puerta de paso del plan: sin un hallazgo que cambie el ranking, el paper sería solo una tabla.

## Por qué es publicable y por qué ahora

- **No existe** un benchmark unificado de predicción V2X a nivel de trayectorias. UniTraj (ECCV 2024) hizo algo parecido para un solo vehículo, pero no soporta V2X. V2XPnP (ICCV 2025) compara métodos de fusión, pero de extremo a extremo desde LiDAR y en su propio dataset.
- Los papers de "benchmark con preguntas" se publican: UniTraj, "What Truly Matters in Trajectory Prediction" (NeurIPS 2023).
- Es de **riesgo bajo**: los modelos son pequeños (1 a 5 M de parámetros) y caben en una RTX 3090. Además, deja montada la base de todo lo que viene después.
- El campo se mueve rápido, así que conviene sacar una versión en arXiv pronto.

## Calendario y destino

- **Nov 2026 – ene 2027:** conseguir los datos, montar los métodos y reproducir dos cifras publicadas (HiVT y V2X-Graph, dentro de ±5 %).
- **Feb – jun 2027:** protocolo, entrenamientos (unos 30–40 en total) y escritura.
- **Destino:** arXiv en verano de 2027. Después, IEEE T-ITS o RA-L (sin fecha límite), o IV 2028 como conferencia.

## Riesgos principales

- **Acceso a V2X-Seq desde España:** la descarga libre es solo desde China continental. Es lo primero que hay que resolver.
- **Cómputo:** del orden de 1 a 2 meses de una sola GPU. Es viable si se empieza pronto.
- **Que un revisor lo vea como "solo reproducir":** se mitiga con las cuatro preguntas de arriba.

## Qué viene después (paper 2)

Un predictor propio que use lo que el benchmark revele:

- el **retraso de cada mensaje** como parte del tiempo relativo;
- un **indicador de fiabilidad por fuente**;
- las **trayectorias que emite la infraestructura** como punto de partida (anchors) del coche;
- **probabilidades calibradas**.

El benchmark será también donde se evalúe.
