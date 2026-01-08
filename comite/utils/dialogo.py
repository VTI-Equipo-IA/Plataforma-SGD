# utils/dialogo.py
# -*- coding: utf-8 -*-
from typing import Dict, Any, List
import re
import unicodedata

def _norm_line(s: str) -> str:
    if not s: return ""
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = re.sub(r"^\s*\d+\s*[\.\)\-]\s*", "", s.strip())
    s = re.sub(r"\s+", " ", s)
    return s.strip().lower()

def _normalize_listado(text: str) -> List[str]:
    if not text: return []
    return [_norm_line(ln) for ln in text.splitlines() if ln.strip()]

def _equal_plans(a: str, b: str) -> bool:
    la = [x for x in _normalize_listado(a) if x]
    lb = [x for x in _normalize_listado(b) if x]
    return la == lb

def run_dialogue(
    *,
    pregunta: str,
    respuesta: str,
    retrievers: Dict[str, Any],
    agentes: Dict[str, Any],
    secretario: Any,
    max_rounds: int = 3,
    question_id: str = "",
    dimension: str = "",
    subdimension: str = "",
    instrumento_indicador: str = "",
    brecha_input: str = "",
    iniciativa: str = "",
) -> Dict[str, Any]:
    """
    Flujo:
      1) PMG abre plan inicial (topes por dimensión).
      2) Rondas: intervienen Abogado/Implementador/Desarrollador (agregar/eliminar),
         Secretario consolida y arma brief, PMG revisa + sintetiza (sin brecha).
      3) Consenso si el plan no cambia respecto a la ronda anterior.
    """
    resultado: Dict[str, Any] = {
        "apertura_pmg": "",
        "rondas": [],
        "final": "",
        "pmg_final": {},
        "secretario_ultima": {}
    }

    # 1) Apertura PMG
    try:
        apertura = agentes["pmg"].initial(
            pregunta=pregunta,
            respuesta=respuesta,
            dimension=dimension,
            instrumento_indicador=instrumento_indicador,
            brecha_input=brecha_input,
            iniciativa=iniciativa
        )
    except Exception as e:
        apertura = ""
        print(f"[ERR] PMG.initial: {e}", flush=True)

    resultado["apertura_pmg"] = apertura
    plan_actual = apertura

    # 2) Rondas
    historial = []
    for ronda in range(1, max_rounds + 1):
        intervenciones: Dict[str, str] = {}

        for rol in ("abogado", "implementador", "desarrollador"):
            agente = agentes.get(rol)
            if not agente:
                intervenciones[rol] = ""
                continue
            try:
                interv = agente.post(
                    pregunta=pregunta,
                    respuesta=respuesta,
                    dimension=dimension,
                    subdimension=subdimension,
                    instrumento_indicador=instrumento_indicador,
                    brecha_input=brecha_input,
                    listado_vigente=plan_actual
                )
            except Exception as e:
                interv = f"Sin observaciones relevantes (error: {e})"
            intervenciones[rol] = (interv or "").strip()

        # Secretario
        try:
            sec_out = secretario.consolidate_and_brief(
                pregunta=pregunta,
                respuesta=respuesta,
                plan_pmg=plan_actual,
                interv_abogado=intervenciones.get("abogado",""),
                interv_implementador=intervenciones.get("implementador",""),
                interv_desarrollador=intervenciones.get("desarrollador",""),
                historial="\n".join(historial) if historial else "",
                dimension=dimension
            )
        except Exception as e:
            sec_out = {"listado": plan_actual, "brief_pmg": f"(error en secretario: {e})"}

        listado_consolidado = (sec_out.get("listado") or "").strip()
        brief_pmg = (sec_out.get("brief_pmg") or "").strip()

        # PMG post-brief (sintetiza campos finales)
        try:
            pmg_out = agentes["pmg"].post(
                dimension=dimension,
                subdimension=subdimension,
                instrumento_indicador=instrumento_indicador,
                brecha_input=brecha_input,
                iniciativa=iniciativa,
                pregunta=pregunta,
                respuesta=respuesta,
                propuesta_previa=plan_actual,
                listado_consolidado=listado_consolidado,
                brief=brief_pmg
            )
        except Exception as e:
            pmg_out = {"listado": plan_actual}
            print(f"[ERR] PMG.post: {e}", flush=True)

        plan_revisado = (pmg_out.get("listado") or "").strip()
        consenso = _equal_plans(plan_revisado, plan_actual)

        resultado["rondas"].append({
            "n": ronda,
            "intervenciones": intervenciones,
            "secretario": {"listado": listado_consolidado, "brief_pmg": brief_pmg},
            "pmg_revision": pmg_out,
            "consenso": consenso
        })

        plan_actual = plan_revisado or plan_actual
        historial.append(f"[RONDA {ronda}] PMG ->\n{plan_actual}")

        if consenso:
            resultado["pmg_final"] = pmg_out
            resultado["secretario_ultima"] = sec_out
            break

        if ronda == max_rounds:
            resultado["pmg_final"] = pmg_out
            resultado["secretario_ultima"] = sec_out

    resultado["final"] = plan_actual
    return resultado



