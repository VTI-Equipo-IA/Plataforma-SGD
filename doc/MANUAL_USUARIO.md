# 📖 Manual de Usuario - Editor de Portafolio de Transformación Digital

## 🎯 ¿Qué es esta aplicación?

El **Editor de Portafolio de Transformación Digital** es una herramienta web que te permite gestionar y mejorar el portafolio estratégico de transformación digital de tu organización. La aplicación te ayuda a:

- ✅ Visualizar y editar elementos del portafolio
- 🤖 Regenerar el portafolio usando Inteligencia Artificial
- 📊 Comparar diferentes versiones del portafolio
- 💾 Importar y exportar datos en formato JSON
- 🔍 Buscar y filtrar información específica

---

## 📚 Tabla de Contenidos

1. [Primeros Pasos](#primeros-pasos)
2. [Navegación Principal](#navegación-principal)
3. [Trabajar con Portafolio](#trabajar-con-portafolio)
4. [Regeneración con IA](#regeneración-con-ia)
5. [Importar y Exportar Datos](#importar-y-exportar-datos)
6. [Comparar Versiones](#comparar-versiones)
7. [Configuración](#configuración)
8. [Gestión de Prompts](#-gestión-de-prompts-nuevo-en-v21) (Nuevo en v2.1)
9. [Preguntas Frecuentes](#preguntas-frecuentes)
10. [Solución de Problemas](#solución-de-problemas)

---

## 🚀 Primeros Pasos

### Acceder a la aplicación

1. Abre tu navegador web (Chrome, Firefox, Edge, Safari)
2. Ingresa la URL de la aplicación proporcionada por tu administrador
3. Verás la página principal con las dimensiones de transformación digital

### Interfaz principal

Al abrir la aplicación verás:

```
┌─────────────────────────────────────────────────────────────────┐
│  📋 Editor de Portafolio - PTD                                  │
├─────────────────────────────────────────────────────────────────┤
│  [Buscar...] [Buscar]                                           │
│  [Nivel/Instrumento/Portafolio] [Cambiar] 🤖 🤝 Vista total     │
│                                                 Vista comparativa│
├─────────────────────────────────────────────────────────────────┤
│  [Tabs: Gobernanza | Calidad Web | Procedimiento]              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Tabla con elementos del portafolio]                          │
│  - Click en columnas para filtrar y ordenar                    │
│  - Botón + para agregar fila debajo (solo Vista por Portafolio)│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🧭 Navegación Principal

### Pestañas de Dimensiones

La aplicación organiza el portafolio en **3 dimensiones**:

#### 📊 Gobernanza de Datos
- **¿Qué es?** Elementos del portafolio para mejorar la gestión y calidad de los datos
- **Incluye:** Políticas de datos, roles y responsabilidades, procesos de gestión
- **Cuándo usar:** Para organizar cómo tu institución maneja la información

#### 🌐 Calidad Web
- **¿Qué es?** Elementos del portafolio para mejorar la presencia web institucional
- **Incluye:** Diseño web, accesibilidad, contenidos digitales
- **Cuándo usar:** Para mejorar tu sitio web y servicios en línea

#### 📝 Procedimiento Administrativo
- **¿Qué es?** Elementos del portafolio para digitalizar trámites y procedimientos
- **Incluye:** Automatización de procesos, sistemas de gestión, atención ciudadana
- **Cuándo usar:** Para hacer más eficientes los trámites institucionales

### Barra de Herramientas Superior

La toolbar se divide en dos secciones:

#### Sección Izquierda - Búsqueda
| Elemento | Función | Cómo usar |
|----------|---------|-----------|
| **Campo de búsqueda** | Busca texto en todas las columnas visibles | Escribe y presiona Enter o click en "Buscar" |
| **Botón Buscar** | Ejecuta la búsqueda | Click para aplicar filtro de búsqueda |
| **Botón Limpiar** | Quita el filtro de búsqueda | Aparece solo cuando hay búsqueda activa |

#### Sección Derecha - Filtros y Acciones
| Botón/Selector | Función | Cuándo usar | Disponible en |
|----------------|---------|-------------|---------------|
| **Nivel de Madurez** (selector) | Filtra portafolio por nivel específico | Solo en Gobernanza de Datos | Vista por Portafolio |
| **Instrumento** (selector) | Filtra portafolio por instrumento | Solo en Calidad Web | Vista por Portafolio |
| **Portafolio** (selector) | Filtra por subdimensión específica | Todas las dimensiones | Vista por Portafolio |
| **Cambiar** | Aplica los filtros seleccionados | Después de cambiar selectores | Vista por Portafolio |
| **🤖 Regenerar portafolio (Agente Maestro)** | Regenera portafolio usando IA (GPT-4) | Mejorar portafolio completo automáticamente | Vista por Portafolio |
| **🤝 Regenerar portafolio (Comité)** | Refina un elemento del portafolio con 5 agentes especializados | Análisis detallado | Vista por Portafolio |
| **Vista total / Vista por portafolio** | Cambia entre ver todos o filtrar | Alternar modo de visualización | Siempre |
| **Vista comparativa / Vista normal** | Compara Agente Maestro vs Comité | Ver diferencias lado a lado | Vista por Portafolio |
| **📝 Gestión de Prompts** | Edita y versiona el SuperPrompt del Agente Maestro | Modificar comportamiento de la IA | Siempre (desde v2.1) |
| **📤 Exportar Portafolio** | Exporta portafolio a JSON | Hacer backup o migrar datos | Siempre |

---

## 📝 Trabajar con Portafolio

### Modos de Visualización

La aplicación ofrece dos modos principales:

#### Vista por Portafolio (Modo Filtrado)
- **Por defecto** al entrar a la aplicación
- Muestra solo los elementos del portafolio de una subdimensión específica
- Selectores en la toolbar para cambiar filtros
- Botón **+** visible en cada fila para agregar elementos del portafolio
- Ideal para trabajar enfocado en una subdimensión específica del portafolio

#### Vista Total (Modo Completo)
- Muestra **todos** los elementos del portafolio de la dimensión
- Sin filtros aplicados
- No hay botón + en las filas
- Ideal para ver el panorama completo

**Cambiar entre vistas:** Click en "Vista total" o "Vista por portafolio" en la toolbar

### Vista Comparativa

En **Vista por Portafolio**, puedes activar la **Vista Comparativa** para ver:
- **Lado izquierdo:** Planes del Agente Maestro
- **Lado derecho:** Planes del Comité
- Solo muestra columnas: Tipo y Descripción
- Permite comparar las propuestas de ambos sistemas de IA

**Activar:** Click en "Vista comparativa" (solo disponible en Vista por Portafolio)

### Ver la tabla del portafolio

La tabla muestra información organizada en columnas (pueden variar según la dimensión):

| Columna | Descripción | Ejemplo | Ordenable | Filtrable |
|---------|-------------|---------|-----------|-----------|
| **Subdimensión** | Área específica del portafolio | "Estrategia y Gobierno del Dato" | ✅ | ✅ |
| **Instrumento** | Herramienta o documento | "Política de Datos Abiertos" | ✅ | ✅ |
| **Nivel Madurez** | Estado de implementación | "Inicial", "Definido" | ✅ | ✅ |
| **Tipo** | Tipo de actividad/hito | "Hito", "Actividad" | ✅ | ✅ |
| **Descripción** | Detalle del elemento del portafolio | Texto descriptivo | ✅ | ❌ |
| **Autor** | Quién creó el elemento del portafolio | "Agente Maestro", "Comité" | ✅ | ✅ |
| **Acciones** | Botones de acción | +, ✏️, 🗑️ | ❌ | ❌ |

### Funciones de columnas

#### Ordenar por columna
1. **Click en el nombre de la columna**
2. **Primera vez:** Orden ascendente (▲)
3. **Segunda vez:** Orden descendente (▼)
4. **Tercera vez:** Sin orden (vuelve al orden original)

#### Filtrar por columna
1. **Click en el nombre de la columna**
2. **Aparecerá un menú** con valores únicos de esa columna
3. **Selecciona uno o varios valores** para filtrar
4. **La tabla mostrará solo** las filas que coincidan

### Editar un elemento del portafolio

1. **Localiza el elemento del portafolio** que deseas editar en la tabla
2. **Haz clic en el botón ✏️** (lápiz) en la columna "Acciones"
3. **Aparecerá un formulario** con los campos editables:
   - Subdimensión
   - Instrumento
   - Nivel de Madurez
   - Hito
   - Actividad
4. **Modifica los campos** que necesites cambiar
5. **Haz clic en "Guardar"** para aplicar los cambios
6. **O haz clic en "Cancelar"** para descartar cambios

> 💡 **Tip:** Los cambios se guardan inmediatamente en la base de datos

### Agregar un nuevo elemento del portafolio

> **Importante:** El botón + solo aparece en **Vista por Portafolio**

#### Método 1: Agregar fila debajo de otra (recomendado)

1. **Localiza el elemento del portafolio** después del cual quieres agregar uno nuevo
2. **Click en el botón +** en la columna de acciones de esa fila
3. **Se insertará una nueva fila vacía** justo debajo
4. **Completa los campos directamente en la tabla** (edición inline)
5. **Los campos se guardan automáticamente** al salir de cada celda

**Ventajas de este método:**
- Mantiene el orden lógico del portafolio
- Más rápido (no abre formulario separado)
- Ideal para agregar múltiples elementos consecutivos

#### Método 2: Edición en formulario modal

1. **Haz doble click** en cualquier celda de la fila
2. **Se abrirá un formulario** con todos los campos
3. **Completa o modifica** los campos necesarios
4. **Click en "Guardar"** para aplicar cambios
5. **O "Cancelar"** para descartar

### Eliminar un elemento del portafolio

1. **Localiza el elemento del portafolio** que deseas eliminar
2. **Haz clic en el botón 🗑️** (papelera) en la columna "Acciones"
3. **Aparecerá un mensaje de confirmación**: "¿Estás seguro de eliminar este elemento del portafolio?"
4. **Haz clic en "Confirmar"** para eliminarlo definitivamente
5. **O haz clic en "Cancelar"** para mantener el elemento del portafolio

> ⚠️ **Advertencia:** La eliminación es permanente y no se puede deshacer

### Buscar y filtrar

#### Búsqueda de texto
1. **Escribe en el campo "Buscar..."** en la parte superior izquierda
2. **Click en "Buscar"** o presiona Enter
3. **La tabla mostrará solo las filas** que contienen el texto buscado
4. **Busca en múltiples columnas:** Subdimensión, Instrumento, Descripción, Autor, etc.
5. **Click en "Limpiar"** para quitar el filtro de búsqueda

**Tip:** La búsqueda no distingue mayúsculas de minúsculas

#### Filtros en Vista por Portafolio

Según la dimensión activa, verás diferentes selectores:

**Gobernanza de Datos:**
- Selector **"Nivel de Madurez"**: Inicial, Gestionado, Definido, Cuantitativo, Optimizado
- Selector **"Portafolio"**: Lista de subdimensiones disponibles

**Calidad Web:**
- Selector **"Instrumento"**: Lista de instrumentos de evaluación
- Selector **"Portafolio"**: Lista de subdimensiones específicas del instrumento

**Procedimiento Administrativo:**
- Selector **"Portafolio"**: Lista de subdimensiones disponibles

**Uso de selectores:**
1. **Selecciona los valores** que desees en cada selector
2. **Click en "Cambiar"** (botón único para aplicar todos los filtros)
3. **La tabla se actualizará** mostrando solo los elementos del portafolio que coincidan

#### Ordenar por columnas
1. **Click en el nombre de cualquier columna**
2. **Primera vez:** Orden ascendente ▲ (A-Z, 0-9)
3. **Segunda vez:** Orden descendente ▼ (Z-A, 9-0)
4. **Los datos se reordenarán** automáticamente

**Tip:** Puedes combinar búsqueda, filtros y ordenamiento simultáneamente

---

## 🤖 Regeneración con IA

La aplicación ofrece **dos sistemas de regeneración** con Inteligencia Artificial:

### Sistema 1: Agente Maestro (🤖)

**¿Qué hace?**  
Regenera el **portafolio** de la subdimensión seleccionada usando un solo agente de IA potente (GPT-4).

**¿Cuándo usarlo?**
- Estás en **Vista por Portafolio** con una subdimensión específica seleccionada
- Estás en **Vista por Portafolio** con una subdimensión específica seleccionada
- Quieres actualizar completamente el portafolio actual
- Necesitas regeneración rápida basada en los filtros activos
- Buscas un enfoque **automatizado y completo**

**Disponibilidad:**
- ✅ Solo en **Vista por Portafolio**
- ❌ No disponible en Vista Total
- Requiere tener seleccionados los filtros (Subdimensión, Instrumento o Nivel de Madurez según dimensión)

**Cómo usarlo:**

#### Regenerar el portafolio actual

1. **Asegúrate de estar en Vista por Portafolio**
2. **Selecciona los filtros necesarios:**
   - **Gobernanza de Datos:** Nivel de Madurez + Portafolio
   - **Calidad Web:** Instrumento + Portafolio
   - **Procedimiento Administrativo:** Solo Portafolio
3. **Click en botón 🤖** "Regenerar portafolio (Agente Maestro)"
4. **Aparecerá modal de confirmación** mostrando:
   - Dimensión a regenerar
   - Filtros activos (subdimensión, instrumento, nivel)
5. **Click en "Iniciar Regeneración"**
6. **Observa el progreso:**
   - Barra de progreso 0-100%
   - Mensajes: "Analizando contexto...", "Generando hitos...", "Creando actividades..."
7. **Al completar (100%):**
   - Mensaje: "✅ Regeneración completada"
   - Click en "Aceptar"
8. **La página se recarga automáticamente** mostrando los nuevos datos

**Ejemplo visual del proceso:**

```
Usuario hace clic en 🤖
         ↓
┌─────────────────────────┐
│  🤖 Regenerar con IA   │
├─────────────────────────┤
│ Dimensión: Gobernanza   │
│ Subdimensión: [Auto]    │
│ Instrumento: [Auto]     │
│ Nivel: [Auto]          │
│                         │
│ [Iniciar] [Cancelar]   │
└─────────────────────────┘
         ↓
┌─────────────────────────┐
│ ⏳ Procesando...       │
│ ████████░░░░ 65%       │
│                         │
│ "Generando hitos..."    │
└─────────────────────────┘
         ↓
┌─────────────────────────┐
│ ✅ ¡Completado!        │
│                         │
│ Se regeneraron 12 elementos del portafolio │
│                         │
│ [Aceptar]              │
└─────────────────────────┘
```

### Sistema 2: Comité de Agentes (🤝)

**¿Qué hace?**  
Refina **el elemento del portafolio seleccionado** usando múltiples agentes especializados que debaten y lo mejoran desde diferentes perspectivas.

**¿Cuándo usarlo?**
- Estás en **Vista por Portafolio**
- Quieres un análisis **detallado y multidimensional**
- Necesitas validación desde **múltiples perspectivas** (legal, técnica, de implementación)
- Buscas **refinamiento de alta calidad** con debate entre expertos

**Disponibilidad:**
- ✅ Solo en **Vista por Portafolio**
- ❌ No disponible en Vista Total
- Funciona con los filtros actualmente seleccionados

**Los 5 agentes especializados:**

1. **🎯 PMG (Project Manager Gobernanza)** 
   - Coordina el proceso y estructura el plan
   - Define objetivos claros y alcanzables
   
2. **⚖️ Abogado** 
   - Revisa aspectos legales y normativos
   - Valida cumplimiento regulatorio
   
3. **💻 Desarrollador** 
   - Evalúa viabilidad técnica
   - Propone soluciones tecnológicas
   
4. **🚀 Implementador** 
   - Analiza factibilidad de ejecución
   - Identifica recursos necesarios
   
5. **📝 Secretario** 
   - Documenta conclusiones del debate
   - Sintetiza aportes de todos los agentes

**Cómo usarlo:**

1. **Asegúrate de estar en Vista por Portafolio**
2. **Selecciona los filtros** del elemento del portafolio que quieres refinar
3. **Click en botón 🤝** "Regenerar portafolio (Comité)"
4. **Aparecerá modal** mostrando el elemento seleccionado
5. **Click en "Iniciar Refinamiento"**
6. **Observa el progreso del comité:**
   ```
   🎯 PMG analizando estructura... ✅
   ⚖️ Abogado revisando normativa... ✅
   � Desarrollador evaluando técnica... ⏳
   🚀 Implementador analizando ejecución... ⏸️
   📝 Secretario preparando síntesis... ⏸️
   
   Progreso: ████████░░░░ 65%
   ```
7. **Al completar:**
   - Mensaje: "✅ Refinamiento completado con aportes de 5 expertos"
   - Los 5 agentes han debatido y mejorado el elemento del portafolio
8. **Click en "Ver cambios"** para comparar versiones
9. **La página se recarga** mostrando el elemento del portafolio refinado

**Ejemplo del proceso del comité:**

```
Usuario hace clic en 🤝 para un elemento específico
         ↓
┌─────────────────────────────┐
│  🤝 Refinar con Comité     │
├─────────────────────────────┤
│ Elemento seleccionado: #142 │
│                             │
│ ¿Qué deseas regenerar?      │
│ ○ Solo portafolio           │
│ ○ Solo hitos                │
│ ● Todo el portafolio        │
│                             │
│ [Iniciar] [Cancelar]        │
└─────────────────────────────┘
         ↓
┌─────────────────────────────┐
│ 🎯 PMG analizando... ✅     │
│ ⚖️ Abogado revisando... ✅  │
│ 💻 Desarrollador evaluando.⏳│
│ 🚀 Implementador... ⏸️      │
│ 📝 Secretario... ⏸️         │
│                             │
│ ████████░░░░ 60%           │
└─────────────────────────────┘
         ↓
┌─────────────────────────────┐
│ ✅ ¡Refinamiento completo! │
│                             │
│ El elemento ha sido mejorado│
│ con aportes de 5 expertos   │
│                             │
│ [Ver cambios] [Cerrar]      │
└─────────────────────────────┘
```

### Comparación de sistemas

| Característica | Agente Maestro 🤖 | Comité 🤝 |
|----------------|-------------------|-----------|
| **Alcance** | Portafolio (según filtros) | Elemento del portafolio seleccionado |
| **Velocidad** | Rápido (2-5 min) | Más lento (5-8 min) |
| **Profundidad** | Análisis automático completo | Debate multidimensional detallado |
| **Perspectivas** | Una (GPT-4) | Cinco (PMG, Abogado, Desarrollador, Implementador, Secretario) |
| **Proceso** | Generación directa | Debate iterativo entre agentes |
| **Mejor para** | Actualización rápida y completa | Refinamiento con validación experta |
| **Uso típico** | Regeneración periódica | Elementos estratégicos críticos |
| **Disponibilidad** | Solo Vista por Portafolio | Solo Vista por Portafolio |
| **Resultado** | Portafolio cohesivo y estructurado | Elemento validado multidimensionalmente |

### Consejos para usar la IA

✅ **Mejores prácticas:**
- **Selecciona los filtros correctos** antes de regenerar (subdimensión, instrumento, nivel)
- **Usa Agente Maestro (🤖)** para actualizaciones rápidas del portafolio
- **Usa Comité (🤝)** cuando necesites análisis desde múltiples perspectivas
- **Activa Vista Comparativa** después de usar ambos sistemas para comparar resultados
- **Edita manualmente** los elementos regenerados para ajustarlos a tu contexto específico
- **No cierres la ventana** mientras la regeneración está en progreso
- **Espera a que complete al 100%** antes de editar los datos

⚠️ **Evita:**
- Regenerar sin tener los filtros adecuados seleccionados
- Cambiar de pestaña o dimensión durante la regeneración
- Cancelar procesos a mitad de ejecución (los cambios parciales no se guardan)
- Regenerar el mismo elemento múltiples veces consecutivas sin revisar los resultados
- Usar regeneración en Vista Total (no está disponible)
- Editar manualmente mientras el sistema está regenerando

---

## 💾 Importar y Exportar Datos

### Exportar datos

**¿Para qué sirve?**
- Crear respaldos de tu portafolio
- Compartir datos con otros sistemas
- Analizar datos en Excel u otras herramientas
- Cumplir requisitos de auditoría

**Cómo exportar:**

1. **Haz clic en el botón 💾** "Exportar" en la barra superior
2. **Selecciona qué exportar:**
   - ✅ Dimensión actual (solo la pestaña activa)
   - ✅ Todas las dimensiones (todo el sistema)
3. **Elige el formato:**
   - **JSON** (recomendado para importar después)
   - **CSV** (para Excel o análisis de datos)
4. **Haz clic en "Descargar"**
5. **El archivo se descargará** a tu carpeta de Descargas

**Nombre del archivo:**
```
portafolio_gobernanza_2025-11-11.json
portafolio_todos_2025-11-11.json
```

### Importar datos

**¿Para qué sirve?**
- Restaurar respaldos previos
- Cargar planes desde otro sistema
- Actualizar múltiples planes de una vez
- Migrar datos entre ambientes

**Cómo importar:**

1. **Prepara tu archivo JSON** con el formato correcto (ver sección "Formato de importación" abajo)
2. **Haz clic en el botón 📥** "Importar" en la barra superior
3. **Se abrirá un cuadro de diálogo**
4. **Haz clic en "Seleccionar archivo"** o arrastra el archivo
5. **Verifica la vista previa** de los datos a importar
6. **Selecciona el modo de importación:**
   - **Reemplazar todo**: Borra datos existentes y carga los nuevos
   - **Agregar/Actualizar**: Mantiene datos existentes y añade/actualiza
   - **Solo agregar nuevos**: Solo añade planes que no existan
7. **Haz clic en "Importar"**
8. **Espera la confirmación** (puede tomar 10-30 segundos)
9. **Recibirás un resumen:**
   ```
   ✅ Importación exitosa
   - 45 planes importados
   - 12 planes actualizados
   - 3 planes duplicados (omitidos)
   ```

### Formato de importación (JSON)

Tu archivo JSON debe tener esta estructura:

```json
{
  "dimension": "Gobernanza de Datos",
  "planes": [
    {
      "subdimension": "Estrategia y Gobierno del Dato",
      "instrumento": "Política de Datos Abiertos",
      "nivel_madurez": "Definido",
      "hito": "Implementar catálogo de datos abiertos",
      "actividad": "Desarrollar plataforma web para publicación de datasets"
    },
    {
      "subdimension": "Calidad y Gestión de Datos",
      "instrumento": "Manual de Calidad de Datos",
      "nivel_madurez": "Inicial",
      "hito": "Definir estándares de calidad",
      "actividad": "Crear documento con criterios de validación"
    }
  ]
}
```

**Campos requeridos:**
- `subdimension`: Nombre exacto de la subdimensión
- `instrumento`: Descripción del instrumento
- `nivel_madurez`: Uno de: "Inicial", "Gestionado", "Definido", "Cuantitativo", "Optimizado"
- `hito`: Descripción del objetivo
- `actividad`: Descripción de la tarea

> ⚠️ **Importante:** Los nombres de subdimensión deben coincidir exactamente con los existentes

---

## 🔍 Vista Comparativa

La aplicación permite comparar elementos del portafolio generados por el **Agente Maestro** vs el **Comité** lado a lado.

### ¿Qué es la Vista Comparativa?

- **Disponible solo en Vista por Portafolio**
- Muestra dos tablas en paralelo
- **Izquierda:** Planes creados por Agente Maestro
- **Derecha:** Planes creados por Comité
- Permite comparar enfoques y seleccionar el mejor

### Acceder a la Vista Comparativa

**Requisito:** Debes estar en **Vista por Portafolio** con filtros seleccionados

1. **Click en "Vista comparativa"** en la toolbar superior derecha
2. **La pantalla se dividirá** en dos paneles
3. **Cada panel tiene scroll independiente**
4. **Solo muestra columnas:** Tipo y Descripción

### Diseño de la Vista Comparativa

```
┌──────────────────────────────────────────────────────────┐
│  Instrumento: [...]  Portafolio: [...]  [Vista normal]    │
├─────────────────────────┬────────────────────────────────┤
│   🤖 Agente Maestro    │    🤝 Comité                   │
├─────────────────────────┼────────────────────────────────┤
│ Tipo │ Descripción      │ Tipo │ Descripción             │
├──────┼──────────────────┼──────┼─────────────────────────┤
│ Hito │ Implementar...   │ Hito │ Establecer marco...     │
│ Activ│ Capacitar equipo │ Activ│ Entrenar personal...    │
│ Hito │ Publicar datos...│ Hito │ Crear plataforma...     │
│  ...scroll...           │  ...scroll...                  │
└─────────────────────────┴────────────────────────────────┘
```

### Características de la comparación

**Encabezados identificados:**
- Panel izquierdo: Fondo azul "Agente Maestro"
- Panel derecho: Fondo azul "Comité"

**Scroll independiente:**
- Cada tabla tiene su propia barra de desplazamiento
- Altura máxima: 65% de la pantalla
- Puedes revisar cada lista a tu ritmo

**Ordenamiento:**
- Ambas tablas ordenadas por ID (orden de creación)
- Mantiene la secuencia lógica de hitos y actividades

### Cómo usar la Vista Comparativa

**Para analizar diferencias:**

1. **Revisa el panel izquierdo** (Agente Maestro)
   - Enfoque más automatizado y estructurado
   - Generación rápida basada en GPT-4
   
2. **Revisa el panel derecho** (Comité)
   - Análisis más detallado y debatido
   - Refinamiento desde múltiples perspectivas

3. **Compara las descripciones:**
   - ¿Qué enfoque es más completo?
   - ¿Cuál se adapta mejor a tu contexto?
   - ¿Qué detalles aporta cada uno?

4. **Identifica el mejor enfoque:**
   - Puedes usar elementos de ambos
   - Edita manualmente para combinar lo mejor de cada uno

**Para volver a vista normal:**

1. **Click en "Vista normal"** en la toolbar
2. **La tabla vuelve** al formato tradicional con todas las columnas
3. **Puedes editar** los planes normalmente

### Casos de uso típicos

**Validación de regeneración:**
- Regeneraste con Agente Maestro
- Luego refinaste con Comité
- Comparas ambos resultados antes de decidir cuál mantener

**Análisis de enfoques:**
- Quieres ver cómo aborda cada sistema el mismo plan
- Identificas fortalezas de cada enfoque
- Combinas lo mejor de ambos editando manualmente

**Revisión de calidad:**
- Verificas que el Comité aportó valor adicional
- Comparas nivel de detalle
- Decides si el refinamiento valió la pena

---

## ⚙️ Configuración

### Acceder a la configuración

1. **Haz clic en el botón ⚙️** "Configuración" en la barra superior
2. **Se abrirá el panel de configuración**

### Opciones disponibles

#### General

| Opción | Descripción | Valores | Por defecto |
|--------|-------------|---------|-------------|
| **Filas por página** | Cuántos planes mostrar por página | 10, 25, 50, 100 | 25 |
| **Auto-guardar** | Guardar automáticamente al editar | Sí / No | Sí |
| **Confirmar eliminaciones** | Pedir confirmación antes de borrar | Sí / No | Sí |
| **Tema visual** | Color de la interfaz | Claro / Oscuro | Claro |

#### Regeneración con IA

| Opción | Descripción | Valores | Por defecto |
|--------|-------------|---------|-------------|
| **Temperatura GPT** | Creatividad de la IA (0-1) | 0.0 - 1.0 | 0.3 |
| **Modelo** | Versión de GPT a usar | GPT-4, GPT-4o | GPT-4o |
| **Timeout** | Tiempo máximo de espera | 60-600 seg | 300 seg |
| **Auto-aplicar cambios** | Aplicar sin confirmación | Sí / No | No |

#### Importación/Exportación

| Opción | Descripción | Valores | Por defecto |
|--------|-------------|---------|-------------|
| **Modo de importación** | Comportamiento por defecto | Reemplazar / Agregar | Agregar |
| **Incluir metadatos** | Exportar con info adicional | Sí / No | Sí |
| **Formato de fecha** | En nombres de archivo | DD-MM-YYYY / YYYY-MM-DD | YYYY-MM-DD |

### Guardar configuración

1. **Ajusta las opciones** según tus preferencias
2. **Haz clic en "Guardar configuración"** en la parte inferior
3. **Recibirás confirmación:** "✅ Configuración guardada"
4. **Los cambios se aplican inmediatamente**

### Restaurar valores por defecto

1. **En el panel de configuración**, busca el botón "Restaurar por defecto"
2. **Haz clic**
3. **Confirma:** "¿Restaurar todas las opciones a valores por defecto?"
4. **Haz clic en "Sí"**
5. **Todas las opciones vuelven** a su estado original

---

## 📝 Gestión de Prompts (Nuevo en v2.1)

### ¿Qué son los Prompts?

El **SuperPrompt** es el conjunto de instrucciones que guía al Agente Maestro (GPT-4) para generar planes de transformación digital. Es como el "manual de instrucciones" de la IA.

### Acceder a la Gestión de Prompts

1. **Desde cualquier vista**, haz clic en **"📝 Gestión de Prompts"** (al lado de "Exportar Portafolio")
2. Verás la interfaz de edición del SuperPrompt

### Interfaz de Gestión

```
┌─────────────────────────────────────────────────────────────────┐
│  📝 Gestión del SuperPrompt - Agente Maestro PTD                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Ver Versiones]  [Volver al Editor]                           │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                                                           │ │
│  │  [Editor de texto grande - 500px de alto]                │ │
│  │  Contenido del SuperPrompt con fuente monoespaciada      │ │
│  │                                                           │ │
│  └───────────────────────────────────────────────────────────┘ │
│                                         98,450 caracteres      │
│                                                                 │
│  Etiqueta de versión: [Opcional - auto-incrementa]            │
│  Notas: [Describe los cambios realizados]                     │
│                                                                 │
│  [Guardar Nueva Versión]                                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Editar el SuperPrompt

1. **Modifica el texto** directamente en el editor
2. **Agrega una etiqueta** (opcional): "v2.0", "Mejora actividades", etc.
3. **Escribe notas** explicando qué cambiaste: "Aumenté límite de actividades de 10 a 15"
4. **Haz clic en "Guardar Nueva Versión"**
5. **Verás confirmación:** "✅ Versión guardada correctamente"

**Importante:** Los cambios se aplican inmediatamente al Agente Maestro. La próxima regeneración usará el prompt actualizado.

### Ver Historial de Versiones

1. **Haz clic en "Ver Versiones"**
2. **Verás una tabla** con todas las versiones guardadas:
   - ✅ **ACTIVA**: La versión actual en uso
   - **Fecha de creación**
   - **Etiqueta** personalizada
   - **Notas** de cambios
   - **Caracteres** totales

3. **Acciones disponibles:**
   - 👁️ **Ver**: Preview del contenido completo
   - ⏮️ **Restaurar**: Volver a esta versión

### Restaurar Versión Anterior

**⚠️ Advertencia:** Restaurar eliminará todas las versiones posteriores.

1. **En el modal de versiones**, identifica la versión deseada
2. **Haz clic en "⏮️ Restaurar"**
3. **Lee la advertencia:** "Se eliminarán todas las versiones posteriores a esta"
4. **Confirma** haciendo clic en "Aceptar"
5. **La página se recarga** con la versión restaurada como activa

### Casos de Uso

#### Caso 1: Aumentar detalle de planes
```
Problema: Los planes son muy cortos
Solución: 
1. Edita el prompt
2. Cambia "10-15 actividades" por "15-20 actividades"
3. Guarda con etiqueta "v2.1 - Más detalle"
4. Regenera planes afectados
```

#### Caso 2: Cambiar estilo de redacción
```
Problema: Lenguaje muy técnico
Solución:
1. Agrega al prompt: "Usa lenguaje simple y directo"
2. Guarda con nota: "Simplificar redacción"
3. Prueba regenerando 1-2 planes
4. Si no funciona, restaura versión anterior
```

#### Caso 3: Corregir error en reglas
```
Problema: IA ignora una regla específica
Solución:
1. Busca la sección de reglas en el prompt
2. Reformula la regla con mayor énfasis
3. Guarda y prueba
4. Si falla, restaura y prueba otra formulación
```

### Ventajas del Sistema de Versionado

✅ **Sin archivos `.md`:** Todo desde la interfaz web  
✅ **Historial completo:** Nunca pierdes una versión funcional  
✅ **Rollback rápido:** Vuelve atrás si algo sale mal  
✅ **Trazabilidad:** Sabes qué prompt generó cada plan  
✅ **Cambios inmediatos:** No necesitas reiniciar scripts  

### Preguntas Frecuentes - Prompts

**¿Qué pasa si edito mal el prompt?**  
Puedes restaurar la versión anterior desde el historial.

**¿Los scripts necesitan reiniciarse?**  
No, cada regeneración carga la versión activa automáticamente.

**¿Cuántas versiones puedo guardar?**  
Ilimitadas, pero se recomienda mantener solo las relevantes.

**¿Puedo exportar una versión?**  
Actualmente no, pero puedes copiar el texto desde el preview.

**¿Qué pasa si hay error de conexión a BD?**  
Los scripts usan el archivo `SuperPrompt_AgenteMaestro_PTD.md` como fallback.

---

## ❓ Preguntas Frecuentes

### ¿Cuántos planes puedo tener?

No hay límite técnico, pero se recomienda mantener entre 50-200 planes por dimensión para mejor rendimiento.

### ¿La regeneración con IA reemplaza mi trabajo?

No, la IA es una **herramienta de apoyo**. Siempre debes revisar y validar los planes generados con tu conocimiento experto.

### ¿Puedo deshacer una regeneración?

Si exportaste antes de regenerar, puedes importar el respaldo. De lo contrario, **no hay función de deshacer**.

### ¿Qué diferencia hay entre Agente Maestro y Comité?

- **Agente Maestro**: Rápido, para muchos planes a la vez
- **Comité**: Detallado, para un plan específico con análisis profundo

### ¿Los datos están seguros?

Sí, todos los datos se guardan en una base de datos PostgreSQL con respaldos automáticos. Consulta con tu administrador sobre políticas de respaldo.

### ¿Puedo usar la aplicación sin conexión a internet?

No, la aplicación requiere conexión para:
- Acceder a la base de datos
- Usar los servicios de IA (GPT-4)
- Sincronizar cambios

### ¿Cuánto tarda la regeneración con IA?

- **Agente Maestro** (subdimensión): 2-5 minutos
- **Agente Maestro** (dimensión completa): 10-20 minutos
- **Comité** (un plan): 5-8 minutos

### ¿Puedo cancelar una regeneración en progreso?

Sí, haz clic en el botón "❌ Cancelar" en la ventana de progreso. Los cambios parciales **no se guardarán**.

### ¿Qué hago si la tabla no carga?

1. Refresca la página (F5)
2. Limpia caché del navegador
3. Verifica tu conexión a internet
4. Contacta al administrador si persiste

### ¿Puedo exportar a Excel?

Sí, exporta en formato CSV y ábrelo con Excel, Google Sheets u otra herramienta de hojas de cálculo.

---

## 🔧 Solución de Problemas

### Problema: No puedo editar un elemento del portafolio

**Posibles causas:**
- No tienes permisos de edición
- El plan está siendo editado por otro usuario
- Hay un error de conexión

**Soluciones:**
1. Verifica que tienes permisos con tu administrador
2. Espera unos minutos y vuelve a intentar
3. Refresca la página (F5)
4. Revisa tu conexión a internet

---

### Problema: La regeneración con IA no funciona

**Síntomas:**
- El botón 🤖 no responde
- Aparece mensaje "Error al iniciar regeneración"
- La barra de progreso se queda en 0%

**Soluciones:**
1. **Verifica que seleccionaste un plan:**
   - Para Agente Maestro: estar en la pestaña correcta
   - Para Comité: seleccionar un plan específico

2. **Revisa la conexión:**
   - Abre las Herramientas de Desarrollador (F12)
   - Ve a la pestaña "Console"
   - Busca errores en rojo

3. **Espera y reintenta:**
   - La API de OpenAI puede estar ocupada
   - Espera 1-2 minutos
   - Intenta de nuevo

4. **Contacta al administrador si:**
   - El error persiste después de 3 intentos
   - Ves mensaje "API Key inválida"
   - Otros usuarios reportan el mismo problema

---

### Problema: La importación falla

**Mensajes de error comunes:**

#### "Formato de archivo inválido"
**Causa:** El archivo JSON no tiene la estructura correcta

**Solución:**
1. Abre el archivo en un editor de texto
2. Verifica que tenga la estructura mostrada en la sección "Formato de importación"
3. Valida el JSON en https://jsonlint.com
4. Corrige errores de sintaxis

#### "Subdimensión no encontrada"
**Causa:** El nombre de la subdimensión no coincide con las existentes

**Solución:**
1. Revisa los nombres exactos de subdimensiones en la aplicación
2. Copia y pega el nombre exacto (incluyendo mayúsculas/minúsculas)
3. Verifica que no haya espacios extra

#### "Nivel de madurez inválido"
**Causa:** El nivel especificado no es uno de los valores permitidos

**Solución:**
Usa exactamente uno de estos valores:
- "Inicial"
- "Gestionado"
- "Definido"
- "Cuantitativo"
- "Optimizado"

---

### Problema: La tabla está vacía

**Posibles causas:**
- Filtros activos
- Error de carga de datos
- Base de datos vacía

**Soluciones:**

1. **Limpia los filtros:**
   - Busca el botón "Limpiar filtros"
   - Haz clic
   - La tabla debería mostrar todos los datos

2. **Recarga la página:**
   - Presiona F5 o Ctrl+R
   - Espera unos segundos

3. **Verifica la dimensión:**
   - Asegúrate de estar en la pestaña correcta
   - Cambia entre pestañas

4. **Importa datos:**
   - Si es una instalación nueva, importa datos iniciales
   - Usa el botón 📥 "Importar"

---

### Problema: Cambios no se guardan

**Síntomas:**
- Editas un plan pero los cambios desaparecen
- Mensaje "Error al guardar"
- Formulario se cierra sin guardar

**Soluciones:**

1. **Verifica todos los campos:**
   - Asegúrate de llenar todos los campos requeridos (marcados con *)
   - No dejes campos vacíos

2. **Revisa la conexión:**
   - Abre las Herramientas de Desarrollador (F12)
   - Ve a "Network"
   - Busca peticiones en rojo (error)

3. **Intenta de nuevo:**
   - Refresca la página
   - Vuelve a editar
   - Guarda inmediatamente

4. **Copia el texto:**
   - Antes de guardar, copia el contenido de los campos
   - Si falla, tendrás el texto guardado
   - Refresca e intenta pegar de nuevo

---

### Problema: Rendimiento lento

**Síntomas:**
- La aplicación tarda mucho en cargar
- La tabla se congela
- Los botones no responden rápidamente

**Soluciones:**

1. **Reduce filas por página:**
   - Ve a Configuración ⚙️
   - Cambia "Filas por página" a 10 o 25
   - Guarda

2. **Limpia caché del navegador:**
   - Chrome: Ctrl+Shift+Delete → Borrar caché
   - Firefox: Ctrl+Shift+Delete → Caché
   - Edge: Ctrl+Shift+Delete → Datos en caché

3. **Cierra pestañas innecesarias:**
   - Deja solo la aplicación abierta
   - Cierra otros programas pesados

4. **Actualiza tu navegador:**
   - Asegúrate de tener la última versión
   - Chrome, Firefox y Edge se actualizan automáticamente

5. **Consulta al administrador:**
   - Si tienes muchos planes (500+), puede necesitarse optimización
   - El servidor puede estar sobrecargado

---

### Problema: Modal de regeneración se cierra solo

**Síntomas:**
- Inicias regeneración y la ventana desaparece
- No ves la barra de progreso
- No sabes si está funcionando

**Soluciones:**

1. **No cambies de pestaña:**
   - Mantén la pestaña de la aplicación activa
   - No minimices el navegador

2. **Verifica en segundo plano:**
   - Abre Herramientas de Desarrollador (F12)
   - Ve a "Console"
   - Busca mensajes de progreso

3. **Espera y recarga:**
   - Espera 5 minutos
   - Recarga la página
   - Verifica si los datos cambiaron

---

### Problema: Errores de permisos

**Mensaje:** "No tienes permisos para esta acción"

**Soluciones:**

1. **Verifica tu rol:**
   - Contacta al administrador
   - Pregunta qué permisos tienes asignados

2. **Roles típicos:**
   - **Visor**: Solo puede ver, no editar
   - **Editor**: Puede ver y editar
   - **Administrador**: Puede hacer todo

3. **Solicita permisos:**
   - Explica qué necesitas hacer
   - El administrador puede actualizar tus permisos

---

## 📞 Contacto y Soporte

### ¿Necesitas ayuda adicional?

**Soporte Técnico:**
- 📧 Email: soporte@tuinstitucion.gob
- 📞 Teléfono: +123 456 7890
- 💬 Chat: disponible en horario laboral

**Horario de atención:**
- Lunes a Viernes: 8:00 AM - 6:00 PM
- Sábados: 9:00 AM - 1:00 PM
- Domingos: Cerrado

**Documentación adicional:**
- 📚 Wiki interna: https://wiki.tuinstitucion/Plataforma-SGD
- 🎥 Videos tutoriales: https://videos.tuinstitucion/Plataforma-SGD
- 📖 Manual técnico: [Contacta al administrador]

---

## 🎓 Recursos de Aprendizaje

### Videos tutoriales disponibles

1. **Introducción rápida** (5 min) - Panorama general de la aplicación
2. **Editar portafolio** (8 min) - Cómo crear, editar y eliminar elementos del portafolio
3. **Regeneración con IA** (12 min) - Usar Agente Maestro y Comité
4. **Importar/Exportar** (7 min) - Gestión de datos masivos
5. **Configuración avanzada** (10 min) - Personalizar la aplicación

### Glosario de términos

| Término | Definición |
|---------|------------|
| **Dimensión** | Área principal de transformación (Gobernanza, Calidad Web, Procedimiento) |
| **Subdimensión** | Subcategoría específica dentro de una dimensión |
| **Instrumento** | Herramienta, política o documento del plan |
| **Nivel de Madurez** | Estado de evolución de la implementación (Inicial a Optimizado) |
| **Hito** | Objetivo o meta a alcanzar |
| **Actividad** | Tarea concreta para lograr el hito |
| **Agente Maestro** | Sistema de IA que regenera subdimensiones completas |
| **Comité** | Sistema de múltiples agentes IA que refinan planes específicos |
| **PTD** | Plan de Transformación Digital |

---

## 📋 Flujos de Trabajo Recomendados

### Flujo 1: Actualización trimestral de planes

```
1. Exportar datos actuales (respaldo) 💾
   ↓
2. Revisar planes obsoletos o desactualizados 📝
   ↓
3. Usar Agente Maestro para regenerar subdimensiones 🤖
   ↓
4. Revisar cambios sugeridos 🔍
   ↓
5. Ajustar manualmente según contexto ✏️
   ↓
6. Exportar nueva versión (respaldo) 💾
```

**Tiempo estimado:** 2-3 horas por dimensión

---

### Flujo 2: Refinamiento de plan crítico

```
1. Identificar plan estratégico a mejorar 🎯
   ↓
2. Exportar plan actual (respaldo) 💾
   ↓
3. Usar Comité para refinamiento detallado 🤝
   ↓
4. Revisar aportes de cada agente 📊
   ↓
5. Comparar versión original vs. refinada 🔍
   ↓
6. Aceptar o editar antes de aplicar ✅
   ↓
7. Guardar versión final 💾
```

**Tiempo estimado:** 30-45 minutos por plan

---

### Flujo 3: Migración de datos desde Excel

```
1. Organizar datos en Excel 📊
   ↓
2. Convertir a formato JSON (usar herramienta online) 🔄
   ↓
3. Validar JSON en jsonlint.com ✅
   ↓
4. Exportar datos actuales de la app (respaldo) 💾
   ↓
5. Importar JSON a la aplicación 📥
   ↓
6. Verificar que los datos se cargaron correctamente 🔍
   ↓
7. Ajustar cualquier error manualmente ✏️
```

**Tiempo estimado:** 1-2 horas para 100+ planes

---

## 🏆 Mejores Prácticas

### ✅ Haz esto:

1. **Exporta respaldos regularmente**
   - Semanalmente para uso activo
   - Antes de regeneraciones masivas
   - Antes de importaciones

2. **Revisa cambios de IA**
   - Nunca aceptes regeneraciones sin revisar
   - Valida con tu conocimiento experto
   - Ajusta según contexto institucional

3. **Usa nombres descriptivos**
   - Instrumentos claros y específicos
   - Hitos medibles y alcanzables
   - Actividades concretas y accionables

4. **Mantén consistencia**
   - Usa terminología estándar
   - Niveles de madurez coherentes
   - Formato uniforme en descripciones

5. **Documenta cambios importantes**
   - Anota por qué regeneraste
   - Registra decisiones tomadas
   - Comparte con el equipo

### ❌ Evita esto:

1. **No edites durante regeneración**
   - Espera a que termine el proceso
   - Evita conflictos de datos

2. **No regeneres sin propósito**
   - La IA no siempre mejora el contenido
   - Usa cuando realmente necesites actualizar

3. **No ignores errores**
   - Reporta problemas al administrador
   - No trabajes con datos corruptos

4. **No compartas credenciales**
   - Cada usuario debe tener su cuenta
   - Trazabilidad de cambios

5. **No trabajes sin respaldos**
   - Siempre ten una copia de seguridad reciente
   - Los errores pueden ocurrir

---

## 📈 Consejos para Usuarios Avanzados

### Uso eficiente de filtros

Combina múltiples filtros para búsquedas complejas:
- Filtra por subdimensión + nivel de madurez
- Busca términos específicos en hitos
- Ordena por múltiples columnas

### Atajos de teclado (si están disponibles)

| Atajo | Acción |
|-------|--------|
| Ctrl + S | Guardar edición actual |
| Ctrl + E | Abrir editor del plan seleccionado |
| Ctrl + F | Buscar en tabla |
| Ctrl + R | Recargar datos |
| Esc | Cerrar modal/cancelar acción |

### Personalización de vistas

Ajusta las columnas visibles según tu necesidad:
1. Clic derecho en encabezado de tabla
2. Selecciona "Personalizar columnas"
3. Marca/desmarca columnas
4. Guarda tu configuración

---

## 🔒 Seguridad y Privacidad

### Protección de datos

- Todos los datos se transmiten encriptados (HTTPS)
- Contraseñas hasheadas en la base de datos
- Respaldos automáticos cada 24 horas
- Acceso controlado por roles y permisos

### Buenas prácticas de seguridad

1. **Usa contraseñas fuertes**
   - Mínimo 8 caracteres
   - Combina letras, números y símbolos
   - No reutilices contraseñas

2. **Cierra sesión al terminar**
   - Especialmente en computadoras compartidas
   - Usa "Cerrar sesión" no solo cerrar pestaña

3. **No compartas tu cuenta**
   - Cada usuario debe tener credenciales propias
   - Reporta accesos no autorizados

4. **Verifica la URL**
   - Asegúrate de estar en el dominio correcto
   - Busca el candado 🔒 en la barra de direcciones

---

## 📝 Actualizaciones del Manual

**Versión:** 2.0  
**Fecha:** 12 de Noviembre de 2025  
**Última actualización:** 12 de Noviembre de 2025

### Historial de cambios

- **v2.0** (12 Nov 2025) - Actualización completa de interfaz:
  - Sistema de filtros unificado (un solo botón "Cambiar")
   - Vista por Portafolio como modo predeterminado
  - Vista Comparativa Agente Maestro vs Comité
   - Botón + para agregar filas (solo en Vista por Portafolio)
  - Filtros específicos por dimensión (Instrumento, Nivel de Madurez)
  - Eliminación de selectores redundantes en toolbar
  - Búsqueda y ordenamiento por columnas
  - Comité de Agentes completamente funcional
- **v1.0** (11 Nov 2025) - Manual inicial completo

---

## ✨ ¡Comienza a usar la aplicación!

Ahora que has leído este manual, estás listo para:

✅ Navegar por la aplicación con confianza  
✅ Usar Vista por Portafolio y Vista Total efectivamente  
✅ Gestionar planes de transformación digital  
✅ Aprovechar ambos sistemas de IA (Agente Maestro y Comité)  
✅ Comparar resultados con Vista Comparativa  
✅ Filtrar y buscar información específica  
✅ Agregar y editar planes eficientemente  
✅ Solucionar problemas comunes  

**¡Éxito en tu trabajo de transformación digital!** 🚀