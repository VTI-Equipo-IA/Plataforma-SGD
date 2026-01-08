# Desarrollo del SuperPrompt - Agente Maestro PTD

## 📖 Resumen Ejecutivo

Este documento explica el **proceso iterativo de desarrollo** del SuperPrompt utilizado por el Agente Maestro PTD. El SuperPrompt evolucionó a través de múltiples iteraciones basadas en feedback de usuarios y resultados de pruebas, transformándose de un prompt genérico a un sistema de instrucciones de 1,500+ líneas altamente especializado.

**Archivo final:** `Prompts/SuperPrompt_AgenteMaestro_PTD.md`

---

## 🎯 Objetivos del SuperPrompt

### Objetivo Principal
Crear un prompt que permita a un LLM (GPT-4o) generar automáticamente Planes de Transformación Digital (PTD) que:
1. Sean **100% técnicos** (solo implementación, sin gestión organizacional)
2. Cierren **brechas específicas** identificadas en diagnósticos
3. Sigan **metodología HITOS-FIRST** (hitos primero, actividades después)
4. Respeten **cantidades mínimas** (3-4 hitos, 9-12 actividades)
5. Tengan **especificidad alta** (12-25 palabras por actividad)
6. Generen **indicadores cualitativos** (no cuantitativos)

### Desafíos Iniciales
- LLM generaba planes genéricos sin contexto técnico
- Actividades demasiado breves (5-8 palabras)
- Mezclaba implementación con capacitaciones/evaluaciones
- Incluía trabajo post-implementación innecesario
- Indicadores confundían "proceso" con "resultado"
- Repetía actividades entre niveles de madurez (Gobernanza)

---

## 🏗️ Arquitectura del SuperPrompt

El SuperPrompt final tiene una estructura de **9 secciones principales**:

```
┌─────────────────────────────────────────────────────────────┐
│              SUPERPROMPT AGENTE MAESTRO PTD                 │
│                     (~1,500 líneas)                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  1. IDENTIDAD DEL AGENTE                                    │
│     ├─ Rol y propósito                                      │
│     ├─ Integración de 3 agentes especializados             │
│     └─ Objetivo de automatización                           │
│                                                              │
│  2. MISIÓN Y ALCANCE                                        │
│     ├─ Objetivo principal                                   │
│     ├─ Documento base (Planes_nuevo.xlsx)                   │
│     ├─ Formato de salida (celda única)                      │
│     ├─ Metodología HITOS-FIRST                              │
│     └─ Flujo de trabajo PTD                                 │
│                                                              │
│  3. INDICADORES DE RESULTADO CUALITATIVOS                   │
│     ├─ Diferencia Proceso vs Resultado                      │
│     ├─ Estructura obligatoria                               │
│     ├─ Verbos/estados permitidos                            │
│     ├─ Ejemplos por dimensión                               │
│     └─ Validación del indicador                             │
│                                                              │
│  4. METODOLOGÍA INTEGRADA (3 FASES)                         │
│     ├─ Fase 1: Clasificación (ClasificadorPMG)             │
│     ├─ Fase 2: Validación (TRIA 2.0)                       │
│     └─ Fase 3: Generación de Plan Completo                 │
│                                                              │
│  5. LECTURA DE PLANES_NUEVO.XLSX (Reglas por dimensión)    │
│     ├─ Procedimiento Administrativo (1 fila = 1 plan)      │
│     ├─ Gobernanza de Datos (1 fila = 1 nivel)              │
│     └─ Calidad Web (1 fila = 1 pregunta)                   │
│                                                              │
│  6. REPORTEO EN TERMINAL                                    │
│     ├─ Secuencia obligatoria de logging                     │
│     └─ Formato estructurado                                 │
│                                                              │
│  7. INSTRUCCIONES CRÍTICAS PROCEDIMIENTO ADMINISTRATIVO     │
│     ├─ ENFOQUE 100% TÉCNICO                                 │
│     ├─ Actividades prohibidas                               │
│     ├─ Actividades permitidas                               │
│     ├─ Cantidades por complejidad                           │
│     ├─ Ejemplos técnicos (60 ejemplos)                      │
│     ├─ Regla de Oro: Plan termina al cerrar brecha         │
│     └─ Progresión de actividades                            │
│                                                              │
│  8. INSTRUCCIONES CRÍTICAS GOBERNANZA DE DATOS              │
│     ├─ PROGRESIÓN INCREMENTAL OBLIGATORIA                   │
│     ├─ Verbos por nivel de madurez                          │
│     ├─ Cantidades por complejidad                           │
│     ├─ Ejemplos por subdimensión                            │
│     └─ Validación: ¿Ya se hizo en nivel anterior?          │
│                                                              │
│  9. INSTRUCCIONES CRÍTICAS CALIDAD WEB                      │
│     ├─ Metodología especial (actividad/pregunta)            │
│     ├─ Hitos como entregables (no métricas)                 │
│     ├─ Integración de descripción de indicador              │
│     └─ Especificidad única por indicador                    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 📅 Cronología de Desarrollo

### Versión 1.0 - Prompt Genérico (Septiembre 2025)

**Estado inicial:**
```markdown
# Super Prompt - Agente Maestro PTD

