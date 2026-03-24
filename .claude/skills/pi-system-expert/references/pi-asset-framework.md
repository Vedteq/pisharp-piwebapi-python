# AVEVA PI Asset Framework (PI AF) -- Expert-Level Technical Notes

## 1. Architecture

### AF Server
- **PI AF Server** is a Windows service (`AFService.exe`) that hosts the Asset Framework runtime. It stores all configuration metadata in a **SQL Server database** called `PIFD` (PI Framework Database).
- The AF Server communicates with clients via **WCF (Windows Communication Foundation)** over TCP (default port **5457**).
- Multiple AF databases can exist on a single AF Server. Each `AFDatabase` is an independent container of elements, templates, tables, enumeration sets, categories, and analyses.

### AF Database Structure
- **Elements** represent physical or logical assets (pumps, tanks, production lines, sites). Elements are organized in a **tree hierarchy** rooted at the database level.
- **Attributes** are properties of elements. Each attribute has a value type (Double, Int32, String, DateTime, etc.) and optionally a **data reference** that fetches its value dynamically.
- **Templates** define reusable blueprints for elements and event frames. An element template specifies attribute templates, child element templates, default analyses, and categories.
- **Categories** are tags/labels applied to elements, attributes, or analyses for grouping and filtering. They have no hierarchy -- they are flat classification labels.
- **Enumeration Sets** define discrete named states (e.g., "Running", "Stopped", "Faulted") mapped to integer values.

### Attribute Data Reference Types

| Data Reference | Description |
|---|---|
| **PI Point** | Maps to a PI Data Archive tag. Supports substitution parameters for dynamic tag name resolution. |
| **PI Point Array** | Maps to multiple PI points, returning an array of values. |
| **Formula** | Evaluates a mathematical formula using other attributes as inputs. Uses PI Performance Equation (PE) syntax. |
| **Table Lookup** | Retrieves a value from an AF Table based on row-matching conditions using AND/OR logic. |
| **String Builder** | Constructs a string value using substitution parameters like `%Element%`, `%@AttributeName%`, `%..\..\Element%`. |
| **URI Builder** | Constructs a URI dynamically using substitution parameters. |
| **None (static)** | Stores a fixed value directly on the attribute. No external data source. |

### Substitution Parameters
- `%Element%` -- name of the containing element
- `%..%` or `%..\Element%` -- parent element traversal
- `%@AttributeName%` -- value of a sibling attribute (the `@` prefix dereferences the attribute value)
- `%@.|ChildAttribute%` -- value of a child attribute
- `%Template%` -- template name
- `%Database%` -- database name
- `%Server%` -- AF server name
- `%Description%` -- element description

---

## 2. AF Modeling Best Practices

### Element Hierarchy Design
- **Geographic/Functional hierarchy** is the most common pattern: Enterprise > Site > Area > Unit > Equipment.
- The **primary hierarchy** uses **Parent-Child references** (the default). Deleting the parent deletes all children.
- **Weak references** create additional "views" or cross-references. A weak reference does not own the element -- if the weak reference is removed, the element persists in its primary location.

### Template Inheritance
- **Base templates** define common attributes shared across equipment types (e.g., a "Rotating Equipment" base template with Speed, Vibration, Temperature).
- **Derived templates** extend base templates with specialized attributes (e.g., "Centrifugal Pump" derives from "Rotating Equipment" and adds FlowRate, DischargePressure).
- Derived templates **inherit all attributes** from the base. You can **override** a base attribute by creating an attribute with the **exact same name**.
- Template inheritance is single-inheritance only, but you can chain: Base > Derived1 > Derived2.

### Attribute Configuration
- Store **configuration data as static attributes** (manufacturer, model number, installation date) directly on the element.
- Store **real-time data as PI Point data references** using substitution parameters for tag name resolution.
- Use **child attributes** for grouping related configuration items.
- Best practice: Use `%@.|PITagName%` pattern where a configuration attribute holds the actual tag name, and the PI Point data reference uses substitution to resolve it.

### AF Tables
- **Internal tables** -- data stored directly in the PIFD SQL database.
- **Imported tables** -- data imported from an external source (snapshot, not live).
- **Linked tables** -- live connection to an external SQL Server database via connection string.
- Keep AF lookup tables **small** to avoid performance issues.

