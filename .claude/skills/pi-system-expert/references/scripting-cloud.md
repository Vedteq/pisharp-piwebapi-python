# PI System Scripting, Programming & Cloud -- Expert Technical Reference

## 1. PowerShell

### OSIsoft.PowerShell Module
Ships with PI SMT 2015+. Requires Windows PowerShell 4.0+.

```powershell
Import-Module OSIsoft.PowerShell
$con = Connect-PIDataArchive -PIDataArchiveMachineName "MYPISERVER"
```

**Core cmdlets**: `Get-PIPoint`, `Add-PIPoint`, `Remove-PIPoint`, `Set-PIPoint`, `Get-PIValue`, `Add-PIValue`, `Get-PIArchiveFileInfo`

**Bulk tag creation from CSV:**
```powershell
Import-Csv "C:\tags.csv" | ForEach-Object {
    Add-PIPoint -Connection $con -Name $_.TagName -PointType $_.PointType `
        -PointSource $_.PointSource -Attributes @{
            descriptor=$_.Description; compressing=$_.Compressing;
            excdev=$_.ExcDev; span=$_.Span; zero=$_.Zero; engunits=$_.EngUnits
        }
}
```

**Bulk attribute modification:**
```powershell
Get-PIPoint -Connection $con -WhereClause "pointsource:='OPC'" |
    Set-PIPoint -Attributes @{ compressing = 1; excdev = 0.5 }
```

**Tag rename:**
```powershell
Set-PIPoint -Connection $con -Name "OLD_NAME" -Attributes @{tag="OLD_NAME"; newtag="NEW_NAME"}
```

### PI Web API from PowerShell
```powershell
$baseUrl = "https://piwebapi.mycompany.com/piwebapi"
$response = Invoke-RestMethod -Uri "$baseUrl/dataservers" -UseDefaultCredentials
$data = Invoke-RestMethod -Uri "$baseUrl/streams/$webId/recorded?startTime=*-24h&endTime=*" -UseDefaultCredentials
```

---

## 2. Python

### PIconnect (AF SDK Wrapper)
Windows only, requires AF SDK. `pip install PIconnect`

```python
import PIconnect as PI

with PI.PIServer() as server:
    points = server.search('sinusoid*')
    tag = server.search('sinusoid')[0]
    data = tag.recorded_values('*-48h', '*')       # pandas.Series
    interp = tag.interpolated_values('*-1h', '*', '5m')  # 5-min intervals
    summary = tag.summary('*-14d', '*', SummaryType.MAXIMUM)

with PI.PIAFDatabase() as db:
    element = db.children['Plant1'].children['Area1']
    attr_data = element.attributes['Temperature'].recorded_values('*-24h', '*')
```

**Multi-tag DataFrame:**
```python
import pandas as pd
with PI.PIServer() as server:
    df = pd.concat([server.search(t)[0].interpolated_values('*-7d','*','1h') for t in tags], axis=1)
```

### PI Web API Python Client
`pip install osisoft.pidevclub.piwebapi`

```python
from osisoft.pidevclub.piwebapi import PIWebApiClient
client = PIWebApiClient("https://piwebapi/piwebapi", useKerberos=True)
df = client.data.get_recorded_values("pi:\\\\PISRV1\\sinusoid", start_time="*-1d", end_time="*")
```

### Raw requests
```python
import requests
from requests_kerberos import HTTPKerberosAuth
session = requests.Session()
session.auth = HTTPKerberosAuth()
data = session.get(f"{base_url}/streams/{webId}/recorded?startTime=*-24h").json()
```

---

## 3. C# / .NET AF SDK

### When to Use Which

| | AF SDK | PI Web API | PI SDK (Legacy) |
|---|---|---|---|
| Platform | Windows/.NET | Any (REST) | Windows (COM) |
| Performance | Highest | Moderate | Moderate |
| Status | Current | Current | **Deprecated** |

### Connection Management
```csharp
PISystems piSystems = new PISystems();
PISystem afServer = piSystems["MyAFServer"];
afServer.Connect();
PIServer piServer = new PIServers()["MyPIServer"];
piServer.Connect();
AFDatabase db = afServer.Databases["MyDatabase"];
```
**Critical**: Create single connection objects, keep alive for app lifetime. Don't recreate per call.

### Reading Data
```csharp
PIPoint tag = PIPoint.FindPIPoint(piServer, "sinusoid");
AFValues values = tag.RecordedValues(new AFTimeRange("*-24h","*"), AFBoundaryType.Inside, null, false, 0);
AFValues interp = tag.InterpolatedValues(new AFTimeRange("*-24h","*"), new AFTimeSpan(0,0,0,0,0,5,0), null, null, false);
```

### Bulk Operations
```csharp
AFAttributeList attrList = new AFAttributeList();
foreach (AFElement elem in elements)
    attrList.Add(elem.Attributes["Temperature"]);
AFValues[] allData = attrList.Data.RecordedValues(timeRange, AFBoundaryType.Inside, null, false, 0);
```

### Writing Data
```csharp
var values = new AFValues();
values.Add(new AFValue(tag1, 42.5, new AFTime("*")));
piServer.UpdateValues(values, AFUpdateOption.InsertNoCompression, AFBufferOption.BufferIfPossible);
```

### Search
```csharp
AFElementSearch search = new AFElementSearch(db, "MySearch", "Name:='Pump*' Template:'PumpTemplate'");
foreach (AFElement elem in search.FindElements()) { ... }
```

### NuGet
```xml
<PackageReference Include="OSIsoft.AFSDK" Version="2.10.*" />
```

---

## 4. SQL and PI

### PI OLEDB Provider (PI Data Archive only)
Connection: `Provider=PIOLEDB;Data Source=PISERVER01;`

```sql
-- Compressed data
SELECT tag, time, value FROM piarchive..picomp2
WHERE tag = 'sinusoid' AND time BETWEEN '*-24h' AND '*'