Eres un agente especializado en generar planes PTD.

## Instrucciones:
1. Lee el indicador
2. Identifica la brecha
3. Genera actividades y hitos
4. Formato: JSON

## Estructura:
- 2-4 hitos
- 3-5 actividades por hito
```

**Problemas detectados:**
- ❌ Planes muy cortos (10-15 actividades totales)
- ❌ Actividades genéricas ("Implementar sistema", "Capacitar personal")
- ❌ Sin contexto técnico específico
- ❌ Formato inconsistente

**Resultado:** Planes inutilizables para desarrolladores

---

### Versión 2.0 - Aumento de Cantidades (Octubre 8)

**Cambios aplicados:**
```markdown
## Estructura por Plan:
- **Mínimo 3-5 HITOS** por plan
- **Mínimo 4-6 ACTIVIDADES por cada hito**
- **PROHIBIDO**: Planes con menos de 3 hitos
- **Total mínimo**: 12-30 actividades totales
```

**Mejoras:**
- ✅ Planes más robustos
- ✅ Mayor profundidad de detalle

**Problemas persistentes:**
- ❌ Seguían siendo genéricos
- ❌ Actividades breves (5-8 palabras)

---

### Versión 3.0 - Formato de Salida Corregido (Octubre 8)

**Problema identificado:**
- Orden incorrecto: Hito → Actividades
- LLM generaba backticks (```)

**Solución implementada:**
```markdown
**ORDEN OBLIGATORIO**: Primero todas las actividades de un hito, luego el hito correspondiente

**Formato correcto:**
```
Actividad: Configurar plataforma
Actividad: Capacitar personal
Hito: Implementación de sistema
```

**Resultado:**
- ✅ Orden correcto
- ✅ Formato consistente

---

### Versión 4.0 - Revolución: Enfoque 100% Técnico (Octubre 10)

**Feedback crítico del usuario:**
> "Estos planes los van a leer personas que son desarrolladores, por lo que solo necesitan que le digan la parte técnica que deben hacer para cerrar la brecha"

**Cambio fundamental:**

#### ANTES (Planes con gestión):
```
Actividad: Participar en capacitación ClaveÚnica
Actividad: Capacitar al personal en uso de ClaveÚnica
Actividad: Establecer protocolos internos de uso
Actividad: Monitorear el uso de ClaveÚnica
Actividad: Recopilar feedback de usuarios
Actividad: Evaluar el impacto de la implementación
Actividad: Ajustar procedimientos basados en feedback
Actividad: Formalizar política institucional de autenticación
```

#### AHORA (Solo implementación técnica):
```
Actividad: Completar Solicitud de Credenciales de Integración a ClaveÚnica en gobdigital.cerofilas.gob.cl
Actividad: Configurar endpoints de autenticación en el backend del sistema
Actividad: Implementar flujo de redirección OAuth con ClaveÚnica
Actividad: Integrar ClaveÚnica en los sistemas de autenticación institucionales
Actividad: Configurar manejo de tokens JWT para sesiones de usuario
Actividad: Realizar pruebas de integración en ambiente de desarrollo
Actividad: Implementar validación de certificados digitales
Actividad: Certificar la operatividad de ClaveÚnica en los procedimientos
```

**Nueva sección agregada:**
```markdown
## 🔧 ENFOQUE 100% TÉCNICO - SOLO IMPLEMENTACIÓN PARA ALCANZAR NIVEL SIGUIENTE

**ACTIVIDADES PROHIBIDAS** (NUNCA incluir):
- ❌ "Capacitar al personal en..."
- ❌ "Evaluar el impacto de..."
- ❌ "Monitorear el uso de..."
- ❌ "Recopilar feedback de usuarios..."
- ❌ "Formalizar la política institucional..."

**ACTIVIDADES PERMITIDAS** (SOLO técnicas):
- ✅ "Completar Solicitud de Credenciales..."
- ✅ "Configurar endpoints de autenticación..."
- ✅ "Implementar flujo de redirección OAuth..."
- ✅ "Integrar ClaveÚnica en los sistemas..."

**VERBOS TÉCNICOS PERMITIDOS**:
Configurar, Desarrollar, Implementar, Integrar, Solicitar, Realizar pruebas, Certificar

