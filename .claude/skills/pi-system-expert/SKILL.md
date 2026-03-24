---
name: pi-system-expert
description: Deep technical reference for AVEVA/OSIsoft PI System — Data Archive, Asset Framework, PI Vision, PI Web API, industrial protocols (OPC, SCADA, PLC/DCS, Modbus, MQTT), scripting (PowerShell, Python, C#/.NET), cloud deployment, security, and GMP compliance. Use when answering PI System questions, designing architectures, troubleshooting, or writing PI-related code.
trigger: When the user asks about PI System, OSIsoft, AVEVA PI, PI Data Archive, PI AF, PI Vision, PI Web API, OPC, SCADA, PLC, DCS, data historian, PI tags, compression, AF SDK, PIconnect, PI ProcessBook, PI DataLink, industrial protocols, or GMP/21 CFR Part 11 compliance for PI.
---

# PI System Expert — Technical Reference Skill

You are a senior PI System engineer. Use the reference files below for detailed technical knowledge.

## External Knowledge Base (Gemini File Search)

For questions that need deeper or more specific answers than the reference files provide, query the Gemini-powered knowledge base:

```bash
python .claude/skills/pi-system-expert/pi_knowledge.py "your question here"
python .claude/skills/pi-system-expert/pi_knowledge.py --json "your question here"
```

This searches the same AVEVA/OSIsoft document store used by the PiSharp chat system and returns document-backed answers with source citations. Use it for:
- Complex troubleshooting scenarios
- Specific API details or edge cases
- Anything the reference files don't cover in enough depth

## Reference Files

Load the relevant reference file(s) based on the question:

| Topic | Reference File |
|---|---|
| PI Data Archive (architecture, compression, tags, admin, HA, troubleshooting) | `references/pi-data-archive.md` |
| PI Asset Framework (modeling, analytics, event frames, AF SDK) | `references/pi-asset-framework.md` |
| PI Vision, ProcessBook, DataLink, dashboarding | `references/pi-vision-visualization.md` |
| PI Web API (REST, batch, channels, OMF, search) | `references/pi-web-api.md` |
| OPC, SCADA, PLC/DCS, Modbus, MQTT, BACnet, DNP3, GMP | `references/industrial-protocols.md` |
| PowerShell, Python, C#/.NET, SQL, cloud, security | `references/scripting-cloud.md` |

## Quick Reference

### Data Flow Through PI System
```
Field Device → Protocol (OPC/Modbus/MQTT) → PI Interface/Adapter
  → Exception Testing (ExcDev/ExcMax at interface node)
    → PI Buffer Subsystem (PIBufSS)
      → PI Data Archive Snapshot Subsystem
        → Compression Testing (Swinging Door: CompDev/CompMax)
          → Event Queue → Archive Files
```

### Key Ports
- PI Data Archive: TCP 5450
- PI AF Server: TCP 5457
- PI Web API: TCP 443 (HTTPS)
- OPC UA: TCP 4840
- Modbus TCP: TCP 502
- MQTT: TCP 1883 (plain) / 8883 (TLS)
- BACnet/IP: UDP 47808
- EtherNet/IP: TCP 44818

### Compression Settings Baseline
| Parameter | Recommended | Notes |
|---|---|---|
| Compressing | 1 (ON) | Always enable |
| ExcDev | Half of CompDev | Instrument precision |
| ExcMax | 600s (10 min) | Force report interval |
| CompDev | Process-specific | Max acceptable error |
| CompMax | 28800s (8 hr) | Force archive interval |
| CompMin | 0 | Unless high-frequency |

### Technology Selection Guide
| Need | Use |
|---|---|
| Highest performance (.NET/Windows) | AF SDK |
| Cross-platform / web apps | PI Web API |
| Python data science | PIconnect or PI Web API |
| Excel reporting | PI DataLink |
| SQL queries against PI | PI OLEDB Provider/Enterprise |
| Admin automation | PowerShell (OSIsoft.PowerShell) |
| High-volume data ingress | OMF via PI Web API |
| Real-time streaming to web | PI Web API Channels (WebSocket) |
| BI dashboards | PI Integrator → Power BI / Grafana plugin |
