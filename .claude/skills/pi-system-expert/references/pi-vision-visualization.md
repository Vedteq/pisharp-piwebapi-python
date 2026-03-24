# PI Vision & Visualization -- Expert Technical Reference

## 1. PI Vision

### Architecture
- Web-based on IIS, HTML5/CSS3/JS (AngularJS), ASP.NET backend
- Uses AF SDK to communicate with PI Data Archive and AF Server
- Requires MS SQL Server 2014+ for display storage
- Responsive — works on phones, tablets, desktops

### Lineage
PI Coresight → renamed to **PI Vision in 2017**. Namespace changed from `window.Coresight` to `window.PIVisualization`.

### Symbol Types

| Symbol | Description |
|---|---|
| Value | Current/end-of-range value with UOM |
| Trend | Line chart, multiple traces, independent y-axes, cursors |
| XY Plot | Scatter plot for data relationships |
| Table | Tabular time-series with timestamps |
| Asset Comparison Table | Rows = assets, columns = shared attributes |
| Gauge (radial/linear/bar) | Switchable to/from Value |
| Multi-state | Any symbol changes color/appearance based on conditions |
| Event Frame Table | Event frames in tabular form |

**Symbol switching**: Trend ↔ Table; Value ↔ any Gauge type.

### AF-Aware Displays
Displays built with AF element templates become **asset-relative**. Context switcher dropdown switches all symbols to a different asset of the same type. One display serves an entire fleet.

### Custom Symbols (Extensibility SDK)
Files go in the `ext/` folder on PI Vision server:

| File | Convention | Purpose |
|---|---|---|
| `sym-<name>.js` | Implementation | Registration, init, data handling |
| `sym-<name>-template.html` | Presentation | HTML with AngularJS bindings |
| `sym-<name>-config.html` | Configuration | Config pane HTML |
| `sym-<name>.css` | Styles | Optional CSS |

```javascript
var definition = {
    typeName: 'myCustomSymbol',
    datasourceBehavior: PV.Extensibility.Enums.DatasourceBehaviors.Single,
    visObjectType: symbolVis,
    getDefaultConfig: function() {
        return { DataShape: 'Value', Height: 200, Width: 400 };
    }
};

function symbolVis() { }
symbolVis.prototype.init = function(scope, elem) {
    this.onDataUpdate = function(data) {
        if (data) {
            scope.value = data.Value;
            scope.timestamp = data.Time;
        }
    };
};
```

---

## 2. PI ProcessBook (Legacy — End of Support Dec 2024)

### Overview
Windows desktop app (.exe, 32-bit). Displays are `.PDI` files.

### Key Features
- Trends, bar charts, XY plots, static graphics
- **Multi-state objects**: shapes change color/visibility based on tag conditions
- **VBA scripting**: every `.PDI` has an associated VBA project
- **DataSets**: custom calculated datasets

### VBA Object Model
```vba
Dim disp As Display
Set disp = ThisDisplay

' Iterate symbols
For Each sym In ThisDisplay.Symbols
    If sym.Type = pbSymbolValue Then
        tagName = sym.GetTagName(1)
    End If
Next sym

' Create trend
Dim oTrend As Trend
Set oTrend = ThisDisplay.Symbols.Add(pbSymbolTrend)
oTrend.AddTrace "\\Server\sinusoid"

' Time range
ThisDisplay.PointTrend.SetStartAndEndTime "*-1d", "*"
```

**Events**: `Display_Open()`, `Display_BeforeClose()`, `Display_DataUpdate()`, `Symbol_Click()`

### Migration to PI Vision
- Migration utility converts `.PDI` to PI Vision displays
- VBA code does NOT migrate (must rewrite in JavaScript)
- ActiveX controls, complex DataSets, OLE objects don't migrate

---

## 3. PI DataLink (Excel Add-in)

### Function Reference

**PIArcVal** (single point-in-time):
```
=PIArcVal("tagname", "timestamp", outcode, "PIServer", "mode")
```
Modes: `auto`, `interpolated`, `previous`, `next`

**PICompDat** (compressed/recorded values):
```
=PICompDat("tagname", "startTime", "endTime", outcode, "PIServer", "mode")
```

**PISampDat** (evenly-spaced interpolated):
```
=PISampDat("tagname", "startTime", "endTime", "interval", outcode, "PIServer")
```

**PITimDat** (values at specified timestamps):
```
=PITimDat("tagname", timestamps, outcode, "PIServer")
```

**PIExpDat** (calculated expression):
```
=PIExpDat("expression", "startTime", "endTime", "interval", outcode, "PIServer")
```

**PICalcVal** (single summary):
```
=PICalcVal("tagname", "startTime", "endTime", "mode", cfactor, outcode, "PIServer")
```
Modes: `total`, `average`, `minimum`, `maximum`, `range`, `stdev`, `count`

### Outcode Reference

| Code | Meaning |
|---|---|
| 0 | Value only |
| 1 | Timestamp + Value (columns) |
| 2 | Transposed (rows) |
| 4 | Adds % Good column |
| 5 | Timestamp + Value + % Good |

Array formulas: `Ctrl+Shift+Enter` (legacy) or auto-spill (Excel 365).

---

## 4. Dashboarding Best Practices

### Operator vs Management Displays

| Aspect | Operators | Management |
|---|---|---|
| Focus | Real-time monitoring | Historical summaries, KPIs |
| Symbols | Trends, gauges, multi-state | Bar charts, comparison tables |
| Update rate | Continuous | Periodic (shift/daily) |
| Density | Higher | Lower, focused |

### Design Principles
- Subdued visuals for normal state, bold colors for alarms only
- Don't overload — highlight anomalies, don't dump raw data
- Colorblind accessible (never color alone)
- Navigation hierarchy: Summary → Area → Equipment detail
- Use AF-relative displays instead of duplicating per asset
- Multi-state indicators for quick anomaly detection

Sources: [PI Vision Architecture](https://docs.aveva.com/bundle/pi-vision/page/1009400.html), [Extensibility Guide](https://github.com/AVEVA/AVEVA-Samples-PI-System/blob/main/docs/PI-Vision-Extensibility-Docs/PI%20Vision%20Extensibility%20Guide.md), [PI DataLink Functions](https://docs.aveva.com/bundle/pi-datalink/page/1013798.html), [Dashboard Best Practices](https://www.itigroup.com/news-blogs/unlocking-insights-dashboard-design-best-practices-with-aveva-pi-vision/)
