# Changelog

## 2026-10-20
- Added input and output token counts to the LLM ask command's usage output.

## 2026-11-26
- Se agregaron los servidores MCP `fetch` (mcp-server-fetch==2026.11.11) y `aws` (URL remota) a `app/mcp_servers.json` y se completó la sección de ejercicios de `lectures/06/answer.md` (pasos 1 a 4).
- Se creó la rama `lec06` a partir de `lec05` y se completó la tarea avanzada de la Lección 06 en `lectures/06/answer.md`: comparación de la configuración de servidores MCP de Gemini CLI (documentación oficial, consultada el 2026-11-26) con `app/mcp_servers.json`.

## 2026-11-16
- Se agregó `search_graph_ranked` (app/retrieval.py), la herramienta del mismo nombre (app/tools.py) y la opción `--graph-ranked` (app/agent.py) para la tarea avanzada de la Lección 05: expansión del grafo ordenada por similitud con la consulta y un salto opcional por términos relacionados.
- Se agregó `scripts/eval_retrieval.py` para comparar qué páginas de evidencia devuelve cada método de recuperación sin generar respuestas.
- Se completó la sección de ejercicios de `lectures/05/answer.md` (contexto completo, búsqueda vectorial, Tree y Graph sobre la misma pregunta).
- Se completó la sección de tarea de `lectures/05/answer.md` (nivel avanzado) con los resultados de 54 ejecuciones.
- Se incorporó a `lec05` la rama principal del curso con los datos de búsqueda en inglés y los materiales de la Lección 06, sin conflictos, y se repitió la prueba de recuperación (`scripts/eval_retrieval.py`) con resultados idénticos a los de los datos en japonés.
- Se incorporaron a `lec05` los cambios de Lección 05 del repositorio del curso (instrucciones y código de recuperación) y se resolvieron conflictos en `app/agent.py`, `app/tools.py` y `.gitignore`.
