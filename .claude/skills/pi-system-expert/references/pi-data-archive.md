# AVEVA PI Data Archive -- Expert Technical Reference

## 1. Architecture

### Data Storage Pipeline

```
Interface Node → Exception Testing → PI Buffer Subsystem → PI Snapshot Subsystem → Compression Testing → Event Queue → Archive Files
```

### Snapshot vs Archive
- **Snapshot**: The Snapshot Subsystem (`pisnapss`) stores the most recent event for each PI point in memory. Every incoming value becomes the new snapshot.
- **Archive**: Values that pass compression testing are written to archive files. The snapshot subsystem applies compression and sends qualifying events to the Event Queue.

### Event Queue
Intermediate disk-based queue between Snapshot and Archive subsystems. Path configurable via `Snapshot_EventQueuePath` tuning parameter. If archive is unavailable (e.g., during shift), events accumulate here.

### Archive Files
- `.arc` extension, stored in `PI\arc` directory by default
- Each contains primary records and overflow records. Every PI point has one primary record per archive file.
- Only one archive is the **primary (active) archive** at any time.
- `Archive_MaxFileSize` and `Archive_AutoArchiveFileSize` control sizing.
- `Archive_AutoArchiveFileRoot` configures path for new archives.

### Compression Algorithms

**Stage 1: Exception Reporting (at interface node)**

| Parameter | Description | Typical |
|---|---|---|
| ExcDev | Minimum change in EU before reporting | Half of CompDev |
| ExcDevPercent | ExcDev as % of Span | - |
| ExcMin | Min seconds between reports | 0 |
| ExcMax | Max seconds between reports | 600 (10 min) |

**Stage 2: Swinging Door Compression (at PI Server)**

1. Maintains a "cone" from last archived value through CompDev band around current snapshot
2. New value inside cone → becomes new snapshot, cone narrows
3. New value outside cone → previous snapshot is archived, new value starts new cone
4. Result: piecewise-linear reconstruction with max error = CompDev

| Parameter | Description | Typical |
|---|---|---|
| CompDev | Max deviation in EU | Process-specific |
| CompDevPercent | CompDev as % of Span | - |
| CompMin | Min seconds between archives | 0 |
| CompMax | Max seconds between archives | 28800 (8 hr) |
| Compressing | 0=off, 1=on | 1 |

**Guideline**: Set ExcDev to half of CompDev.

### Core Subsystems
- **pibasess** -- Base: point database, security, configuration
- **pisnapss** -- Snapshot: current values and compression
- **piarchss** -- Archive: archive files and data retrieval
- **piupdmgr** -- Update Manager: data update notifications
- **pibufss** -- Buffer: buffering on interface nodes

---

## 2. Administration

### Directory Structure
- `PI\adm` (admin tools), `PI\arc` (archives), `PI\bin` (binaries), `PI\dat` (databases, event queue), `PI\log` (logs)

### Key Tuning Parameters

| Parameter | Description |
|---|---|
| `Archive_MaxFileSize` | Maximum archive file size |
| `Archive_AutoArchiveFileSize` | Size of auto-created archives |
| `Archive_AutoArchiveFileRoot` | Path for new archives |
| `Archive_OverwriteDataOnAutoShiftFailure` | 0=stop, 1=overwrite oldest |
| `Snapshot_EventQueuePath` | Path for event queue files |
| `ArcMaxCollect` | Max events returned per archive call |
| `Archive_MaxQueryExecutionSec` | Timeout for archive queries |

### Backup
- Use `piartool -backup` or `pibackup.bat` via Windows Task Scheduler
- Back up: archive files, snapshot, event queue, point database, security databases
- Best practice: daily automated backups to separate location

### High Availability -- PI Collective

- **Primary member**: Receives all writes, replicates config to secondaries
- **Secondary members**: Read-only replicas
- **Key insight**: Collectives do NOT sync data between members. PIBufSS on each interface node fans out (n-way) data to ALL members simultaneously.
- **Upgrade order**: Secondaries first, then primary
- **PI Collective Manager**: Tool for creating/configuring/monitoring collectives

### Buffering (PIBufSS)

```ini
[PIBUFSS]
QUEUEPATH=D:\PI\Buffers
QUEUESIZE=512  ; MB (default 32, range 8-131072)
```

- N-way buffering for collectives
- Stores events locally when PI Server unreachable
- On reconnect, drains buffer queue

### Security Model