**VERBOS PROHIBIDOS**:
Capacitar, Evaluar, Monitorear, Recopilar feedback, Formalizar, Establecer protocolos
```

**Impacto:**
- ✅ Planes 100% accionables para desarrolladores
- ✅ Cero actividades de gestión organizacional

---

### Versión 5.0 - Plan Termina al Cerrar Brecha (Octubre 10)

**Problema identificado:**
- Planes con 7 hitos cuando solo se necesitaban 3-4
- Últimos hitos eran post-implementación: "Optimización...", "Evaluación continua..."

**Feedback del usuario:**
> "El plan debe ser una serie de pasos a seguir para cerrar la brecha, es decir, la ultima actividad e hito deberia ser la que cierre la brecha, sin agregar trabajo adicional posterior."

**Cambios críticos:**

1. **Cantidades reducidas:**
```markdown
## CANTIDADES ESPERADAS:
- **3-4 hitos MÁXIMO** (NO 7 hitos)
- **3-4 actividades por hito**
- **Total: 10-16 actividades MÁXIMO**
```

2. **Regla de Oro:**
```markdown
**REGLA DE ORO**: Si la actividad se hace DESPUÉS de que el sistema está operativo en producción, NO incluirla.

**EL PLAN TERMINA cuando**:
- El sistema está operativo en producción certificado
- La brecha identificada está cerrada
- Los usuarios pueden usar el sistema

**NO AGREGAR**:
- ❌ Optimizaciones posteriores
- ❌ Evaluaciones continuas
- ❌ Monitoreo post-despliegue
- ❌ Mejoras futuras
```

3. **Lista expandida de prohibiciones:**
```markdown
**ACTIVIDADES ABSOLUTAMENTE PROHIBIDAS**:
- ❌ "Implementar sistema de monitoreo..."
- ❌ "Optimizar el flujo..."
- ❌ "Formalizar el cierre..."
- ❌ "Documentar lecciones aprendidas..."
- ❌ "Realizar revisión final..."
- ❌ "Confirmar la operatividad con usuarios finales..."

**HITOS PROHIBIDOS**:
- ❌ "Cierre del proyecto..."
- ❌ "Optimización..."
- ❌ "Robustez del sistema..."
- ❌ "Mejora continua..."
```

**Resultado:**
- ✅ Planes 70% más cortos
- ✅ Enfocados exclusivamente en cerrar la brecha
- ✅ Sin trabajo post-cierre

**Ejemplo de plan correcto:**
```
Actividad: Completar Solicitud de Credenciales
Actividad: Configurar endpoints de autenticación
Actividad: Implementar flujo OAuth
Hito: Configuración inicial de ClaveÚnica

Actividad: Integrar ClaveÚnica en sistemas
Actividad: Configurar manejo de tokens JWT
Actividad: Implementar validación de certificados
Hito: Integración técnica de autenticación

Actividad: Realizar pruebas de integración
Actividad: Desplegar en producción
Actividad: Certificar operatividad de ClaveÚnica ← ÚLTIMA (cierra brecha)
Hito: Pruebas y despliegue en producción

FIN - Brecha cerrada, sistema operativo
```

---

### Versión 6.0 - Eliminación de Hipersíntesis (Octubre 17)

**Problema detectado:**
- Actividades demasiado breves: "Implementar ClaveÚnica" (2 palabras)
- Falta de detalle técnico específico

**Solución implementada:**
```markdown
## ELIMINACIÓN DE HIPERSÍNTESIS

**CADA actividad debe tener entre 12-25 palabras (NO menos de 12)**
**CADA hito debe tener entre 10-20 palabras (NO menos de 10)**

**PROHIBIDO**: Enunciados genéricos
**OBLIGATORIO**: Especificar QUÉ exactamente, DÓNDE específicamente, CÓMO técnicamente

**Ejemplos de mejora:**

**Procedimiento Administrativo - Autenticación Digital:**
- ❌ ANTES: "Implementar ClaveÚnica en sistemas"
- ✅ AHORA: "Integrar el mecanismo de autenticación ClaveÚnica en el portal de trámites institucionales mediante el SDK oficial provisto por la Secretaría de Gobierno Digital"

**Gobernanza de Datos - Visión Estratégica:**
- ❌ ANTES: "Establecer compromiso directivo"
- ✅ AHORA: "Formalizar el compromiso de la alta dirección mediante la firma de una declaración institucional que establezca la gestión de datos como prioridad estratégica y asigne recursos específicos"
```

**Impacto:**
- ✅ Actividades con contexto técnico completo
- ✅ Desarrolladores entienden exactamente qué hacer

---

### Versión 7.0 - Indicadores Cualitativos (Octubre 17)

**Problema crítico:**
- Indicadores de resultado eran cuantitativos: "% de sistemas con ClaveÚnica"
- Se confundían con indicadores de proceso

**Solución conceptual:**

```markdown
## DIFERENCIA FUNDAMENTAL:

| Tipo | Enfoque | Naturaleza | Ejemplo |
|------|---------|------------|---------|
| **Indicador Proceso** | Mide ejecución | Cuantitativo | "% de sistemas integrados con ClaveÚnica" |
| **Indicador Resultado** | Mide impacto | Cualitativo | "Autenticación digital consolidada como mecanismo oficial" |

