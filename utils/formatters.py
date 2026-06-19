def brl(value: float) -> str:
    """Formata valor como moeda brasileira."""
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def mes_label(mes_ref: str) -> str:
    """Converte '2025-03' em 'Mar/2025'."""
    meses = {
        "01": "Jan", "02": "Fev", "03": "Mar", "04": "Abr",
        "05": "Mai", "06": "Jun", "07": "Jul", "08": "Ago",
        "09": "Set", "10": "Out", "11": "Nov", "12": "Dez"
    }
    try:
        partes = mes_ref.split("-")
        return f"{meses[partes[1]]}/{partes[0]}"
    except Exception:
        return mes_ref


def cor_saldo(valor: float) -> str:
    return "green" if valor >= 0 else "red"
