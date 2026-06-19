import os
import re

# Reduce logs informativos de TensorFlow al cargar transformers pipeline.
os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

ENABLE_HF_MODERATOR = os.getenv("ENABLE_HF_MODERATOR", "0") == "1"
_moderador_hf = None
_moderador_hf_attempted = False

PATRONES_PROHIBIDOS = [
    # Sexual
    r"\b(sexo|sexual|pornografía|porno|desnudo|masturba[rc]|violación|violador|orgasmo|erección|eyaculación)\b",
    # Violencia
    r"\b(matar|asesinar|apuñalar|violento|sangre|sádico|violar|golpear|estrangular|arma|navaja|tiroteo)\b",
    # Lenguaje obsceno
    r"\b(estúpido|idiota|imbécil|mierda|maldito|puta|pendejo|jódete|cabr[oó]n|zorra|cul[oó]|verga|chingar)\b",
    # Discriminación racial
    r"\b(negro de mierda|maldito negro|judío maldito|indio bruto|chino de mierda|sudaca|nazi)\b",
    # Discriminación de género e identidad
    r"\b(maric[oó]n|puto|lesbiana de mierda|transexual deforme|machorra|hembra estúpida|feminazi|gay asqueroso)\b"
]

def contiene_lenguaje_ofensivo_regex(texto: str) -> bool:
    texto = texto.lower()
    for patron in PATRONES_PROHIBIDOS:
        if re.search(patron, texto):
            return True
    return False


def _get_moderador_hf():
    """Carga perezosa del modelo HF (opcional por entorno)."""
    global _moderador_hf_attempted, _moderador_hf
    if _moderador_hf_attempted:
        return _moderador_hf

    _moderador_hf_attempted = True
    if not ENABLE_HF_MODERATOR:
        return None

    try:
        from transformers import pipeline

        _moderador_hf = pipeline(
            "text-classification",
            model="unitary/toxic-bert",
            top_k=None,
        )
    except Exception as e:
        print("❌ Error al cargar modelo moderador HF:", e)
        _moderador_hf = None
    return _moderador_hf

def contiene_lenguaje_ofensivo_modelo(texto: str, umbral=0.6) -> bool:
    moderador_hf = _get_moderador_hf()
    if not moderador_hf:
        return False  # fallback si el modelo no cargó
    resultado = moderador_hf(texto)
    for pred in resultado[0]:
        if pred["label"] != "non-toxic" and pred["score"] > umbral:
            return True
    return False

def is_inappropriate_input(texto: str) -> bool:
    return (
        contiene_lenguaje_ofensivo_regex(texto)
        or contiene_lenguaje_ofensivo_modelo(texto)
    )