## REGLAS OBLIGATORIAS:

**PROHIBIDO - Indicadores Cuantitativos:**
- ❌ "% de páginas web con lenguaje claro"
- ❌ "Número de sistemas integrados"
- ❌ Cualquier cosa con: %, número, cantidad

**OBLIGATORIO - Indicadores Cualitativos:**
- ✅ "Autenticación digital consolidada como mecanismo único de acceso"
- ✅ "Comunicación clara establecida como estándar de calidad"

## ESTRUCTURA OBLIGATORIA:
[Concepto/Capacidad] + [Estado de consolidación] + [Contexto institucional]

## VERBOS/ESTADOS PERMITIDOS:
- consolidado, establecido, institucionalizado, implementado
- operativo, funcional, adoptado, normalizado, estandarizado
- incorporado, arraigado, habilitado, fortalecido, mejorado
```

**Ejemplos comparativos:**

| Dimensión | Antes (Cuantitativo) | Ahora (Cualitativo) |
|-----------|---------------------|---------------------|
| **PA** | "% de sistemas con ClaveÚnica" | "Autenticación digital mediante ClaveÚnica consolidada como mecanismo oficial de identificación en todos los canales digitales institucionales" |
| **GD** | "% de políticas implementadas" | "Política Institucional de Datos formalizada y operativa como marco normativo de gobierno de datos" |
| **CW** | "% de páginas con lenguaje claro" | "Comunicación digital clara y accesible establecida como estándar de calidad en todos los contenidos web institucionales" |

**Impacto:**
- ✅ Indicadores reflejan transformación institucional
- ✅ Diferenciación clara con indicadores de proceso

---

### Versión 8.0 - Progresión Incremental Gobernanza (Octubre 17)

**Problema crítico en Gobernanza de Datos:**
- Repetición de actividades entre niveles de madurez

**Ejemplo del problema:**
- Insuficiente→Básico: "Definir política de datos"
- Básico→Medio: "Definir política de datos" ❌ REPETIDO
- Medio→Avanzado: "Definir política de datos" ❌ REPETIDO

**Solución implementada:**

```markdown
## PROGRESIÓN INCREMENTAL OBLIGATORIA

**Regla fundamental**: Cada nivel debe CONSTRUIR sobre el anterior, no repetirlo

**VERBOS POR NIVEL**:

**Insuficiente → Básico** (Establecimiento inicial):
- Definir, Crear, Establecer, Identificar, Configurar, Designar
- Elaborar, Formalizar, Documentar, Especificar

**Básico → Medio** (Operativización):
- Implementar, Integrar, Desplegar, Aplicar, Expandir
- Ejecutar, Operacionalizar, Poner en marcha

**Medio → Avanzado** (Optimización):
- Automatizar, Optimizar, Consolidar, Escalar, Certificar
- Perfeccionar, Estandarizar, Sofisticar

**VALIDACIÓN OBLIGATORIA**:
Pregunta crítica: "¿Esto ya se hizo en el nivel anterior?"
- Si SÍ → NO incluir (evitar repetición)
- Si NO → Incluir (progresión correcta)
```

**Ejemplos de progresión correcta:**

```markdown
**Subdimensión "Gobierno de Datos":**

**Insuficiente → Básico** (Establecer):
- "Elaborar y aprobar la Política Institucional de Gestión de Datos"
- "Designar al Responsable del Gobierno de Datos institucional"

**Básico → Medio** (Implementar):
- "Implementar la Política Institucional en todas las unidades operativas"
- "Ejecutar el plan de trabajo del Responsable de Gobierno de Datos"

**Medio → Avanzado** (Automatizar):
- "Automatizar el monitoreo del cumplimiento de la Política mediante herramientas digitales"
- "Consolidar el gobierno de datos como práctica institucional certificada"
```

**Impacto:**
- ✅ Planes realistas que no duplican trabajo
- ✅ Cada nivel agrega valor sobre el anterior
- ✅ Alineación con modelo de madurez MGDE

---

### Versión 9.0 - Metodología HITOS-FIRST (Septiembre-Octubre)

**Concepto agregado:**
```markdown
## METODOLOGÍA OBLIGATORIA DE GENERACIÓN

**ORDEN DE CREACIÓN**:
1. **PRIMERO**: Crear los HITOS del plan (¿Cuáles van a ser los entregables clave del plan?)
2. **SEGUNDO**: Una vez establecidos los hitos, generar el conjunto de ACTIVIDADES que le corresponde a cada hito

**Lógica**:
- Definir PRIMERO las metas/entregables (hitos)
- DESPUÉS descomponer cada meta en pasos técnicos (actividades)
```

**Secuencia en el código:**
```python
# 1. Generar hitos
hitos = generar_hitos(dimension, subdimension)
print(f"Se han generado {len(hitos)} Hitos:")
for i, hito in enumerate(hitos, 1):
    print(f"{i}. {hito}")

