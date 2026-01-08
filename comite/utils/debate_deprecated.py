# utils/debate.py
# -*- coding: utf-8 -*-
from typing import Callable, Dict, Any

# Sanitizador opcional
try:
    from utils.text_guard import sanitize_line, sanitize_block
except Exception:
    def sanitize_line(s: str) -> str: return (s or "").strip()
    def sanitize_block(s: str) -> str: return (s or "").strip()

# Tipo del agente: fn(retriever, pregunta, texto, *, mode="initial", propuesta_previa="", criticas_recibidas="")
AgentFn = Callable[..., str]

def _criticar_todos(agentes: Dict[str, AgentFn], retrievers: Dict[str, Callable], pregunta: str, propuestas: Dict[str, str]) -> Dict[str, Dict[str, str]]:
    """
    Retorna dict: {criticador: {criticado: "texto crítica"}}
    """
    roles = list(agentes.keys())
    criticas: Dict[str, Dict[str, str]] = {r: {} for r in roles}
    for criticador in roles:
        for criticado in roles:
            if criticador == criticado:
                continue
            objetivo = propuestas.get(criticado, "")
            out = agentes[criticador](retrievers.get(criticador), pregunta, objetivo, mode="critique")
            criticas[criticador][criticado] = sanitize_line(out or "")
    return criticas

def _criticas_recibidas_por_rol(criticas_cruzadas: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    """
    Convierte {A:{B:txt,..}, ...} en {rol: "X→rol:..., Y→rol:..."} para alimentar 'criticas_recibidas' en cada agente.
    """
    acumuladas: Dict[str, list] = {}
    for criticador, destinos in criticas_cruzadas.items():
        for criticado, texto in destinos.items():
            if not texto: 
                continue
            acumuladas.setdefault(criticado, []).append(f"{criticador}→{criticado}: {texto}")
    return {rol: " ".join(lst) for rol, lst in acumuladas.items()}

def run_debate(
    pregunta: str,
    respuesta: str,
    proponer_fn: Callable[[], Dict[str, str]],
    rondas: int,
    model: str,
    *,
    retrievers: Dict[str, Callable] = None,
    agentes: Dict[str, AgentFn] = None
) -> Dict[str, Any]:
    """
    Estructura:
      ronda_0:
        acciones: {rol: propuesta_inicial (texto breve)}
      ronda_1:
        criticas: {criticador: {criticado: critica}}
        acciones: {rol: propuesta_post (LISTADO numerado, máx. 10)}
    """
    if retrievers is None:
        retrievers = {}
    if agentes is None:
        raise ValueError("Debes pasar 'agentes' con funciones de cada rol.")

    historial: Dict[str, Any] = {}

    # --- RONDA 0: propuestas iniciales ---
    propuestas = proponer_fn()  # {rol: texto breve}
    propuestas = {k: sanitize_line(v) for k, v in propuestas.items()}
    historial["ronda_0"] = {"acciones": propuestas}

    # --- RONDA 1: críticas cruzadas ---
    criticas = _criticar_todos(agentes, retrievers, pregunta, propuestas)
    historial["ronda_1"] = {"criticas": criticas}

    # Armar críticas recibidas por cada rol
    crit_recibidas = _criticas_recibidas_por_rol(criticas)

    # --- Revisión post-críticas: listado numerado (máx. 10) por cada rol ---
    propuestas_post = {}
    for rol, agente_fn in agentes.items():
        propuesta_previa = propuestas.get(rol, "")
        críticas_de_otros = crit_recibidas.get(rol, "")
        out = agente_fn(
            retrievers.get(rol),
            pregunta,
            respuesta,  # seguimos partiendo de la respuesta original del formulario
            mode="post",
            propuesta_previa=propuesta_previa,
            criticas_recibidas=críticas_de_otros
        )
        propuestas_post[rol] = sanitize_block(out or "")

    historial["ronda_1"]["acciones"] = propuestas_post

    # Soporta 'rondas' > 1 (iteraciones extra) si quieres extender más tarde
    return historial
