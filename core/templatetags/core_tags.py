from django import template

register = template.Library()


@register.filter(name="clp")
def clp_format(value):
    """
    Formatea un número con puntos de miles para peso chileno / enteros.
    Ej: 5000 -> "5.000", 9990 -> "9.990", 120000 -> "120.000", 1500000 -> "1.500.000"
    """
    if value is None or value == "":
        return "0"
    try:
        val = int(round(float(value)))
        return f"{val:,}".replace(",", ".")
    except (ValueError, TypeError):
        return str(value)


@register.filter(name="dot_number")
def dot_number_format(value):
    """
    Formatea un entero con separador de miles en puntos.
    Ej: 1000 -> "1.000"
    """
    return clp_format(value)
