"""Genera un CSV simulado con las ventas de un restaurante / tienda."""
import os
import random

# producto -> (categoría, precio unitario en COP)
CATALOGO = {
    "Hamburguesa": ("Comidas", 18000), "Pizza personal": ("Comidas", 22000),
    "Sandwich": ("Comidas", 12000), "Ensalada": ("Comidas", 14000),
    "Pasta": ("Comidas", 20000), "Bandeja paisa": ("Comidas", 28000),
    "Empanada": ("Comidas", 3500), "Perro caliente": ("Comidas", 9000),
    "Gaseosa": ("Bebidas", 4500), "Jugo natural": ("Bebidas", 6500),
    "Cerveza": ("Bebidas", 7000), "Agua": ("Bebidas", 3000),
    "Limonada": ("Bebidas", 5500), "Cafe": ("Bebidas", 3500),
    "Te frio": ("Bebidas", 5000), "Malteada": ("Bebidas", 11000),
    "Helado": ("Postres", 7500), "Brownie": ("Postres", 8000),
    "Cheesecake": ("Postres", 11000), "Tres leches": ("Postres", 9500),
    "Flan": ("Postres", 6500), "Torta": ("Postres", 10000),
    "Papas fritas": ("Acompañamientos", 6000), "Arepa": ("Acompañamientos", 3000),
    "Aros de cebolla": ("Acompañamientos", 7000), "Yuca frita": ("Acompañamientos", 5500),
    "Nuggets": ("Acompañamientos", 9000), "Patacones": ("Acompañamientos", 6500),
    "Combo familiar": ("Combos", 65000), "Combo personal": ("Combos", 28000),
    "Combo infantil": ("Combos", 20000), "Combo pareja": ("Combos", 48000),
}


def generar_ventas(ruta, num_registros=200_000, semilla=42):
    """Crea el CSV si no existe. Formato: id_venta,producto,categoria,cantidad,precio_unitario
    La semilla fija hace que ambas versiones lean exactamente los mismos datos."""
    if os.path.exists(ruta):
        return
    rnd = random.Random(semilla)
    productos = list(CATALOGO)
    pesos = [1 / (i + 1) ** 0.7 for i in range(len(productos))]   # unos productos se venden mucho más
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("id_venta,producto,categoria,cantidad,precio_unitario\n")
        for i in range(1, num_registros + 1):
            producto = rnd.choices(productos, pesos)[0]
            categoria, precio = CATALOGO[producto]
            cantidad = rnd.choices([1, 2, 3, 4, 5, 8, 10, 12, 20], [30, 25, 15, 10, 8, 5, 4, 2, 1])[0]
            f.write(f"{i},{producto},{categoria},{cantidad},{precio}\n")


if __name__ == "__main__":
    generar_ventas("ventas.csv")
    print("Archivo generado: ventas.csv")
