# AI Engineering Course

Curso práctico de **Ingeniería de Inteligencia Artificial (AI Engineering)**. Este repositorio incluye notebooks por módulos, código reutilizable y aplicaciones listas para ejecutar (RAG, agentes, despliegue, etc.).

Funciona en **Linux**, **macOS** y **Windows**.

**Versión de Python del proyecto:** `3.11.15`

---

## Requisitos previos

| Herramienta | Versión | Descripción |
|-------------|---------|-------------|
| **Python** | **3.11.15** | Versión usada y probada en este curso |
| **Git** | Cualquier versión reciente | Clonar el repositorio |
| **Ollama** | Última estable | LLMs y embeddings en local |
| **RAM** | 8 GB+ (16 GB recomendado) | Para modelos locales |

Opcional: **JupyterLab** (incluido en `requirements.txt`) para los notebooks.

---

## Instalación rápida

### 1. Clonar el repositorio

```bash
git clone https://github.com/ederleon-GL/AI-course.git
cd AI-course
```

### 2. Instalar Python 3.11.15

Comprueba si ya lo tienes:

```bash
python3.11 --version
# Debe mostrar: Python 3.11.15
```

Si no está instalado:

| Sistema | Instalación |
|---------|-------------|
| **macOS** | `brew install python@3.11` |
| **Linux (Debian/Ubuntu)** | `sudo apt install python3.11 python3.11-venv python3.11-pip` |
| **Windows** | Descarga el instalador desde [python.org/downloads](https://www.python.org/downloads/release/python-31115/) y marca **Add Python to PATH** |

> Usa siempre `python3.11` (o `py -3.11` en Windows) para crear el entorno. Otras versiones (3.9, 3.10, 3.12) pueden causar incompatibilidades con `requirements.txt`.

### 3. Crear entorno virtual

#### macOS / Linux

```bash
python3.11 -m venv venv
source venv/bin/activate
python --version          # Python 3.11.15
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Windows (PowerShell)

```powershell
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
python --version          # Python 3.11.15
python -m pip install --upgrade pip
pip install -r requirements.txt
```

#### Windows (CMD)

```cmd
py -3.11 -m venv venv
venv\Scripts\activate.bat
python --version
python -m pip install --upgrade pip
pip install -r requirements.txt
```
### 3.5. Testear Instalacion
Utilizar el archivo scripts\test.py
> **Nota Windows:** Si PowerShell bloquea la activación del entorno, ejecuta una vez:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

### 4. Instalar Ollama

Descarga e instala Ollama desde [https://ollama.com/download](https://ollama.com/download).

| Sistema | Método |
|---------|--------|
| **macOS** | Instalador `.dmg` o `brew install ollama` |
| **Linux** | `curl -fsSL https://ollama.com/install.sh \| sh` |
| **Windows** | Instalador `.exe` desde la web oficial |

Verifica la instalación:

```bash
ollama --version
```

### 5. Descargar modelos necesarios

Con Ollama en ejecución, descarga el modelo de embeddings y al menos un LLM:

```bash
ollama pull nomic-embed-text
ollama pull qwen2.5:1.5b
```

Modelos LLM alternativos disponibles en la app:

- `qwen2.5:1.5b` (ligero, recomendado para empezar)
- `llama3.2:1b`
- `llama3.2:3b`
- `llama3.2:latest`

### 6. Iniciar el servidor Ollama

Ollama suele arrancar automáticamente al instalarlo. Si no está activo:

```bash
ollama serve
```

En otra terminal (con el entorno virtual activado) comprueba que responde:

```bash
ollama list
```

---

## Ejecutar la aplicación RAG (Streamlit)

Desde la **raíz del proyecto** (`AI-course/`), con el entorno virtual activado:

```bash
streamlit run apps/rag_app/app.py
```

Se abrirá el navegador en `http://localhost:8501`.

### Uso de la app

1. **Panel lateral (⚙️ Configuración):** elige el modelo LLM, número de chunks (`k`), temperatura y si quieres ver las fuentes.
2. **Chat:** escribe preguntas sobre los papers de ML/IA indexados.
3. **Ver fragmentos recuperados:** tras cada respuesta, expande el panel para ver el texto extraído de ChromaDB.
4. Si cerraste el menú lateral, pulsa el botón `>>` en la esquina superior izquierda para volver a abrirlo.

### Primera ejecución

La app descarga automáticamente 5 papers de arXiv y crea el índice vectorial en `data/vector_db/`. La primera carga puede tardar varios minutos según tu conexión y hardware.

---

## Ejecutar los notebooks (Jupyter)

Con el entorno virtual activado, desde la raíz del proyecto:

```bash
jupyter lab
```

O con Jupyter Notebook clásico:

```bash
jupyter notebook
```

Los notebooks están organizados por módulos en `notebooks/`:

| Módulo | Carpeta | Contenido |
|--------|---------|-----------|
| 01 | `01_introduction/` | Introducción a IA, ML y LangChain |
| 02 | `02_llms/` | Transformers y prompting |
| 03 | `03_embeddings/` | Embeddings y bases vectoriales |
| 04 | `04_rag/` | RAG básico con ChromaDB |
| 05 | `05_agents/` | Agentes (en desarrollo) |
| 06 | `06_mcp/` | Model Context Protocol (en desarrollo) |
| 07 | `07_deployment/` | FastAPI, Streamlit, Docker (en desarrollo) |
| 08 | `08_monitoring/` | LangSmith y evaluación (en desarrollo) |
| 09 | `09_security/` | Seguridad y IA responsable (en desarrollo) |

> Algunos notebooks usan comandos mágicos de Jupyter (`%pip`, `!ollama`). Ejecútalos celda a celda dentro de Jupyter, no como scripts `.py` directos.

---

## Estructura del proyecto

```
AI-course/
├── apps/
│   └── rag_app/          # App Streamlit RAG
├── data/
│   ├── Papers/           # PDFs descargados (arXiv)
│   └── vector_db/        # Índice ChromaDB (generado localmente)
├── docs/                 # Material teórico, labs, syllabus
├── notebooks/            # Cuadernos por módulo
├── outputs/              # Artefactos de salida
├── scripts/              # Utilidades
├── src/                  # Código reutilizable (RAG, agentes, etc.)
├── requirements.txt
└── README.md
```

Las rutas de datos se resuelven automáticamente desde la raíz del repositorio; no necesitas editar rutas absolutas al clonar en otro equipo u sistema operativo.

---

## Configuración opcional (`.env`)

Si usas API keys externas (OpenAI, LangSmith, etc.), crea un archivo `.env` en la raíz del proyecto:

```bash
# macOS / Linux
cp .env .env.local   # o crea .env manualmente

# Windows (PowerShell)
Copy-Item .env .env.local
```

Ejemplo de variables (ajusta según necesites):

```env
OPENAI_API_KEY=sk-...
LANGCHAIN_API_KEY=...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=ai-course
```

El archivo `.env` está en `.gitignore` y no debe subirse al repositorio.

---

## Comandos de referencia por sistema operativo

| Acción | macOS / Linux | Windows (PowerShell) |
|--------|---------------|----------------------|
| Verificar Python | `python3.11 --version` | `py -3.11 --version` |
| Crear entorno | `python3.11 -m venv venv` | `py -3.11 -m venv venv` |
| Activar entorno | `source venv/bin/activate` | `.\venv\Scripts\Activate.ps1` |
| Desactivar entorno | `deactivate` | `deactivate` |
| Instalar deps | `pip install -r requirements.txt` | `pip install -r requirements.txt` |
| App RAG | `streamlit run apps/rag_app/app.py` | `streamlit run apps/rag_app/app.py` |
| Jupyter | `jupyter lab` | `jupyter lab` |
| Listar modelos Ollama | `ollama list` | `ollama list` |

---

## Solución de problemas

### Ollama no responde / connection refused

```bash
# Inicia el servidor en una terminal aparte
ollama serve

# Comprueba que el puerto 11434 está activo
curl http://localhost:11434        # macOS / Linux
# Windows PowerShell:
Invoke-WebRequest http://localhost:11434
```

### Error de dimensiones en ChromaDB

El modelo de embeddings (`nomic-embed-text`) no coincide con el índice guardado. Borra el índice y reinicia la app para que se reconstruya:

```bash
# macOS / Linux
rm -rf data/vector_db/*

# Windows (PowerShell)
Remove-Item -Recurse -Force data\vector_db\*
```

### No veo el menú lateral (Configuración)

Pulsa el botón `>>` en la esquina superior izquierda de la ventana del navegador para expandir el sidebar.

### `streamlit` no encontrado

Asegúrate de tener el entorno virtual activado e instala dependencias:

```bash
pip install -r requirements.txt
```

### Notebooks: advertencia de `ipywidgets`

```bash
pip install ipywidgets
jupyter labextension enable --py widgetsnbextension   # si usas Jupyter clásico
```

### Versión de Python incorrecta

El proyecto requiere **Python 3.11.15**. Si `python --version` muestra otra versión, recrea el entorno:

```bash
# macOS / Linux
deactivate
rm -rf venv
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

```powershell
# Windows (PowerShell)
deactivate
Remove-Item -Recurse -Force venv
py -3.11 -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

## Stack tecnológico

- **Python:** 3.11.15
- **LLMs locales:** [Ollama](https://ollama.com) + LangChain
- **RAG:** ChromaDB, PyPDF, LangChain
- **Embeddings:** `nomic-embed-text`
- **Interfaz:** Streamlit
- **Notebooks:** JupyterLab

---

## Licencia y contribuciones

Material educativo del curso AI Engineering. Para dudas o incidencias, abre un issue en el repositorio o consulta con el instructor del curso.

# ai-course
AI-Course by Elder

### TAREA
* Cambiar diccionario por tabla: Hacer notebook igual a tools pero cargar la tabla que esta en data table, ajustar las tools para que hagan la busqueda sobre la tabla en vez del diccionario
* A partir del csv construir una DB.
* Revisar lo siguiente: https://docs.langchain.com/oss/python/integrations/tools/pandas
* Vimos hasta 05_agents/05_pandas_agent_worldcup.ipynb
* Hacer agentes que...
* Hacer algo de la funcion...
* Copiar y pegar todo lo que sacamos de Agus...