### Naming Conventions
- Use consistent naming for templates, elements, and attributes across the enterprise.
- Use **leading zeros** for numeric identifiers: `PUMP01`, not `PUMP1`.
- Maintain abbreviation standards (e.g., always "TMP" for temperature).

---

## 3. AF Analytics

### Analysis Types

**Expression Analysis**
- Uses Performance Equation (PE) syntax to compute output values from input attributes.
- Variable mapping: Input variables map to AF attributes. Output variables map to output attributes where results are written.
- Syntax: `IF 'Variable1' < 50 THEN "under limit" ELSE "good"`

**Key Expression Functions by Category:**

| Category | Functions |
|---|---|
| **Aggregation** | `TagTot`, `TagMean`, `TagAvg`, `TagMax`, `TagMin`, `TagVal`, `PctGood`, `StDev`, `Range` |
| **Counting** | `EventCount`, `FindEq`, `FindGT`, `FindLT`, `FindGE`, `FindLE`, `FindNE` |
| **Math** | `Abs`, `Sqr`, `Sqrt`, `Round`, `Trunc`, `Log`, `Ln`, `Exp`, `Sin`, `Cos`, `Tan` |
| **String** | `Trim`, `Left`, `Right`, `Mid`, `Concat`, `Len`, `UCase`, `LCase`, `InStr`, `Format` |
| **Status** | `BadVal`, `IsSet`, `DigState`, `StateNo` |
| **Navigation** | `Prev`, `PrevVal`, `PrevEvent`, `NextVal`, `NextEvent` |
| **Time** | `Timestamp`, `Year`, `Month`, `Day`, `Hour`, `Minute`, `Second`, `DaySec`, `Weekday`, `Yearday` |
| **Conditional** | `IF...THEN...ELSE`, `Case` |

**Rollup Analysis**
- Aggregates values from child element attributes or attributes matching a category/template filter.
- Rollup functions: Average, Total (Sum), Minimum, Maximum, Count, Range, StdDev, PercentGood.

### Scheduling

| Mode | Description |
|---|---|
| **Event-Triggered** | Executes when any mapped input attribute receives a new event. |
| **Periodic** | Executes at a fixed interval (e.g., every 5 minutes, hourly). |
| **Natural** | Used with event frame generation -- tied to the event lifecycle. |

### Backfilling and Recalculation
- **Backfill**: Fills in data gaps only. Does not overwrite existing output values.
- **Recalculation**: Deletes ALL existing output values in the time range, then recalculates from scratch. Use when input data has been corrected.
- Management via PSE Analyses tab or programmatically via `AFAnalysisService.QueueCalculation()`.
- Out-of-order data is ignored as triggers in real-time; you must recalculate manually or enable auto-recalculation.

---

## 4. Event Frames

### Core Concepts
- An **Event Frame** captures a time-bounded event with a start time, end time (optional for in-progress events), and associated attributes/data.
- Event frames can be **nested** (parent/child hierarchy) following ISA-88 batch standards: Procedure > Unit Procedure > Operation > Phase.
- Event frames are **searchable** by time range, template, element reference, attribute value, name, and category.

### Event Frame Templates
- Define standardized attribute sets for event types.
- Template attributes can have PI Point data references that capture data at event start/end or over the event duration.

### Event Frame Generation Analysis
- **StartTrigger**: Expression that, when TRUE, creates a new event frame. When FALSE, closes it.
- **EndTrigger**: Optional separate expression for closing the event frame.
- **"True For" option**: Requires the trigger to remain true for a specified duration before generating the event frame.
- For **child event frames**: Multiple start triggers can be active simultaneously, creating a hierarchy.

### Use Cases
- **Batch Tracking**: ISA-88 hierarchy (Batch > UnitProcedure > Phase).
- **Golden Batch**: Compare current batch against a reference "golden" batch.
- **Downtime Tracking**: Capture equipment downtime with reason codes and duration.
- **Alarm/Exceedance Tracking**: Event frames generated when process variables exceed limits.

---

## 5. AF SDK / .NET Development

### Key Namespaces

