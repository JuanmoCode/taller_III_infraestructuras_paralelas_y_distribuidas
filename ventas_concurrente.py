"""Análisis de ventas por producto y categoría - VERSIÓN CONCURRENTE (MapReduce + hilos)."""
import math
import os
import sys
import threading
import time

from generador_ventas import generar_ventas
from ventas_secuencial import (LATENCIA_MS, analizar_secuencial, mostrar_resultados,
                               procesar_registros)


def calcular_rangos(ruta, num_hilos):
    """Divide el archivo en num_hilos bloques de bytes [inicio, fin)."""
    tamano = os.path.getsize(ruta)
    paso = tamano // num_hilos
    rangos = []
    for i in range(num_hilos):
        inicio = i * paso
        fin = tamano if i == num_hilos - 1 else inicio + paso
        rangos.append((inicio, fin))
    return rangos


def leer_rango(ruta, inicio, fin):
    """Generador: entrega las líneas de ventas que EMPIEZAN dentro de [inicio, fin).
    Cada hilo abre su propio manejador del archivo (no se comparte la posición de lectura)."""
    with open(ruta, "rb") as f:
        if inicio == 0:
            f.readline()                     # el hilo 0 salta el encabezado
        else:
            f.seek(inicio - 1)
            f.readline()                     # descarta la línea que empezó en el bloque anterior
        while f.tell() < fin:
            linea = f.readline()
            if not linea:
                break
            yield linea.decode("utf-8")


def map_function(ruta, inicio, fin, latencia_ms, resultados, indice):
    """FASE MAP: cada hilo procesa SU bloque de ventas y calcula los totales por producto
    y por categoría (valor, descuento, IVA, comisión, utilidad y unidades)."""
    por_producto, por_categoria = {}, {}
    procesar_registros(leer_rango(ruta, inicio, fin), por_producto, por_categoria, latencia_ms)
    resultados[indice] = (por_producto, por_categoria)   # cada hilo escribe en su propia posición


def combinar(destino, parcial):
    """Suma los totales parciales de cada clave dentro del diccionario destino."""
    for clave, (neto, utilidad, unidades) in parcial.items():
        if clave not in destino:
            destino[clave] = [0.0, 0.0, 0]
        destino[clave][0] += neto
        destino[clave][1] += utilidad
        destino[clave][2] += unidades


def reduce_function(resultados):
    """FASE REDUCE: suma los totales parciales de cada producto y categoría."""
    total_producto, total_categoria = {}, {}
    for por_producto, por_categoria in resultados:
        combinar(total_producto, por_producto)
        combinar(total_categoria, por_categoria)
    return total_producto, total_categoria


def analizar_concurrente(ruta, num_hilos, latencia_ms=LATENCIA_MS):
    rangos = calcular_rangos(ruta, num_hilos)
    resultados = [None] * num_hilos
    hilos = []
    for i, (ini, fin) in enumerate(rangos):                     # lanzar hilos (Map)
        h = threading.Thread(target=map_function, args=(ruta, ini, fin, latencia_ms, resultados, i))
        hilos.append(h)
        h.start()
    for h in hilos:                                             # esperar a todos
        h.join()
    return reduce_function(resultados)                          # Reduce


def son_iguales(a, b):
    """Las unidades deben ser idénticas; los valores monetarios, iguales con tolerancia
    (la suma de flotantes puede variar en el último dígito según el orden)."""
    if a.keys() != b.keys():
        return False
    return all(a[k][2] == b[k][2]
               and math.isclose(a[k][0], b[k][0], rel_tol=1e-9)
               and math.isclose(a[k][1], b[k][1], rel_tol=1e-9) for k in a)


if __name__ == "__main__":
    # Uso: python ventas_concurrente.py [latencia_ms]   (0 = sin espera de E/S)
    latencia = float(sys.argv[1]) if len(sys.argv) > 1 else LATENCIA_MS
    archivo = "ventas.csv"
    generar_ventas(archivo)
    print(f"Latencia simulada por lote de consulta: {latencia} ms\n")

    # Línea base secuencial (para calcular speedup y verificar resultados)
    t0 = time.perf_counter()
    prod_seq, cat_seq = analizar_secuencial(archivo, latencia)
    t_seq = time.perf_counter() - t0
    print(f"Tiempo SECUENCIAL: {t_seq:.4f} s\n")

    print(f"{'Hilos':<7}{'Tiempo (s)':<13}{'Speedup':<10}{'¿Correcto?'}")
    for n in (1, 2, 4, 8):
        t0 = time.perf_counter()
        prod, cat = analizar_concurrente(archivo, n, latencia)
        t = time.perf_counter() - t0
        ok = son_iguales(prod, prod_seq) and son_iguales(cat, cat_seq)
        print(f"{n:<7}{t:<13.4f}{t_seq / t:<10.2f}{ok}")

    print("\nResultados (versión concurrente con 4 hilos):")
    prod, cat = analizar_concurrente(archivo, 4, latencia)
    mostrar_resultados(prod, cat)