-- Interpolated
SELECT time, value FROM piarchive..piinterp
WHERE tag = 'ba:level.1' AND time BETWEEN '*-1d' AND '*' AND timestep = '1h'

-- Aggregates
SELECT tag, average, maximum, minimum, total, count FROM piarchive..picalc
WHERE tag = 'sinusoid' AND time BETWEEN '*-7d' AND '*'

-- Tag config
SELECT tag, descriptor, pointsource, engunits FROM pipoint..pipoint2 WHERE pointsource = 'R'
```

### PI OLEDB Enterprise (AF-based)
Connection: `Provider=PIOLEDBENT;Data Source=MYAFSERVER;Integrated Security=SSPI;`

### Linked Server in SQL Server
```sql
EXEC sp_addlinkedserver @server='PIOLEDB_LINK', @srvproduct='', @provider='PIOLEDB', @datasrc='PISERVER01';
SELECT * FROM OPENQUERY(PIOLEDB_LINK, 'SELECT tag, time, value FROM piarchive..picomp2 WHERE tag=''sinusoid'' AND time>''*-1h''')
```

### PI Integrator for Business Analytics
Publishes PI data to: SQL Server, Azure SQL, Azure Data Lake Gen2, S3, Kafka, Azure IoT Hub, Kinesis, Pub/Sub, CSV, Parquet. Zero-code. Three services: Framework, Sync, Worker Node.

---

## 5. Cloud Deployment

### Product Evolution
OSIsoft Cloud Services (OCS) → AVEVA Data Hub (ADH) → **CONNECT data services**

### PI-to-Cloud Transfer
- **PI to CONNECT Agent**: On-prem alongside PI Server, transfers to cloud SDS
- **CONNECT to PI Agent**: Reverse (cloud → on-prem)

### Cloud Data Model (SDS)
- **SDS Types**: Shape of events
- **SDS Streams**: Named series conforming to type
- **SDS Stream Views**: Virtual projections

### CONNECT API
```python
# OAuth2 token
resp = requests.post("https://dat-b.aveva.com/connect/token", data={
    "client_id": "<id>", "client_secret": "<secret>", "grant_type": "client_credentials"
})
token = resp.json()["access_token"]
# Query
streams = requests.get(f"https://uswe.datahub.connect.aveva.com/api/v1/Tenants/{tid}/Namespaces/{nid}/Streams",
    headers={"Authorization": f"Bearer {token}"}).json()
```

### Azure Deployment
ARM templates and PowerShell scripts: [AVEVA/sample-pi_core-deployment_azure-powershell](https://github.com/AVEVA/sample-pi_core-deployment_azure-powershell)

### Hybrid Patterns
1. On-prem primary + cloud analytics (PI Integrator → data lake)
2. Cloud primary + on-prem collection (PI Server in Azure, connectors pull from plant)
3. Full hybrid (collective spanning on-prem + cloud)
4. Edge + Cloud (Edge Data Store → OMF → CONNECT)

---

## 6. Security

### Three-Layer Model
1. **PI Identities**: Internal security principals (not Windows accounts)
2. **PI Mappings** (recommended): Windows users/groups → PI Identities via SSPI
3. **PI Trusts** (legacy): IP/hostname-based. Less secure.

### Kerberos Delegation (Double-Hop)
```
Browser → PI Vision/Web API (IIS) → PI Data Archive / AF Server
```

**SPN Registration:**
```cmd
setspn -s HTTP/piwebapi.mycompany.com DOMAIN\svc_piwebapi
```

Backend SPNs: `AFSERVER/<hostname>`, `PISERVER/<hostname>`

AD Delegation: "Trust this user for delegation to specified services only" → "Use any authentication protocol" → Add AFSERVER/PISERVER SPNs.

### Network Architecture (DMZ)
```
[Plant/OT] → [DMZ] → [Corporate/IT]
PI DA, AF     Connector Relay    PI Vision, Web API
Interfaces    (outbound only)    BI tools
```

### Key Ports
- PI Data Archive: TCP 5450
- PI AF Server: TCP 5457
- PI Web API: TCP 443
- No additional inbound for Windows Integrated Security

Sources: [OSIsoft.PowerShell Docs](https://techsupport.osisoft.com/Documentation/PI-Powershell/index.html), [PIconnect](https://piconnect.readthedocs.io/), [AF SDK Overview](https://docs.aveva.com/bundle/af-sdk/page/html/af-sdk-overview.htm), [PI OLEDB Basics](https://cdn.osisoft.com/learningcontent/pdfs/PI%20OLEDB%20Basics%20Learn%20How%20to%20Query%20PI.pdf), [PI Security Best Practices](https://cdn.osisoft.com/osi/presentations/2023-AVEVA-San-Francisco/UC23NA-2PGK06-AVEVA-Biggins-Best-practices-for-security-in--PI-System.pdf), [CONNECT API](https://docs.aveva.com/bundle/connect-data-services-developer/page/api-reference/ocs-api-reference.html)