| Namespace | Contents |
|---|---|
| `OSIsoft.AF` | `PISystem`, `PISystems`, `AFDatabase`, `AFDatabases` |
| `OSIsoft.AF.Asset` | `AFElement`, `AFAttribute`, `AFElementTemplate`, `AFAttributeTemplate`, `AFCategory`, `AFTable`, `AFEnumerationSet` |
| `OSIsoft.AF.PI` | `PIPoint`, `PIPointList`, `PIServer`, `PIServers` |
| `OSIsoft.AF.Data` | `AFListData`, `AFData` -- bulk data access methods |
| `OSIsoft.AF.EventFrame` | `AFEventFrame`, `AFEventFrames` |
| `OSIsoft.AF.Search` | `AFElementSearch`, `AFEventFrameSearch`, `AFAttributeSearch`, `AFAnalysisSearch` |
| `OSIsoft.AF.Time` | `AFTime`, `AFTimeRange`, `AFTimeSpan` |

### Connection Patterns

```csharp
// Implicit connection (recommended)
PISystems piSystems = new PISystems();
PISystem piSystem = piSystems["MyAFServer"];
AFDatabase afDb = piSystem.Databases["MyDatabase"];

// PI Data Archive connection
PIServers piServers = new PIServers();
PIServer piServer = piServers["MyPIServer"];
piServer.Connect();
```

### Key Classes and Methods

**AFElement:**
- `afDb.Elements` -- root element collection
- `element.Elements` -- child elements
- `element.Attributes["AttrName"]` -- attribute by name
- `AFElement.FindElementsByTemplate()` -- find elements by template

**AFAttribute:**
- `attribute.GetValue()` -- current value (returns `AFValue`)
- `attribute.Data.RecordedValues(timeRange, boundaryType, ...)` -- historical recorded values
- `attribute.Data.InterpolatedValues(timeRange, interval, ...)` -- interpolated values
- `attribute.Data.Summaries(timeRange, summaryDuration, summaryTypes, ...)` -- summary statistics
- `attribute.PIPoint` -- the underlying PIPoint (if PI Point data reference)

**PIPoint:**
- `PIPoint.FindPIPoints(piServer, query)` -- returns `IEnumerable<PIPoint>`
- `piPoint.RecordedValues(timeRange, boundaryType, filterExpression, ...)` -- recorded values
- `piPoint.UpdateValue(AFValue, AFUpdateOption)` -- write single value
- `piPoint.CurrentValue()` -- snapshot value

**PIPointList (Bulk Operations):**
- `PIPointList.RecordedValues(...)` -- bulk recorded values across multiple points
- When a `PIPointList` contains points from multiple PI Servers, the SDK internally partitions by server and issues parallel bulk queries.
- Use `PIPagingConfiguration` to control page size.

**AFAttributeList (Bulk Operations):**
- `AFAttributeList.Data.RecordedValues(...)` -- bulk data via AF attributes
- `AFAttributeList.Data.UpdateValues(values, AFUpdateOption)` -- bulk write
- Performance: 1000 points x 3 events = 3000 values written in ~252ms via single RPC call.

**AFEventFrame:**
- `new AFEventFrame(afDb, "EventName", efTemplate)` -- create event frame
- `eventFrame.SetStartTime(AFTime)`, `eventFrame.SetEndTime(AFTime)`
- `eventFrame.PrimaryReferencedElement` -- the associated element
- `eventFrame.Acknowledge()` -- acknowledge the event

**Search Classes (AF SDK 2.8+):**
- `AFElementSearch` -- `new AFElementSearch(afDb, "searchName", queryString)`
  - Query syntax: `Name:='Pump*' Template:='CentrifugalPump' Category:='Critical'`
- `AFEventFrameSearch` -- `new AFEventFrameSearch(afDb, "searchName", queryString)`
  - Filter operators: `Name`, `Template`, `Category`, `ElementName`, `Start`, `End`, `InProgress`, `Duration`

### CheckIn/CheckOut Pattern
- `CheckOut()` to lock the object before modifying
- `ApplyChanges()` or `CheckIn()` to persist
- `UndoCheckOut()` to discard changes
- `afDb.CheckIn()` to batch-commit multiple changes

