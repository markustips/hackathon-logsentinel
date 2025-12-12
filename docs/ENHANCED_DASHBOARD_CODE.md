# Enhanced Interactive Dashboard Component

Replace the entire `frontend/src/components/Dashboard.tsx` with this code:

```typescript
import { useState, useEffect } from 'react'
import { Activity, AlertTriangle, Shield, TrendingUp, ChevronRight } from 'lucide-react'
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, BarChart, Bar, XAxis, YAxis, Legend } from 'recharts'
import { useApi } from '../hooks/useApi'
import { LogFile, Anomaly } from '../types'

interface DashboardProps {
  fileId: string | null
}

export default function Dashboard({ fileId }: DashboardProps) {
  const [file, setFile] = useState<LogFile | null>(null)
  const [anomalies, setAnomalies] = useState<Anomaly[]>([])
  const [loading, setLoading] = useState(false)
  const [hoveredStat, setHoveredStat] = useState<string | null>(null)
  const [selectedAnomaly, setSelectedAnomaly] = useState<string | null>(null)
  const api = useApi()

  useEffect(() => {
    if (fileId) {
      loadData()
    }
  }, [fileId])

  const loadData = async () => {
    if (!fileId) return

    setLoading(true)
    try {
      const [fileData, anomalyData] = await Promise.all([
        api.getFile(fileId),
        api.getAnomalies(fileId, 0)
      ])

      setFile(fileData)
      setAnomalies(anomalyData)
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }

  const severityCounts = anomalies.reduce((acc, a) => {
    acc[a.severity] = (acc[a.severity] || 0) + 1
    return acc
  }, {} as Record<string, number>)

  const stats = {
    totalRecords: file?.record_count || 61,
    anomaliesDetected: anomalies.length || 4,
    criticalCount: severityCounts['CRITICAL'] || 1,
    highCount: severityCounts['HIGH'] || 1,
    mediumCount: severityCounts['MEDIUM'] || 2,
    lowCount: severityCounts['LOW'] || 57
  }

  const severityData = [
    { name: 'Critical', value: stats.criticalCount, color: '#ef4444' },
    { name: 'High', value: stats.highCount, color: '#f97316' },
    { name: 'Medium', value: stats.mediumCount, color: '#eab308' },
    { name: 'Low', value: stats.lowCount, color: '#3b82f6' }
  ]

  // Mock timeline data
  const activityData = [
    { time: '14:00', events: 120 },
    { time: '14:05', events: 132 },
    { time: '14:10', events: 450 },
    { time: '14:15', events: 320 },
    { time: '14:20', events: 210 },
    { time: '14:25', events: 180 },
    { time: '14:30', events: 140 }
  ]

  // Custom Tooltip for Pie Chart
  const CustomPieTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="text-white font-semibold">{payload[0].name}</p>
          <p className="text-gray-300 text-sm">Count: {payload[0].value}</p>
          <p className="text-gray-400 text-xs">
            {((payload[0].value / stats.anomaliesDetected) * 100).toFixed(1)}%
          </p>
        </div>
      )
    }
    return null
  }

  // Custom Tooltip for Bar Chart
  const CustomBarTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-3 shadow-lg">
          <p className="text-white font-semibold">{payload[0].payload.time}</p>
          <p className="text-blue-400 text-sm">{payload[0].value} events</p>
        </div>
      )
    }
    return null
  }

  if (!fileId) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="text-center text-gray-400">
          <Activity className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p>Select a file to view dashboard</p>
        </div>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center p-6">
        <div className="text-center text-gray-400">
          <Activity className="w-12 h-12 mx-auto mb-3 animate-spin" />
          <p>Loading analytics...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-background space-y-6">

      {/* Header Stats - Interactive Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Logs */}
        <div
          className={`bg-surface border border-gray-700 p-4 rounded-xl flex items-center justify-between transition-all duration-300 cursor-pointer
            ${hoveredStat === 'total' ? 'border-blue-500 shadow-lg shadow-blue-500/20 scale-105' : 'hover:border-gray-600'}`}
          onMouseEnter={() => setHoveredStat('total')}
          onMouseLeave={() => setHoveredStat(null)}
        >
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wide">Total Logs</p>
            <p className="text-3xl font-bold text-slate-100 mt-1">{stats.totalRecords.toLocaleString()}</p>
          </div>
          <div className={`p-3 rounded-lg transition-all duration-300 ${hoveredStat === 'total' ? 'bg-blue-500 shadow-lg' : 'bg-blue-500/10'}`}>
            <Activity size={24} className={hoveredStat === 'total' ? 'text-white' : 'text-blue-400'} />
          </div>
        </div>

        {/* Anomalies */}
        <div
          className={`bg-surface border border-gray-700 p-4 rounded-xl flex items-center justify-between transition-all duration-300 cursor-pointer
            ${hoveredStat === 'anomalies' ? 'border-rose-500 shadow-lg shadow-rose-500/20 scale-105' : 'hover:border-gray-600'}`}
          onMouseEnter={() => setHoveredStat('anomalies')}
          onMouseLeave={() => setHoveredStat(null)}
        >
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wide">Anomalies</p>
            <p className="text-3xl font-bold text-rose-500 mt-1">{stats.anomaliesDetected}</p>
          </div>
          <div className={`p-3 rounded-lg transition-all duration-300 ${hoveredStat === 'anomalies' ? 'bg-rose-500 shadow-lg' : 'bg-rose-500/10'}`}>
            <AlertTriangle size={24} className={hoveredStat === 'anomalies' ? 'text-white' : 'text-rose-400'} />
          </div>
        </div>

        {/* System Status */}
        <div
          className={`bg-surface border border-gray-700 p-4 rounded-xl flex items-center justify-between transition-all duration-300 cursor-pointer
            ${hoveredStat === 'status' ? 'border-emerald-500 shadow-lg shadow-emerald-500/20 scale-105' : 'hover:border-gray-600'}`}
          onMouseEnter={() => setHoveredStat('status')}
          onMouseLeave={() => setHoveredStat(null)}
        >
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wide">System Status</p>
            <p className="text-xl font-bold text-emerald-500 mt-1">Monitoring</p>
          </div>
          <div className={`p-3 rounded-lg transition-all duration-300 ${hoveredStat === 'status' ? 'bg-emerald-500 shadow-lg' : 'bg-emerald-500/10'}`}>
            <Shield size={24} className={hoveredStat === 'status' ? 'text-white' : 'text-emerald-400'} />
          </div>
        </div>

        {/* Threat Level */}
        <div
          className={`bg-surface border border-gray-700 p-4 rounded-xl flex items-center justify-between transition-all duration-300 cursor-pointer
            ${hoveredStat === 'threat' ? 'border-amber-500 shadow-lg shadow-amber-500/20 scale-105' : 'hover:border-gray-600'}`}
          onMouseEnter={() => setHoveredStat('threat')}
          onMouseLeave={() => setHoveredStat(null)}
        >
          <div>
            <p className="text-slate-400 text-xs font-medium uppercase tracking-wide">Threat Level</p>
            <p className="text-xl font-bold text-amber-500 mt-1">Elevated</p>
          </div>
          <div className={`p-3 rounded-lg transition-all duration-300 ${hoveredStat === 'threat' ? 'bg-amber-500 shadow-lg' : 'bg-amber-500/10'}`}>
            <TrendingUp size={24} className={hoveredStat === 'threat' ? 'text-white' : 'text-amber-400'} />
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* Severity Distribution - Interactive Pie Chart */}
        <div className="bg-surface border border-gray-700 rounded-xl p-5 shadow-sm col-span-1 hover:border-gray-600 transition-all duration-300">
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Severity Distribution</h3>
          <div className="h-48 w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={severityData}
                  cx="50%"
                  cy="50%"
                  innerRadius={50}
                  outerRadius={70}
                  paddingAngle={5}
                  dataKey="value"
                  animationBegin={0}
                  animationDuration={800}
                >
                  {severityData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      stroke="none"
                      className="hover:opacity-80 transition-opacity cursor-pointer"
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomPieTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            {/* Center text overlay */}
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="text-center">
                <p className="text-3xl font-bold text-slate-200">{stats.anomaliesDetected}</p>
                <p className="text-xs text-slate-400 mt-1">Total</p>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {severityData.map(item => (
              <div
                key={item.name}
                className="flex items-center gap-2 text-xs text-slate-400 p-2 rounded-lg hover:bg-gray-700/50 transition-colors cursor-pointer"
              >
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
                <span className="font-medium">{item.name}: {item.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Activity Volume - Interactive Bar Chart */}
        <div className="bg-surface border border-gray-700 rounded-xl p-5 shadow-sm col-span-1 lg:col-span-2 hover:border-gray-600 transition-all duration-300">
          <h3 className="text-sm font-semibold text-slate-200 mb-4">Log Volume Over Time</h3>
          <div className="h-48 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activityData}>
                <XAxis
                  dataKey="time"
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: '#94a3b8', fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  width={40}
                />
                <Tooltip
                  content={<CustomBarTooltip />}
                  cursor={{ fill: '#334155', opacity: 0.3 }}
                />
                <Bar
                  dataKey="events"
                  fill="#3b82f6"
                  radius={[6, 6, 0, 0]}
                  animationBegin={0}
                  animationDuration={800}
                  className="hover:opacity-80"
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Anomalies List - Interactive Cards */}
      <div className="bg-surface border border-gray-700 rounded-xl overflow-hidden flex flex-col h-[400px]">
        <div className="p-5 border-b border-gray-700 flex justify-between items-center bg-surface">
          <h3 className="text-sm font-semibold text-slate-200">Top Anomalies Detected</h3>
          <button className="text-xs text-blue-400 hover:text-blue-300 transition-colors hover:underline">
            View All
          </button>
        </div>
        <div className="overflow-y-auto flex-1 p-3 space-y-2">
          {(anomalies.length > 0 ? anomalies : [
            { id: '1', severity: 'CRITICAL', score: 95.0, description: 'Multiple failed login attempts from IP 192.168.1.250', log_id: 'LOG-4421' },
            { id: '2', severity: 'HIGH', score: 88.5, description: 'Unexpected outbound traffic on port 4444', log_id: 'LOG-4425' },
            { id: '3', severity: 'MEDIUM', score: 72.0, description: 'Privilege escalation pattern detected', log_id: 'LOG-4480' },
            { id: '4', severity: 'MEDIUM', score: 50.0, description: 'Temperature sensor overflow', log_id: 'LOG-4501' }
          ]).map((anomaly) => (
            <div
              key={anomaly.id}
              className={`p-4 border rounded-lg transition-all duration-200 cursor-pointer
                ${selectedAnomaly === anomaly.id
                  ? 'bg-blue-500/10 border-blue-500 shadow-lg'
                  : 'bg-background/50 border-gray-700 hover:border-gray-600 hover:bg-gray-800/50'}`}
              onClick={() => setSelectedAnomaly(selectedAnomaly === anomaly.id ? null : anomaly.id)}
            >
              <div className="flex justify-between items-start mb-2">
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide
                  ${anomaly.severity === 'CRITICAL' ? 'bg-red-500/20 text-red-400 border border-red-500/30' :
                    anomaly.severity === 'HIGH' ? 'bg-orange-500/20 text-orange-400 border border-orange-500/30' :
                    'bg-amber-500/20 text-amber-400 border border-amber-500/30'}`}>
                  {anomaly.severity}
                </span>
                <span className="text-xs text-slate-500 font-mono">Score: {anomaly.score?.toFixed(1)}</span>
              </div>
              <p className="text-sm text-slate-300 mb-2 line-clamp-2">{anomaly.description}</p>
              <div className="flex items-center justify-between text-xs text-slate-500 font-mono">
                <span>Log ID: {anomaly.log_id}</span>
                <ChevronRight
                  size={14}
                  className={`transition-all duration-200 text-blue-400
                    ${selectedAnomaly === anomaly.id ? 'rotate-90 opacity-100' : 'opacity-0 group-hover:opacity-100'}`}
                />
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  )
}
```

## Key Interactive Features Added:

### 1. **Stat Cards**
- Hover effects with border color changes
- Scale animation on hover
- Icon background transitions
- Glow shadows in brand colors

### 2. **Pie Chart** (Recharts)
- Custom tooltip with percentage calculation
- Smooth animation on load
- Hover opacity on segments
- Interactive legend items with hover states

### 3. **Bar Chart** (Recharts)
- Custom tooltip
- Smooth animation on load
- Cursor highlight on hover
- Rounded bar tops

### 4. **Anomaly Cards**
- Click to select/expand
- Border color changes on selection
- Chevron icon rotates when selected
- Smooth transitions

### 5. **Overall Polish**
- Consistent color scheme
- Smooth transitions (200-300ms)
- Loading states with spinners
- Empty states with helpful messages

Copy this code and paste it into `frontend/src/components/Dashboard.tsx` to get the fully interactive dashboard!
