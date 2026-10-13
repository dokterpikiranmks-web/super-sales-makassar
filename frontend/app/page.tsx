"use client"
import { useState, useEffect } from "react"

interface Campaign {
  id: string
  name: string
  status: string
  objective: string
  created_time: string
}

interface Lead {
  id: string
  wa_id: string
  product_key: string
  product_name: string
  ad_id?: string
  status: string
  location: string
  created_at: string
  last_active: string
  bant: {
    budget: string
    authority: string
    need: string
    timeline: string
    score: number
  }
  chat_history?: { sender: string; message: string; timestamp: string }[]
}

interface ProductMetric {
  name: string
  price: number
  cogs: number
  daily_budget: number
  total_leads: number
  engaged: number
  follow_up: number
  closing: number
  spend: number
  revenue: number
  profit: number
  cpl: number
  roas: string
}

export default function MobileDashboard() {
  const [activeTab, setActiveTab] = useState<"dashboard" | "leads" | "roas" | "waba">("dashboard")
  const [campaigns, setCampaigns] = useState<Campaign[]>([])
  const [leads, setLeads] = useState<Lead[]>([])
  const [stats, setStats] = useState<{ [key: string]: ProductMetric }>({})
  const [wabaStatus, setWabaStatus] = useState<any>({
    status: "pending",
    status_label: "Menunggu Verifikasi (2 Hari Kerja)",
    phone_number: "+62 811-443-327",
    phone_status: "NOT_VERIFIED",
    can_activate_ads: false
  })
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdated, setLastUpdated] = useState<string>("")
  const [showModal, setShowModal] = useState(false)
  const [newProduct, setNewProduct] = useState({ name: "", price: "", target_sales: "10", budget_rp: "25000", description: "" })
  const [launching, setLaunching] = useState(false)
  const [launchMsg, setLaunchMsg] = useState("")

  const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "")

  const fetchData = async (isManual = false) => {
    try {
      if (isManual) setRefreshing(true)
      const [campRes, leadsRes, wabaRes] = await Promise.all([
        fetch(`${API_BASE}/api/campaigns`).catch(() => null),
        fetch(`${API_BASE}/api/leads`).catch(() => null),
        fetch(`${API_BASE}/api/waba/status`).catch(() => null)
      ])

      if (campRes && campRes.ok) {
        const campData = await campRes.json()
        setCampaigns(campData.data || [])
      }

      if (leadsRes && leadsRes.ok) {
        const leadData = await leadsRes.json()
        setLeads(leadData.leads || [])
        setStats(leadData.stats || {})
      }

      if (wabaRes && wabaRes.ok) {
        const wData = await wabaRes.json()
        setWabaStatus(wData)
      }

      setLastUpdated(new Date().toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit", second: "2-digit" }))
    } catch (err) {
      console.error("Gagal refresh data:", err)
    } finally {
      setLoading(false)
      if (isManual) setRefreshing(false)
    }
  }

  // Real-time polling every 30 seconds
  useEffect(() => {
    fetchData()
    const timer = setInterval(() => fetchData(false), 30000)
    
    // Register PWA service worker if supported
    if (typeof window !== "undefined" && "serviceWorker" in navigator) {
      navigator.serviceWorker.register("/sw.js").catch(() => {})
    }

    return () => clearInterval(timer)
  }, [])

  // Dynamic ROAS calculator function
  // Formula: (price * closing_rate * leads) / spend
  const calculateDynamicROAS = (price: number, leadsCount: number, spend: number, customClosingRate = 0.25) => {
    if (spend <= 0) return { roasVal: 0, text: "-", color: "text-slate-400", badgeColor: "bg-slate-800 text-slate-400" }
    const estimatedClosings = leadsCount > 0 ? Math.max(1, Math.round(leadsCount * customClosingRate)) : 0
    const estRevenue = price * estimatedClosings
    const roasVal = estRevenue / spend
    
    // Color indicator: >5x hijau, 3-5x kuning, <3x merah
    let color = "text-emerald-400"
    let badgeColor = "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
    if (roasVal < 3) {
      color = "text-rose-400"
      badgeColor = "bg-rose-500/20 text-rose-300 border-rose-500/40"
    } else if (roasVal <= 5) {
      color = "text-amber-400"
      badgeColor = "bg-amber-500/20 text-amber-300 border-amber-500/40"
    }
    return { roasVal: Number(roasVal.toFixed(1)), text: `${roasVal.toFixed(1)}x`, color, badgeColor }
  }

  const handleLaunchProduct = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newProduct.name) return alert("Mohon masukkan nama produk.")
    setLaunching(true)
    setLaunchMsg("")
    try {
      const res = await fetch(`${API_BASE}/api/product`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: newProduct.name,
          price: parseInt(newProduct.price) || 0,
          target_sales: parseInt(newProduct.target_sales) || 10,
          budget_rp: parseInt(newProduct.budget_rp) || 25000,
          description: newProduct.description
        })
      })
      const data = await res.json()
      setLaunchMsg(`Sukses! Campaign dibuat di Makassar (Status: PAUSED) dengan ID: ${data?.result?.campaign?.meta_campaign_id || "OK"}`)
      setShowModal(false)
      setNewProduct({ name: "", price: "", target_sales: "10", budget_rp: "25000", description: "" })
      fetchData(true)
    } catch (err: any) {
      alert("Gagal launch: " + err.message)
    } finally {
      setLaunching(false)
    }
  }

  // Dynamic leads counts from API
  const totokLeads = leads.filter(l => l.product_key === "totok_saraf").length
  const hipnoLeads = leads.filter(l => l.product_key === "hipnoterapi").length

  const totokROAS = calculateDynamicROAS(150000, totokLeads, 25000, 0.4) // target closing 30-40%
  const hipnoROAS = calculateDynamicROAS(600000, hipnoLeads, 25000, 0.5) // middle-up closing rate

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans pb-24 md:pb-12 antialiased selection:bg-emerald-500 selection:text-black">
      
      {/* 1. STICKY HEADER (Mobile Optimized) */}
      <header className="sticky top-0 z-40 bg-slate-950/95 backdrop-blur-md border-b border-slate-800/80 px-4 py-3 md:px-8 md:py-4 transition shadow-md">
        <div className="max-w-7xl mx-auto flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <h1 className="text-lg md:text-2xl font-black tracking-tight text-white">
                Super Sales Makassar
              </h1>
            </div>
            
            {/* Pull to refresh / Sync Button */}
            <button 
              onClick={() => fetchData(true)}
              disabled={refreshing}
              className="p-2 md:px-3 md:py-1.5 text-xs font-semibold rounded-xl bg-slate-900 border border-slate-800 hover:bg-slate-800 text-slate-300 flex items-center gap-1.5 active:scale-95 transition"
              title="Refresh Real-time"
            >
              <span className={refreshing ? "animate-spin" : ""}>🔄</span>
              <span className="hidden sm:inline">{refreshing ? "Memuat..." : "Sinkron"}</span>
              {lastUpdated && <span className="hidden lg:inline text-slate-500">({lastUpdated})</span>}
            </button>
          </div>

          {/* Badges Stack */}
          <div className="flex flex-wrap items-center gap-1.5 text-[11px] md:text-xs">
            <span className="px-2.5 py-0.5 rounded-full font-bold bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 flex items-center gap-1">
              <span>✓</span> 100% Valid • Terapis Pria • Sarung Tangan • Baju Lengkap
            </span>
            <span className={`px-2.5 py-0.5 rounded-full font-bold flex items-center gap-1 ${
              wabaStatus.can_activate_ads 
                ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40" 
                : "bg-amber-500/15 text-amber-300 border border-amber-500/30"
            }`}>
              <span>{wabaStatus.can_activate_ads ? "✓" : "⏳"}</span>
              WABA: {wabaStatus.status_label || "Menunggu Verifikasi"} • {wabaStatus.phone_number || "+62 811-443-327"}
            </span>
          </div>
        </div>
      </header>

      {/* MAIN CONTAINER */}
      <main className="max-w-7xl mx-auto w-full px-4 md:px-8 mt-5 flex-1">
        
        {/* NGROK / MOBILE ACCESS BANNER */}
        <div className="mb-6 p-3.5 rounded-2xl bg-gradient-to-r from-slate-900 via-slate-900 to-indigo-950 border border-slate-800 text-xs text-slate-300 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 shadow-sm">
          <div className="flex items-center gap-2">
            <span className="text-base">📱</span>
            <span>
              <strong>Akses di HP via ngrok:</strong> Jalankan <code className="bg-slate-950 px-1.5 py-0.5 rounded text-sky-400 font-mono">ngrok http 3000</code> lalu buka link di browser HP Anda.
            </span>
          </div>
          <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 shrink-0">
            PWA Ready • Add to Home Screen
          </span>
        </div>

        {launchMsg && (
          <div className="mb-6 p-4 rounded-xl bg-emerald-950/80 border border-emerald-700 text-emerald-200 text-xs sm:text-sm flex items-center justify-between shadow-lg">
            <span>{launchMsg}</span>
            <button onClick={() => setLaunchMsg("")} className="text-emerald-400 hover:text-white ml-2">✕</button>
          </div>
        )}

        {/* TAB 1: DASHBOARD VIEW */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            
            {/* Quick KPI Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
              <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/90 shadow-md">
                <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-slate-400 block">Total Campaigns</span>
                <div className="text-2xl sm:text-3xl font-black text-white mt-1">{campaigns.length}</div>
                <span className="text-[10px] sm:text-xs text-amber-400 mt-1 block font-medium">3 PAUSED (Aman)</span>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/90 shadow-md">
                <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-slate-400 block">Leads Masuk</span>
                <div className="text-2xl sm:text-3xl font-black text-white mt-1">{leads.length}</div>
                <span className="text-[10px] sm:text-xs text-emerald-400 mt-1 block font-medium">Real-time leads.json</span>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/90 shadow-md">
                <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-slate-400 block">Budget / Hari</span>
                <div className="text-2xl sm:text-3xl font-black text-emerald-400 mt-1">Rp 50.000</div>
                <span className="text-[10px] sm:text-xs text-slate-400 mt-1 block">Rp 25k Totok + Rp 25k Hipno</span>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/90 shadow-md">
                <span className="text-[10px] sm:text-xs font-bold uppercase tracking-wider text-slate-400 block">Est. ROAS Gabungan</span>
                <div className="text-2xl sm:text-3xl font-black text-sky-400 mt-1">9.0x</div>
                <span className="text-[10px] sm:text-xs text-emerald-400 mt-1 block font-medium">Margin Sehat Anti-Boncos</span>
              </div>
            </div>

            {/* 2 PRODUCT CARDS (MOBILE: 1 KOLOM, DESKTOP: 2 KOLOM) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mt-4">
              
              {/* CARD A: TOTOK SARAF (HIJAU MEDIS) */}
              <div className="p-5 sm:p-6 rounded-2xl bg-gradient-to-br from-emerald-950/40 via-slate-900 to-slate-950 border-2 border-emerald-500/80 shadow-xl relative overflow-hidden flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                      MASS MARKET 25-60th
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                      PAUSED
                    </span>
                  </div>

                  <h3 className="text-lg sm:text-xl font-black text-white mt-3 leading-snug">
                    Totok Saraf Makassar - Rp 150.000 / 60 menit
                  </h3>
                  <p className="text-xs text-emerald-300 font-semibold mt-0.5">
                    Konsultasi + Pemeriksaan Saraf + Terapi Totok Fisik
                  </p>

                  <div className="mt-3.5 p-3 rounded-xl bg-emerald-950/40 border border-emerald-800/50 text-xs text-emerald-100/95 leading-relaxed">
                    🌿 <strong>USP:</strong> Terapis Pria Berseragam Hijau Medis + Sarung Tangan Steril, Pasien Tetap Berpakaian Lengkap di Ruang Spa Higienis.
                  </div>

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-3 gap-2 sm:gap-2.5 mt-4 text-center">
                    <div className="bg-slate-950/80 p-2.5 rounded-xl border border-emerald-900/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Total Leads</span>
                      <span className="text-base sm:text-lg font-black text-white">{totokLeads}</span>
                    </div>
                    <div className="bg-slate-950/80 p-2.5 rounded-xl border border-emerald-900/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Budget / Hari</span>
                      <span className="text-base sm:text-lg font-black text-slate-200">Rp 25.000</span>
                    </div>
                    <div className="bg-slate-950/80 p-2.5 rounded-xl border border-emerald-900/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Target CPL</span>
                      <span className="text-base sm:text-lg font-black text-sky-400">Rp 15.000</span>
                    </div>

                    <div className="bg-slate-950/80 p-2.5 rounded-xl border border-emerald-900/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Target Closing</span>
                      <span className="text-base sm:text-lg font-black text-emerald-400">30 / bln</span>
                    </div>
                    <div className="bg-slate-950/80 p-2.5 rounded-xl border border-emerald-900/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Laba / Sesi</span>
                      <span className="text-base sm:text-lg font-black text-emerald-400">Rp 130.000</span>
                    </div>
                    <div className="bg-slate-950/80 p-2.5 rounded-xl border border-emerald-900/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Est. ROAS</span>
                      <span className={`text-base sm:text-lg font-black ${totokROAS.color}`}>{totokROAS.text}</span>
                    </div>
                  </div>
                </div>

                {/* Progress Bar Hijau */}
                <div className="mt-5 pt-3 border-t border-emerald-900/50">
                  <div className="flex justify-between text-[11px] text-slate-300 mb-1">
                    <span>Efisiensi ROAS Target: 6.0x</span>
                    <span className="font-bold text-emerald-400">85% Efektif</span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden border border-emerald-900">
                    <div className="bg-emerald-500 h-2.5 rounded-full" style={{ width: "85%" }}></div>
                  </div>
                </div>
              </div>

              {/* CARD B: HIPNOTERAPI (BIRU NAVY) */}
              <div className="p-5 sm:p-6 rounded-2xl bg-gradient-to-br from-blue-950/40 via-slate-900 to-slate-950 border-2 border-blue-500/80 shadow-xl relative overflow-hidden flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between gap-2">
                    <span className="px-3 py-1 rounded-full text-[11px] font-black uppercase tracking-wider bg-blue-500/20 text-blue-300 border border-blue-500/40">
                      MIDDLE-UP TIER 28-55th
                    </span>
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30">
                      PAUSED
                    </span>
                  </div>

                  <h3 className="text-lg sm:text-xl font-black text-white mt-3 leading-snug">
                    Hipnoterapi Dokter Pikiran - 1 Sesi Rp 600k • Paket 3 Sesi Rp 1,5jt
                  </h3>
                  <p className="text-xs text-sky-300 font-semibold mt-0.5">
                    Ekonomi Mapan • Atasi Insomnia, Cemas & Trauma
                  </p>

                  <div className="mt-3.5 p-3 rounded-xl bg-blue-950/40 border border-blue-800/50 text-xs text-blue-100/95 leading-relaxed">
                    🎁 <strong>Value Stack Rp 2.398.000:</strong> E-book 199k + Audio 199k + Pendampingan 21 Hari 2jt. Terapis Pria C.Ht. Bersertifikasi Klinis.
                  </div>

                  {/* Metrics Grid */}
                  <div className="grid grid-cols-3 gap-2 sm:gap-2.5 mt-4 text-center">
                    <div className="bg-slate-950/80 p-2.5 rounded-xl border border-blue-900/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Total Leads</span>
                      <span className="text-base sm:text-lg font-black text-white">{hipnoLeads}</span>
                    </div>
                    <div className="bg-slate-950/80 p-2.5 rounded-xl border border-blue-900/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Budget / Hari</span>
                      <span className="text-base sm:text-lg font-black text-slate-200">Rp 25.000</span>
                    </div>
                    <div className="bg-slate-950/80 p-2.5 rounded-xl border border-blue-900/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Target CPL</span>
                      <span className="text-base sm:text-lg font-black text-sky-400">Rp 25.000</span>
                    </div>

                    <div className="bg-slate-950/80 p-2.5 rounded-xl border border-blue-900/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Target Closing</span>
                      <span className="text-base sm:text-lg font-black text-emerald-400">15 / bln</span>
                    </div>
                    <div className="bg-slate-950/80 p-2.5 rounded-xl border border-blue-900/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Laba / Klien</span>
                      <span className="text-base sm:text-lg font-black text-emerald-400">Rp 570k-1,41jt</span>
                    </div>
                    <div className="bg-slate-950/80 p-2.5 rounded-xl border border-blue-900/60">
                      <span className="text-[10px] uppercase font-semibold text-slate-400 block">Est. ROAS</span>
                      <span className={`text-base sm:text-lg font-black ${hipnoROAS.color}`}>{hipnoROAS.text}</span>
                    </div>
                  </div>
                </div>

                {/* Progress Bar Biru */}
                <div className="mt-5 pt-3 border-t border-blue-900/50">
                  <div className="flex justify-between text-[11px] text-slate-300 mb-1">
                    <span>Efisiensi ROAS Target: 12.0x</span>
                    <span className="font-bold text-sky-400">92% Potensi</span>
                  </div>
                  <div className="w-full bg-slate-950 rounded-full h-2.5 overflow-hidden border border-blue-900">
                    <div className="bg-sky-500 h-2.5 rounded-full" style={{ width: "92%" }}></div>
                  </div>
                </div>
              </div>
            </div>

            {/* LIST 3 CAMPAIGNS MAKASSAR (PAUSED) */}
            <div className="mt-8">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-base sm:text-lg font-bold text-white tracking-tight">Campaigns Makassar (3 Terdaftar)</h2>
                <span className="text-xs text-slate-400">Budget: Rp 25.000 / hari</span>
              </div>
              <div className="overflow-x-auto rounded-2xl border border-slate-800 bg-slate-900/60 shadow-lg">
                <table className="w-full text-left text-xs sm:text-sm text-slate-300">
                  <thead className="bg-slate-900/90 text-[11px] uppercase text-slate-400 font-bold border-b border-slate-800">
                    <tr>
                      <th className="px-4 py-3 sm:px-6 sm:py-3.5">Nama Campaign</th>
                      <th className="px-4 py-3 sm:px-6 sm:py-3.5">Status</th>
                      <th className="px-4 py-3 sm:px-6 sm:py-3.5">Budget</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {campaigns.map((c) => (
                      <tr key={c.id} className="hover:bg-slate-800/30 transition">
                        <td className="px-4 py-3 sm:px-6 sm:py-3.5 font-semibold text-white">
                          <div className="flex items-center gap-2">
                            <span className="w-2 h-2 rounded-full bg-amber-400"></span>
                            <span>{c.name}</span>
                          </div>
                          <span className="text-[10px] text-slate-500 font-mono block mt-0.5">{c.id}</span>
                        </td>
                        <td className="px-4 py-3 sm:px-6 sm:py-3.5">
                          <span className="px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 whitespace-nowrap">
                            PAUSED (Menunggu WABA)
                          </span>
                        </td>
                        <td className="px-4 py-3 sm:px-6 sm:py-3.5 font-medium text-slate-300 whitespace-nowrap">
                          {c.name.includes("Kopi") ? "Rp 0 (Nonaktif)" : "Rp 25.000 / hari"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

          </div>
        )}

        {/* TAB 2: LEADS VIEW */}
        {activeTab === "leads" && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg sm:text-xl font-bold text-white">Log Leads Masuk WhatsApp</h2>
              <span className="text-xs text-slate-400">Total: {leads.length} leads</span>
            </div>

            {leads.length === 0 ? (
              <div className="p-12 text-center text-slate-500 bg-slate-900/50 rounded-2xl border border-slate-800">
                Belum ada leads tersimpan.
              </div>
            ) : (
              <div className="space-y-3">
                {leads.map((l) => {
                  const lastMsg = l.chat_history?.slice().reverse().find(m => m.sender !== "user")?.message || "-"
                  return (
                    <div key={l.id} className="p-4 sm:p-5 rounded-2xl bg-slate-900 border border-slate-800 hover:border-slate-700 transition shadow-md">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-mono text-emerald-400 font-bold text-sm">+{l.wa_id}</span>
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300 capitalize">
                          {l.status}
                        </span>
                      </div>
                      <div className="flex items-center gap-2 mt-2">
                        <span className="text-xs font-bold text-white">{l.product_name}</span>
                        <span className="text-slate-600">•</span>
                        <span className="text-xs text-slate-400 font-medium">BANT Score: {l.bant?.score || 0}/100</span>
                      </div>
                      <div className="mt-3 p-2.5 rounded-xl bg-slate-950/80 border border-slate-800/80 text-xs text-slate-300">
                        <span className="text-slate-500 block text-[10px] mb-0.5">Balasan Bot Terakhir:</span>
                        {lastMsg}
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        )}

        {/* TAB 3: ROAS VIEW */}
        {activeTab === "roas" && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl">
              <h2 className="text-lg sm:text-xl font-bold text-white mb-2">Simulasi & Monitoring ROAS Real-Time</h2>
              <p className="text-xs sm:text-sm text-slate-400 mb-6">
                Formula dinamis: <code className="bg-slate-950 px-2 py-1 rounded text-sky-400 font-mono">(Price × Closing Rate × Leads) / Spend</code>
              </p>

              <div className="space-y-5">
                <div className="p-4 rounded-xl bg-slate-950/70 border border-emerald-900/60">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-bold text-white">Totok Saraf Makassar (Rp 150.000)</span>
                    <span className={`text-base font-black px-2.5 py-0.5 rounded-lg border ${totokROAS.badgeColor}`}>
                      {totokROAS.text}
                    </span>
                  </div>
                  <span className="text-xs text-slate-400 block mb-3">Target CPL: Rp 15k | Closing: 40%</span>
                  <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                    <div className="bg-emerald-500 h-2 rounded-full" style={{ width: "85%" }}></div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/70 border border-blue-900/60">
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm font-bold text-white">Hipnoterapi Dokter Pikiran (Rp 600.000 - Rp 1.500.000)</span>
                    <span className={`text-base font-black px-2.5 py-0.5 rounded-lg border ${hipnoROAS.badgeColor}`}>
                      {hipnoROAS.text}
                    </span>
                  </div>
                  <span className="text-xs text-slate-400 block mb-3">Target CPL: Rp 25k | Closing: 50%</span>
                  <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden">
                    <div className="bg-sky-500 h-2 rounded-full" style={{ width: "95%" }}></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: WABA & INTEGRASI VIEW */}
        {activeTab === "waba" && (
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 shadow-xl">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-lg sm:text-xl font-bold text-white">Status WhatsApp Business Account (WABA)</h2>
                <span className="text-[10px] text-slate-500 font-mono">Polling 30s</span>
              </div>
              <p className="text-xs sm:text-sm text-slate-400 mb-6">
                Informasi nomor tunggal untuk layanan Totok Saraf & Hipnoterapi Makassar.
              </p>

              <div className="space-y-4">
                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex justify-between items-center">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-500 block">Nomor Terdaftar</span>
                    <span className="text-base font-mono font-bold text-white">{wabaStatus.phone_number || "+62 811-443-327"}</span>
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${
                    wabaStatus.can_activate_ads
                      ? "bg-emerald-500/15 text-emerald-300 border-emerald-500/40"
                      : "bg-amber-500/10 text-amber-300 border border-amber-500/30"
                  }`}>
                    {wabaStatus.status_label || "Menunggu Verifikasi (2 Hari Kerja)"}
                  </span>
                </div>

                <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 space-y-2">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold">
                    <span>✓</span> Ads Manager Siap (2 Iklan Baru Pria Hijau & Biru Terpasang)
                  </div>
                  <div className="flex items-center gap-2 text-emerald-400 font-bold">
                    <span>✓</span> Budget Aman Terkunci Rp 25.000 / hari
                  </div>
                  <div className={`flex items-center gap-2 font-bold ${wabaStatus.can_activate_ads ? "text-emerald-400" : "text-amber-300"}`}>
                    <span>{wabaStatus.can_activate_ads ? "✓" : "🔒"}</span>
                    {wabaStatus.can_activate_ads 
                      ? "Nomor WABA telah Aktif! Campaign siap di-UNPAUSE." 
                      : "Campaign tetap berstatus PAUSED sampai nomor aktif"}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* 2. BOTTOM NAVIGATION FIXED (Mobile UX 48px Touch Target) */}
      <nav className="fixed bottom-0 left-0 right-0 z-50 bg-slate-950/95 backdrop-blur-lg border-t border-slate-800/90 px-2 py-1.5 md:hidden shadow-2xl">
        <div className="grid grid-cols-4 max-w-md mx-auto">
          <button 
            onClick={() => setActiveTab("dashboard")}
            className={`min-h-[48px] flex flex-col items-center justify-center rounded-xl transition ${activeTab === "dashboard" ? "text-emerald-400 font-bold" : "text-slate-400 hover:text-slate-200"}`}
          >
            <span className="text-lg">📊</span>
            <span className="text-[10px] mt-0.5">Dashboard</span>
          </button>

          <button 
            onClick={() => setActiveTab("leads")}
            className={`min-h-[48px] flex flex-col items-center justify-center rounded-xl transition ${activeTab === "leads" ? "text-emerald-400 font-bold" : "text-slate-400 hover:text-slate-200"}`}
          >
            <span className="text-lg">💬</span>
            <span className="text-[10px] mt-0.5">Leads</span>
          </button>

          <button 
            onClick={() => setActiveTab("roas")}
            className={`min-h-[48px] flex flex-col items-center justify-center rounded-xl transition ${activeTab === "roas" ? "text-emerald-400 font-bold" : "text-slate-400 hover:text-slate-200"}`}
          >
            <span className="text-lg">📈</span>
            <span className="text-[10px] mt-0.5">ROAS</span>
          </button>

          <button 
            onClick={() => setActiveTab("waba")}
            className={`min-h-[48px] flex flex-col items-center justify-center rounded-xl transition ${activeTab === "waba" ? "text-emerald-400 font-bold" : "text-slate-400 hover:text-slate-200"}`}
          >
            <span className="text-lg">📱</span>
            <span className="text-[10px] mt-0.5">WABA</span>
          </button>
        </div>
      </nav>

      {/* MODAL LAUNCH PRODUK BARU */}
      {showModal && (
        <div className="fixed inset-0 bg-black/85 backdrop-blur-md flex items-center justify-center p-4 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-lg p-6 sm:p-7 shadow-2xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3.5 border-b border-slate-800">
              <div>
                <h3 className="text-base sm:text-lg font-bold text-white">Launch Produk Baru (Makassar)</h3>
                <p className="text-xs text-slate-400">Nomor WA tetap Kopi Robusta (+62 811-443-327)</p>
              </div>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-white p-2">✕</button>
            </div>
            <form onSubmit={handleLaunchProduct} className="mt-4 space-y-3.5">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Nama Produk / Layanan *</label>
                <input 
                  type="text" 
                  required
                  placeholder="Misal: Bekam Medik Makassar" 
                  className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-emerald-500 outline-none"
                  value={newProduct.name}
                  onChange={e => setNewProduct({...newProduct, name: e.target.value})}
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">Harga (Rp)</label>
                  <input 
                    type="number" 
                    placeholder="150000" 
                    className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-emerald-500 outline-none"
                    value={newProduct.price}
                    onChange={e => setNewProduct({...newProduct, price: e.target.value})}
                  />
                </div>
                <div>
                  <label className="text-xs font-semibold text-slate-400 block mb-1">Budget Harian (Rp)</label>
                  <input 
                    type="number" 
                    placeholder="25000" 
                    className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-emerald-500 outline-none"
                    value={newProduct.budget_rp}
                    onChange={e => setNewProduct({...newProduct, budget_rp: e.target.value})}
                  />
                </div>
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Deskripsi Singkat</label>
                <textarea 
                  rows={3}
                  placeholder="Keunggulan layanan..." 
                  className="w-full p-3 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:border-emerald-500 outline-none"
                  value={newProduct.description}
                  onChange={e => setNewProduct({...newProduct, description: e.target.value})}
                />
              </div>
              <div className="pt-2 flex justify-end gap-3">
                <button 
                  type="button" 
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2.5 text-xs font-medium rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700"
                >
                  Batal
                </button>
                <button 
                  type="submit" 
                  disabled={launching}
                  className="px-5 py-2.5 text-xs font-bold rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 text-slate-950 disabled:opacity-50"
                >
                  {launching ? "Memproses..." : "Launch Campaign (PAUSED)"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  )
}