# 2. Para cada hito, generar actividades
for hito in hitos:
    actividades = generar_actividades_para_hito(hito)
    print(f"\nGenerando Actividades para el Hito '{hito}'...")
    print(f"Se generaron {len(actividades)} Actividades")
```

---

### Versión 10.0 - Calidad Web: Hitos como Entregables (Octubre 8)

**Problema específico de Calidad Web:**
- Hitos se redactaban como métricas: "Asegurar que el 100% de contenidos sean claros"

**Corrección:**
```markdown
## HITOS COMO ENTREGABLES TANGIBLES

**INCORRECTO** (Hito como métrica):
- ❌ "Asegurar que el 100% de los contenidos sean claros y precisos"
- ❌ "Lograr el 95% de cumplimiento en fiabilidad"

**CORRECTO** (Hito como entregable):
- ✅ "Implementación completa del sistema de identificación de autoría en todas las páginas"
- ✅ "Establecimiento de protocolos de verificación y trazabilidad de información"
- ✅ "Creación del manual de estilo institucional para lenguaje claro"

**Características de un hito correcto**:
- ✅ Entregable CONCRETO y TANGIBLE
- ✅ Se puede completar y verificar como terminado
- ✅ Usa verbos de logro: Implementar, Establecer, Crear, Desarrollar
- ❌ NO usa: "Asegurar que X%", "Lograr X%", "Garantizar X%"
```

**Impacto:**
- ✅ Hitos representan productos tangibles
- ✅ Fácil verificar completitud

---

### Versión 11.0 - Especificidad Única por Indicador (Octubre 8)

**Problema de Calidad Web:**
- Hitos muy similares entre indicadores diferentes

**Ejemplo del problema:**
- Fiabilidad: "Establecimiento de un sistema integral de revisión..."
- Completitud: "Establecimiento de un sistema integral de revisión..."

**Solución:**
```markdown
## ESPECIFICIDAD ÚNICA POR INDICADOR

**REGLAS CRÍTICAS**:
1. UN SOLO HITO ÚNICO Y ESPECÍFICO para el indicador
2. NO usar frases genéricas que apliquen a cualquier indicador
3. Refleje directamente la esencia de la descripción del indicador

**EVITAR FRASES GENÉRICAS**:
- ❌ "Establecimiento de un sistema integral de revisión y actualización"
- ❌ "Implementación de mejoras en el sitio web"
- ❌ "Desarrollo de estrategias para mejorar la calidad"

**EJEMPLOS ESPECÍFICOS**:
- **Fiabilidad**: "Implementación del protocolo de verificación de fuentes y sistema de trazabilidad"
- **Completitud**: "Desarrollo de plantillas estandarizadas de contenido que garanticen exhaustividad"
- **Lenguaje Plano**: "Creación del manual de estilo institucional para lenguaje claro"
- **Accesibilidad**: "Implementación completa del estándar WCAG 2.1 nivel AA"

**Validación**: "¿Este hito solo aplica al indicador X?" → Debe ser SÍ
```

**Impacto:**
- ✅ Hitos únicos y diferenciados
- ✅ Fácil identificar qué hito corresponde a qué indicador

---

## 🔧 Componentes Técnicos del SuperPrompt

### 1. Sección de Identidad

**Propósito:** Establecer el rol del LLM

```markdown
## 🎯 IDENTIDAD DEL AGENTE

Eres el **Agente Maestro PTD**, un sistema integrado especializado en generar **Planes de Transformación Digital (PTD)** para el **Programa de Mejoramiento de la Gestión (PMG)** del gobierno chileno. Combinas las capacidades de tres agentes especializados:

1. **ClasificadorPMG**: Identifica brechas y propone actividades/hitos
2. **TRIA 2.0**: Valida metodológicamente según estándares oficiales  
3. **GeneradorPTD**: Estructura planes completos listos para OTF automática
```

**Por qué es importante:**
- Define el contexto completo del LLM
- Establece expectativas de calidad (OTF automática)
- Alinea con agentes especializados del dominio

### 2. Cantidades Mínimas por Complejidad

**Procedimiento Administrativo:**
```markdown
**COMPLEJIDAD MEDIA** (regla general):
- **MÍNIMO 7 hitos** con **7-9 actividades cada uno**
- **Total esperado**: MÍNIMO 49-63 actividades

