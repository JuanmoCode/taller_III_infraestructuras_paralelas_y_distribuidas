"""Análisis de ventas por producto y categoría - VERSIÓN SECUENCIAL."""
import sys
import time

from generador_ventas import generar_ventas

IVA = 0.19              # impuesto
COMISION = 0.03         # comisión de la pasarela de pago
MARGEN_COSTO = 0.55     # el costo de producción es el 55 % del precio
TAMANO_LOTE = 500       # cada cuántos registros se consulta el servicio de promociones/impuestos
LATENCIA_MS = 0      # espera simulada (E/S) de esa consulta, en milisegundos


def calcular_venta(cantidad, precio):
    """Procesamiento de UN registro, devolviendo el neto y la utilidad de la venta."""
    valor_bruto = cantidad * precio                     # valor_venta = cantidad x precio
    if cantidad >= 10:                                  # descuento por volumen
        descuento = valor_bruto * 0.10
    elif cantidad >= 5:
        descuento = valor_bruto * 0.05
    else:
        descuento = 0.0
    base = valor_bruto - descuento
    iva = base * IVA
    comision = base * COMISION
    neto = base + iva - comision                        # lo que realmente queda por la venta
    costo = cantidad * precio * MARGEN_COSTO
    utilidad = base - costo - comision
    return neto, utilidad


def acumular(diccionario, clave, neto, utilidad, cantidad):
    """clave -> [total_neto, total_utilidad, unidades]"""
    if clave not in diccionario:
        diccionario[clave] = [0.0, 0.0, 0]
    acum = diccionario[clave]
    acum[0] += neto
    acum[1] += utilidad
    acum[2] += cantidad


def consultar_servicio(latencia_ms):
    """Simula consultar un servicio externo (promociones, impuestos, base de datos).
    time.sleep representa una espera de E/S: mientras espera, el hilo libera el GIL."""
    if latencia_ms > 0:
        time.sleep(latencia_ms / 1000)


def procesar_registros(lineas, por_producto, por_categoria, latencia_ms):
    """Recorre un iterable de líneas CSV y acumula totales por producto y por categoría.
    La usan las dos versiones, así hacen exactamente el mismo trabajo."""
    n = 0
    for linea in lineas:
        _, producto, categoria, cantidad, precio = linea.strip().split(",")
        cantidad = int(cantidad)
        precio = float(precio)
        if cantidad <= 0 or precio <= 0:                # validación básica
            continue
        neto, utilidad = calcular_venta(cantidad, precio)
        acumular(por_producto, producto, neto, utilidad, cantidad)
        acumular(por_categoria, categoria, neto, utilidad, cantidad)
        n += 1
        if n % TAMANO_LOTE == 0:
            consultar_servicio(latencia_ms)


def analizar_secuencial(ruta, latencia_ms=LATENCIA_MS):
    """Un solo flujo recorre TODOS los registros."""
    por_producto, por_categoria = {}, {}
    with open(ruta, "r", encoding="utf-8") as f:
        next(f)                                         # saltar el encabezado
        procesar_registros(f, por_producto, por_categoria, latencia_ms)
    return por_producto, por_categoria


def mostrar_resultados(por_producto, por_categoria, top=10):
    print(f"Top {top} productos por ventas netas:")
    ranking = sorted(por_producto.items(), key=lambda kv: kv[1][0], reverse=True)[:top]
    for i, (producto, (neto, utilidad, unidades)) in enumerate(ranking, 1):
        print(f"  {i:>2}. {producto:<16} ${neto:>14,.0f}   {unidades:>7} unid.")
    print("Ventas netas por categoría:")
    for categoria, (neto, utilidad, unidades) in sorted(por_categoria.items(), key=lambda kv: -kv[1][0]):
        print(f"  {categoria:<16} ${neto:>14,.0f}   utilidad ${utilidad:>13,.0f}")


if __name__ == "__main__":
    # Uso: python ventas_secuencial.py [latencia_ms]   (0 = sin espera de E/S)
    latencia = float(sys.argv[1]) if len(sys.argv) > 1 else LATENCIA_MS
    archivo = "ventas.csv"
    generar_ventas(archivo)

    inicio = time.perf_counter()
    por_producto, por_categoria = analizar_secuencial(archivo, latencia)
    duracion = time.perf_counter() - inicio

    mostrar_resultados(por_producto, por_categoria)
    print(f"\nLatencia simulada por lote: {latencia} ms")
    print(f"Tiempo SECUENCIAL: {duracion:.4f} s")