### AFTime
- `new AFTime("*")` -- current time
- `new AFTime("*-1h")` -- one hour ago
- `new AFTime("t")` -- today at midnight
- `new AFTime("y")` -- yesterday at midnight
- Timestamp precision: 1/65536th of a second (~15 microseconds)

---

## 6. PI Notifications

### Key Components

| Component | Description |
|---|---|
| **Notification Rule** | Defines trigger condition and subscribers |
| **Notification Contact** | Individual or group that receives messages |
| **Delivery Endpoint** | Destination (email address, IM address) |
| **Delivery Channel** | Transport: Email (SMTP), Microsoft OCS, or custom |
| **Escalation Team** | Ordered list of endpoints; messages escalate until acknowledged |

### Notification Flow
1. Event frame generated or analysis triggers condition
2. Notification rule evaluates the event
3. Message formatted with AF attribute substitution
4. Message sent to subscribed contacts
5. If unacknowledged, escalation proceeds

---

## 7. PI Analysis Service

### Deployment
- Windows service: `PIAnalysisManager.exe`
- Can be on same machine as AF Server or separate (recommended for large deployments)

### Key Configuration Parameters

| Parameter | Default | Description |
|---|---|---|
| `CalculationWaitTimeInSeconds` | 5 | Wait time before evaluating to ensure input data has arrived |
| `MaxConcurrentPerProcessor` | varies | Concurrent evaluations per CPU core |

### Performance Tuning
1. Remove non-production analyses from production AF Server
2. Optimize expensive analyses (many `TagTot`/`TagMean` over long ranges)
3. Adjust `CalculationWaitTimeInSeconds` based on data latency
4. Separate Analysis Service to dedicated server if needed
5. Monitor via Windows Performance Monitor counters

### Common Issues
- **High latency growing over time**: Service can't keep up. Reduce load, optimize, add hardware.
- **Missing output values**: Misconfigured output mappings, permissions, or stopped analysis.
- **Late-arriving data**: Ignored as real-time triggers. Enable auto-recalculation or manual backfill.

---

## 8. Best Practices Summary

### Template Design
- Standardize at enterprise level with base templates
- Use substitution parameters in PI Point references (never hard-code tag names)
- Group related attributes under child attributes
- Use categories for reporting classification

### AF Security
- Built-in identities: `Administrators`, `Engineers`, `World`
- Map Windows users/groups to AF identities
- Security inheritance: set at top levels, override at lower levels only when needed
- Principle of least privilege: `World` = read-only

### High Availability
- AF Collective: multiple AF Servers with SQL Server replication
- Primary = publisher; secondaries = read-only subscribers
- PI Analysis Service and Notifications require separate failover planning

Sources:
- [PI AF asset hierarchies](https://docs.aveva.com/bundle/pi-server-l-af-pse/page/1021106.html)
- [PI point data references](https://docs.aveva.com/bundle/pi-server-f-af-pse/page/1020491.html)
- [Substitution parameters](https://docs.aveva.com/bundle/pi-server-l-af-pse/page/1022031.html)
- [Base and derived templates](https://docs.aveva.com/bundle/pi-server-l-af-pse/page/1021662.html)
- [Expression functions reference](https://docs.aveva.com/bundle/pi-server-l-af-analytics/page/1021946.html)
- [Backfilling and recalculation](https://docs.aveva.com/bundle/pi-server-l-af-analytics/page/1022569.html)
- [Event frames](https://docs.aveva.com/bundle/pi-server-l-af-pse/page/1021923.html)
- [Event frame generation analyses](https://docs.aveva.com/bundle/pi-server-l-af-analytics/page/1021921.html)
- [AF SDK Overview](https://docs.aveva.com/bundle/af-sdk/page/html/af-sdk-overview.htm)
- [AF collective implementation](https://docs.aveva.com/bundle/pi-server-s-buf-ha/page/1022397.html)
- [Configuring PI System Security](https://osicdn.blob.core.windows.net/learningcontent/Online%20Course%20Workbooks/Configuring%20PI%20System%20Security.pdf)
- [Troubleshooting PI Analysis Service](https://community.aveva.com/pi-square-community/b/aveva-blog/posts/troubleshooting-pi-analysis-service-performance-issues-high-latency)