**Ejemplo de complejidad MEDIA**: Autenticación digital, Interoperabilidad
```

**Gobernanza de Datos:**
```markdown
**Cantidades obligatorias**:
- **MÍNIMO 4-5 HITOS**
- **MÍNIMO 5-7 ACTIVIDADES por cada hito**
- **Total esperado**: MÍNIMO 20-35 actividades
```

**Calidad Web:**
```markdown
**Metodología especial**:
- **1 actividad por pregunta** (575 preguntas en total)
- **1 hito por indicador** (reutilizable para múltiples preguntas)
```

### 3. Ejemplos Técnicos por Subdimensión

**Estrategia:** Proveer 10 ejemplos concretos por subdimensión

**Autenticación digital (10 ejemplos):**
```markdown
1. Completar Solicitud de Credenciales de Integración a ClaveÚnica en gobdigital.cerofilas.gob.cl
2. Configurar endpoints de autenticación en el backend del sistema
3. Implementar flujo de redirección OAuth con ClaveÚnica
4. Integrar ClaveÚnica en los sistemas de autenticación institucionales
5. Configurar manejo de tokens JWT para sesiones de usuario
6. Realizar pruebas de integración en ambiente de desarrollo
7. Implementar validación de certificados digitales
8. Certificar la operatividad de ClaveÚnica en los procedimientos
9. Configurar políticas de seguridad para sesiones autenticadas
10. Implementar logs de auditoría de autenticación
```

**Por qué funciona:**
- LLM aprende el nivel de detalle esperado
- Ejemplos son copias literales de URLs y herramientas reales
- Establece el "estilo" de redacción técnica

### 4. Validación por Palabras Prohibidas

**Lista de palabras/frases que NO deben aparecer:**
```python
palabras_prohibidas = [
    'capacitación', 'capacitar', 'entrenamiento',
    'evaluar', 'evaluación', 'auditoría',
    'monitorear', 'monitoreo', 'seguimiento continuo',
    'optimizar', 'optimización', 'mejora continua',
    'lecciones aprendidas', 'retroalimentación',
    'revisar periódicamente', 'actualización constante'
]
```

**Implementación en scripts:**
```python
def validar_plan_100_tecnico(plan_texto):
    violaciones = []
    for palabra in palabras_prohibidas:
        if palabra.lower() in plan_texto.lower():
            violaciones.append(palabra)
    
    if violaciones:
        print(f"❌ VIOLACIONES DETECTADAS: {', '.join(violaciones)}")
    else:
        print("✅ SIN VIOLACIONES - Plan 100% técnico")
    
    return len(violaciones) == 0
```

### 5. Estructura JSON de Output

**Formato esperado:**
```markdown
**Formato de Plan en Celda Única**:
```
Actividad: [Acción específica 1.1]
Actividad: [Acción específica 1.2]
Actividad: [Acción específica 1.3]
Hito: [Descripción del entregable 1]
Actividad: [Acción específica 2.1]
Actividad: [Acción específica 2.2]
Hito: [Descripción del entregable 2]
```

**Por qué este formato:**
- Fácil de parsear con regex
- Compatible con inserción en Excel/DB
- Orden lógico: actividades → hito correspondiente

---

## 📊 Métricas de Evolución del SuperPrompt

### Evolución de Longitud

| Versión | Líneas | Palabras | Caracteres | Fecha |
|---------|--------|----------|------------|-------|
| v1.0 | 100 | 500 | 3,000 | Sept 2025 |
| v2.0 | 200 | 1,000 | 6,000 | Oct 8 |
| v4.0 | 500 | 2,500 | 15,000 | Oct 10 |
| v6.0 | 800 | 4,000 | 24,000 | Oct 17 |
| v11.0 | 1,500+ | 8,000+ | 50,000+ | Oct 17 |

### Evolución de Calidad de Planes

| Métrica | v1.0 | v4.0 | v11.0 (Final) |
|---------|------|------|---------------|
| **Actividades por plan** | 10-15 | 30-40 | 49-63 (PA) / 20-35 (GD) |
| **Palabras por actividad** | 5-8 | 10-15 | 12-25 |
| **% técnico** | 60% | 85% | 100% |
| **Especificidad** | Baja | Media | Alta |
| **Violaciones** | 15-20 | 5-10 | 0-3 |

### Iteraciones por Tipo de Cambio

| Tipo de cambio | Iteraciones | Impacto |
|---------------|------------|---------|
| **Cantidades** | 3 | Alto |
| **Formato** | 2 | Medio |
| **Enfoque técnico** | 4 | Crítico |
| **Especificidad** | 2 | Alto |
| **Indicadores** | 2 | Alto |
| **Progresión incremental** | 1 | Alto (GD) |

---

## 🎓 Lecciones Aprendidas

### 1. Iteración con Feedback Real es Clave

**Lección:** Un prompt no se perfecciona en la primera versión

**Evidencia:**
- v1.0 → v11.0 = 11 versiones mayores
- 15+ iteraciones menores
- 2 meses de refinamiento continuo

**Aplicación:** Siempre probar con usuarios reales del dominio (desarrolladores)

### 2. Ejemplos Concretos > Reglas Abstractas

**Lección:** LLM aprende mejor con ejemplos que con reglas

**Evidencia:**
- 60 ejemplos técnicos específicos en PA
- 10 ejemplos por subdimensión
- Ejemplos con URLs reales y herramientas específicas

