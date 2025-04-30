# itineraries/templatetags/filters.py

import re
from django import template

register = template.Library()

@register.filter
def strip_markdown(value):
    """
    Converte marcações básicas de Markdown em HTML simples
    e mantém emojis, negrito, itálico etc.
    """

    # 1) Converte títulos (# Título) em <h3> (exemplo simples)
    #    Se quiser sempre <h2> ou <h4>, etc., é só trocar.
    value = re.sub(r'^(#{1,6})\s*(.*)', r'<h3>\2</h3>', value, flags=re.MULTILINE)

    # 2) Converte **texto** em <strong>texto</strong>
    value = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', value)

    # 3) Converte *texto* em <em>texto</em> (itálico)
    value = re.sub(r'\*(.*?)\*', r'<em>\1</em>', value)

    # 4) Remove linhas que sejam exatamente "---"
    value = re.sub(r'^---$', '', value, flags=re.MULTILINE)

    # 5) Converte `texto` em <code>texto</code>
    value = re.sub(r'`([^`]+)`', r'<code>\1</code>', value)

    # 6) Importante: NÃO remover emojis nem caracteres especiais
    #    (Remova aquele re.sub(r'[^\w\s,.\-;:()\[\]\/]', '', value))

    return value.strip()