- **PI Identities**: Named security principals. Permissions via ACLs.
- **PI Mappings** (recommended): Associate Windows users/groups to PI Identities via SSPI.
- **PI Trusts** (legacy): Identify by IP/hostname/process. Less secure.
- **PIWorld**: Default identity for all connecting users. Restrict in production.
- **piadmin**: Full administrative access.

---

## 3. PI Tags (PI Points)

### Point Types

| Type | Description |
|---|---|
| Float16 | 16-bit float (smallest storage) |
| Float32 | 32-bit float (most common) |
| Float64 | 64-bit double |
| Int16/Int32 | Integer types |
| Digital | Enumerated state from digital state set |
| String | Up to 976 characters in archive |
| Blob | Binary large object |
| Timestamp | Date/time value |

### Key Point Attributes

**Identification:** Tag, PointID, PointSource, PointType, PointClass
**Range:** Zero, Span, TypicalValue
**Exception:** ExcDev, ExcDevPercent, ExcMin, ExcMax
**Compression:** CompDev, CompDevPercent, CompMin, CompMax, Compressing
**Other:** Descriptor, EngUnits, Shutdown, DigitalSet, Scan, Location1-5, InstrumentTag, SourceTag, Step (0=linear interp, 1=step), Future

### Tag Creation via piconfig
```
@table pipoint
@mode create
@istr tag,pointtype,pointsource,zero,span,compdev,excdev,compmax,excmax,compressing,descriptor,engunits
TAG001,Float32,OPC1,0,100,0.5,0.25,28800,600,1,Reactor Temperature,degC
```

### Digital States
System states: `Shutdown`, `Bad Input`, `Pt Created`, `No Data`, `Scan Off`, `I/O Timeout`, `Over Range`, `Under Range`, `Calc Failed`, `Configure`, `Bad`

---

## 4. Data Access Technologies

### AF SDK (.NET) -- Highest Performance
```csharp
PIPoint.FindPIPoint(server, "tagname")
piPoint.RecordedValues(timeRange, boundaryType, filter, includeFiltered, maxCount)
piPoint.InterpolatedValues(timeRange, interval, filter, includeFiltered)
piPoint.PlotValues(timeRange, intervals)  // optimized for charting
piPoint.Summary(timeRange, summaryType, calculationBasis, timeType)
piPoint.CurrentValue()
piPoint.UpdateValues(values, updateOption)
```

### PI Web API (REST) -- Cross-Platform
- `GET /streams/{webId}/recorded` -- recorded values
- `GET /streams/{webId}/interpolated` -- interpolated values
- `GET /streams/{webId}/plot` -- plot values
- `GET /streams/{webId}/summary` -- statistics
- `POST /streams/{webId}/recorded` -- write values
- `POST /batch` -- multiple requests in one call
- Auth: Kerberos (preferred) or Basic

### PI OLEDB (SQL Access)
```sql
SELECT tag, time, value FROM piarchive..picomp2
WHERE tag = 'sinusoid' AND time BETWEEN 'y' AND 't'
```

---

## 5. Troubleshooting

### Data Gaps
- Check buffer status, interface service, `piartool -qs` for queue backlog, message logs, network

### Stale Tags
- Check health tags: `UI_HEARTBEAT`, `UI_IORATE`, `UI_SCIORATE`, `UI_SCSKIPPED`
- Verify `Scan` attribute = 1, PointSource correct

### Buffering Issues
- `pibufss -cfg` to check status
- Verify network, queue size, PI Trust/mapping for write access

### Common System Digital States

| State | Meaning |
|---|---|
| Shutdown | Written on DA restart |
| Bad Input | Interface can't read source |
| Pt Created | No data yet |
| I/O Timeout | Communication timeout |
| Calc Failed | PE or totalizer failed |

---

Sources: [AVEVA PI Data Archive Admin Docs](https://docs.aveva.com/bundle/pi-server-s-da-admin/page/1032389.html), [Compression Testing](https://docs.aveva.com/bundle/pi-server-s-da-admin/page/1021696.html), [PI Web API Reference](https://docs.aveva.com/bundle/pi-web-api-reference/page/help.html), [PI Buffer Subsystem](https://docs.aveva.com/bundle/pi-server-s-buf-ha/page/1020154.html), [PI System Security](https://osicdn.blob.core.windows.net/learningcontent/Online%20Course%20Workbooks/Configuring%20PI%20System%20Security.pdf)
