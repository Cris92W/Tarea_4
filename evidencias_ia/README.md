# Evidencias del uso de inteligencia artificial

Modalidad: **Opción B, exportación de las conversaciones** (issue #201). Todo el proyecto se desarrolló con Claude
Code en una sola conversación, exportada por etapas desde el registro que Claude Code guarda de cada sesión. Además
hay registros de las ejecuciones de Claude Code sin interfaz (`claude -p`) que prueban que el MCP, las Skills y el
agente funcionan.

## Qué hay en cada carpeta

| Carpeta | Conversación de desarrollo | Ejecuciones registradas |
|---|---|---|
| [`mcp/`](mcp/) | [`00_conversacion.md`](mcp/00_conversacion.md): lectura del issue, plan, pregunta y servidor MCP | `pruebas.txt` (10 passed) y 5 consultas al MCP desde Claude Code |
| [`skills/`](skills/) | [`00_conversacion.md`](skills/00_conversacion.md): las Skills de la ENAHO, gráficos, mapa y exportación de evidencias | 6 ejecuciones: activación por lenguaje natural, coordinación limpieza → mapa e invocación directa de cada Skill |
| [`integracion/`](integracion/) | [`00_conversacion.md`](integracion/00_conversacion.md): pregunta de investigación, skill de cruce, ejecuciones del agente, verificación y evaluación | `05_ejecucion_agente`: la investigación completa (4 Skills y 3 herramientas MCP en una ejecución); 01 a 03, intentos en los que el agente informó el error sin inventar; 04, prueba con un año sin datos |
| [`evaluacion/`](evaluacion/) | (está en la conversación de `integracion/`) | Las 20 ejecuciones de la evaluación, `<pregunta>_<modo>` |

Cada ejecución tiene dos archivos: `.jsonl`, el registro crudo de `--output-format stream-json` con cada
herramienta y lo que devolvió, y `.md`, el mismo registro legible.

## Qué se omitió y por qué

- **El razonamiento interno del modelo y los mensajes internos de Claude Code.** No son parte de la conversación.
- **Datos personales:** las rutas y el nombre de usuario de la carpeta personal (se reemplazan por `~` y `usuario`)
  y los correos.
- **Las notas de memoria del asistente.** Al inicio leyó notas propias sobre otras tareas del curso; se reemplazan
  por un aviso.
- **Los comentarios de otros estudiantes en el issue.** Tienen nombres de terceros, se reemplazan por un aviso y
  siguen públicos en GitHub.

Cada omisión queda marcada en el texto como `[omitido: …]` u `[oculto]`.