**Aplicación:** Incluir ejemplos literales del dominio

### 3. Validación Automática es Esencial

**Lección:** No confiar solo en el LLM, validar output

**Evidencia:**
- Lista de palabras prohibidas
- Script de validación automática
- Reporteo de violaciones

**Aplicación:** Implementar validaciones post-generación

### 4. Contexto de Dominio es Crítico

**Lección:** LLM necesita entender el "para quién" y "para qué"

**Evidencia:**
- Cambio fundamental: "planes para desarrolladores"
- Eliminación de gestión organizacional
- Enfoque en implementación técnica

**Aplicación:** Definir claramente la audiencia objetivo

### 5. Restricciones Claras Mejoran Calidad

**Lección:** Límites estrictos previenen desviaciones

**Evidencia:**
- Cantidades mínimas/máximas
- Palabras/frases prohibidas
- Regla de Oro: "Plan termina al cerrar brecha"

**Aplicación:** Establecer boundaries claros y explícitos

### 6. Especificidad vs Brevedad

**Lección:** Brevedad extrema sacrifica utilidad

**Evidencia:**
- "Implementar ClaveÚnica" (inútil para desarrollador)
- "Integrar el mecanismo de autenticación ClaveÚnica en el portal de trámites institucionales mediante el SDK oficial provisto por la Secretaría de Gobierno Digital" (útil)

**Aplicación:** Balance entre concisión y completitud

### 7. Progresión Incremental en Madurez

**Lección:** Niveles de madurez requieren verbos específicos

**Evidencia:**
- Insuficiente→Básico: Definir, Crear
- Básico→Medio: Implementar, Integrar
- Medio→Avanzado: Automatizar, Optimizar

**Aplicación:** Mapear niveles a acciones específicas

---

## 🔄 Proceso de Iteración

### Ciclo de Mejora

```
┌─────────────────────────────────────────────────────────┐
│                  CICLO DE ITERACIÓN                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│  1. GENERACIÓN                                          │
│     └─ Ejecutar script con SuperPrompt actual          │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  2. EVALUACIÓN                                          │
│     ├─ Validación automática (palabras prohibidas)     │
│     ├─ Revisión manual (desarrollador/experto)         │
│     └─ Métricas (# actividades, especificidad, etc.)   │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  3. IDENTIFICACIÓN DE PROBLEMAS                         │
│     ├─ ¿Violaciones detectadas?                        │
│     ├─ ¿Feedback negativo del usuario?                 │
│     ├─ ¿Planes muy cortos/largos?                      │
│     └─ ¿Actividades genéricas?                         │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  4. MODIFICACIÓN DEL SUPERPROMPT                        │
│     ├─ Agregar reglas específicas                      │
│     ├─ Expandir lista de prohibiciones                 │
│     ├─ Agregar ejemplos concretos                      │
│     └─ Ajustar cantidades mínimas/máximas             │
└──────────────┬──────────────────────────────────────────┘
               │
               ▼
┌─────────────────────────────────────────────────────────┐
│  5. DOCUMENTACIÓN                                       │
│     ├─ Actualizar CHANGELOG.md                         │
│     ├─ Documentar cambio en SuperPrompt                │
│     └─ Versionar (v1.0 → v2.0)                         │
└──────────────┬──────────────────────────────────────────┘
               │
               └──────────────┐
                             │
                             ▼
                    ¿Calidad aceptable?
                             │
                   ┌─────────┴─────────┐
                   │                   │
                  SÍ                  NO
                   │                   │
                   ▼                   │
            FIN DEL CICLO              │
                                       │
                                       └─── REPETIR CICLO
```

### Ejemplo de Ciclo Real

**Iteración Octubre 10 - Enfoque 100% Técnico:**

1. **GENERACIÓN:** 
   - Ejecutar `prueba_generar_pa.py`
   - Generar plan para "Autenticación digital"

2. **EVALUACIÓN:**
   - Desarrollador revisa plan
   - Detecta: 9 violaciones (capacitaciones, evaluaciones, monitoreo)

3. **IDENTIFICACIÓN:**
   - Problema: Mezcla implementación con gestión organizacional
   - Feedback: "Planes son para desarrolladores, solo parte técnica"

4. **MODIFICACIÓN:**
   - Agregar sección "ENFOQUE 100% TÉCNICO"
   - Lista de actividades prohibidas
   - Lista de actividades permitidas
   - 60 ejemplos técnicos específicos

5. **DOCUMENTACIÓN:**
   - CHANGELOG.md: Nueva entrada [2025-10-10 - 18:00]
   - SuperPrompt: v4.0 → v5.0

6. **VALIDACIÓN:**
   - Ejecutar script nuevamente
   - Resultado: 0 violaciones
   - ✅ Calidad aceptable

---

## 🛠️ Herramientas de Desarrollo

