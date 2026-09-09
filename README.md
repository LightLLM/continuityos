# ContinuityOS

**Autonomous production intelligence for film crews.** Built for the Google Cloud Agentic Cinema Hackathon, Grafana Labs track.

ContinuityOS watches production telemetry, investigates continuity and operational anomalies, and gives the crew a clear go/no-go decision before the next shot. The judge-ready **Project Eclipse** flow is: `AT RISK → investigate → HOLD SHOOT → resolve → READY TO SHOOT`.

## Runtime architecture

`Browser → Vercel serverless function → Google ADK / Gemini → Grafana Cloud MCP`

- **Gemini** reasons across continuity, camera, and schedule evidence.
- **Google ADK** defines the production-supervisor agent and its orchestration contract.
- **Grafana Cloud MCP** is contacted at runtime to expose the monitoring tools available to the agent.
- **Vercel** hosts the control room and Python serverless endpoint.

## Demo fallback versus real integrations

The distinction is intentionally visible in both the interface and API response:

| Mode | Trigger | Behavior |
|---|---|---|
| `demo_fallback` | Credentials absent or an integration fails | Uses a deterministic, disclosed Project Eclipse fixture. It never claims a live Grafana/Gemini call. |
| `real_runtime` | `GOOGLE_API_KEY` is present and Gemini succeeds | Runs Gemini through the Google SDK, instantiates the ADK supervisor, and includes Grafana MCP context when configured. |

For a qualifying Grafana-track demonstration, configure the real runtime and confirm the response reports `real_runtime` and `grafana_mcp: connected`.

## Run locally

Serve the repository root with any static server. To exercise the Python endpoint locally, install `requirements.txt` and run it using a compatible serverless emulator. The hosted Vercel build needs no frontend compilation.

## Environment variables

Copy `.env.example` into your private environment and configure:

- `GOOGLE_API_KEY` — Gemini API credential
- `GEMINI_MODEL` — defaults to `gemini-2.5-flash`
- `GRAFANA_MCP_HTTP_URL` — Grafana Cloud MCP HTTP endpoint
- `GRAFANA_MCP_TOKEN` — Grafana access token

Never commit secrets. Without them, the application remains fully usable in clearly labeled demo fallback mode.

## API

- `GET /api/investigate` — health and runtime-mode check
- `POST /api/investigate` — execute the Project Eclipse investigation

## Deploy

Import this repository into Vercel or run `vercel --prod`. Add runtime variables in the Vercel project settings, then redeploy. Verify the mode endpoint before recording the technical demo.

## License

MIT — see [LICENSE](LICENSE).