### Scripts de Testing

**prueba_generar_pa.py:**
```python
# Prueba rápida de un plan específico
def probar_plan(subdimension):
    datos = leer_datos(subdimension)
    superprompt = cargar_superprompt()
    plan = generar_plan_ptd(datos, superprompt)
    
    # Validación automática
    validar_plan_100_tecnico(plan)
    
    # Contar elementos
    contar_actividades_hitos(plan)
    
    # Mostrar plan
    print(plan)
```

### Validador de Calidad

**validar_calidad_plan.py:**
```python
def validar_calidad(plan):
    checks = {
        'violaciones': validar_palabras_prohibidas(plan),
        'cantidad_actividades': contar_actividades(plan),
        'longitud_actividades': validar_longitud(plan, min=12, max=25),
        'especificidad': medir_especificidad(plan),
        'formato': validar_formato(plan)
    }
    
    score = calcular_score(checks)
    return score, checks
```

### Comparador de Versiones

**comparar_versiones.py:**
```python
def comparar_versiones(v_anterior, v_actual, subdimension):
    plan_anterior = generar_con_version(v_anterior, subdimension)
    plan_actual = generar_con_version(v_actual, subdimension)
    
    comparacion = {
        'actividades_antes': contar_actividades(plan_anterior),
        'actividades_ahora': contar_actividades(plan_actual),
        'violaciones_antes': contar_violaciones(plan_anterior),
        'violaciones_ahora': contar_violaciones(plan_actual),
        'especificidad_antes': medir_especificidad(plan_anterior),
        'especificidad_ahora': medir_especificidad(plan_actual)
    }
    
    print_comparacion(comparacion)
```

---

## 📚 Referencias y Recursos

### Documentos Base

1. **Guía Metodológica STD:** Transformación Digital del Estado
2. **Marco MGDE:** Marco de Gobierno de Datos del Estado
3. **Normativas ClaveÚnica:** gobdigital.cerofilas.gob.cl
4. **Red de Interoperabilidad:** Estándares de intercambio

### Papers y Artículos Relevantes

- "Few-Shot Learning for Prompts" (OpenAI, 2023)
- "Chain-of-Thought Prompting" (Wei et al., 2022)
- "Constitutional AI" (Anthropic, 2022)

### Herramientas Utilizadas

- **LangChain:** Framework para LLM
- **OpenAI GPT-4o:** Modelo de lenguaje
- **VS Code:** Editor de texto
- **Git:** Control de versiones

---

## 💡 Recomendaciones para Nuevos SuperPrompts

### 1. Comienza con Identidad Clara

```markdown
## IDENTIDAD DEL AGENTE
Eres [ROL], especializado en [DOMINIO].
Tu objetivo es [OBJETIVO PRINCIPAL].
Trabajas para [AUDIENCIA] que necesita [NECESIDAD].
```

### 2. Provee Ejemplos Abundantes

- Mínimo 5-10 ejemplos por caso de uso
- Ejemplos deben ser del dominio real
- Incluir tanto correctos como incorrectos

### 3. Establece Restricciones Claras

```markdown
**PROHIBIDO**:
- ❌ [Lista específica]

**OBLIGATORIO**:
- ✅ [Lista específica]
```

### 4. Itera con Usuarios Reales

- No asumas que la v1.0 es perfecta
- Recoge feedback específico
- Ajusta basado en resultados reales

### 5. Documenta Cada Cambio

- CHANGELOG.md con fecha y razón
- Versionar el SuperPrompt
- Explicar impacto de cada cambio

### 6. Implementa Validación Automática

- Script de validación post-generación
- Métricas cuantitativas
- Detección de patrones problemáticos

### 7. Balancea Flexibilidad y Restricción

- No sobre-restringir (mata creatividad)
- No sub-restringir (permite desvíos)
- Encontrar el punto medio

---

## 📝 Conclusión

El desarrollo del SuperPrompt fue un **proceso iterativo de 2 meses** que transformó un prompt genérico de 100 líneas en un sistema de instrucciones de 1,500+ líneas altamente especializado.

**Claves del éxito:**
1. ✅ Feedback continuo de usuarios reales
2. ✅ Validación automática de calidad
3. ✅ Ejemplos abundantes del dominio
4. ✅ Restricciones claras y explícitas
5. ✅ Documentación exhaustiva de cambios
6. ✅ Pruebas iterativas con scripts de testing

**Resultado final:**
- Planes 100% técnicos
- Especificidad alta (12-25 palabras/actividad)
- Progresión incremental (Gobernanza)
- Indicadores cualitativos
- 0-3 violaciones por plan

Este SuperPrompt ahora puede ser **adaptado a otros PMG** siguiendo la misma metodología de desarrollo iterativo documentada en este archivo.

---

**Última actualización:** 12 de noviembre de 2025  
**Versión del SuperPrompt:** v11.0  
**Versión del documento:** 1.0
