import React, { useEffect, useState } from "react";

type NavInfo = {
  total: number;
  spot: number;
  fut: number;
};

type Position = {
  id: number;
  symbol: string;
  side: string;
  qty: number;
  sl: number;
  tp: number;
  status: string;
  updated_at: string;
};

type Order = {
  symbol: string;
  score: number;
  action: string;
  atr_pct: number;
  expected_return: number;
};

const Dashboard: React.FC = () => {
  const [nav, setNav] = useState<NavInfo>({ total: 0, spot: 0, fut: 0 });
  const [positions, setPositions] = useState<Position[]>([]);
  const [signals, setSignals] = useState<Record<string, Order[]>>({ SPOT: [], FUT: [] });
  const [alerts, setAlerts] = useState<string[]>([]);

  useEffect(() => {
    async function fetchData() {
      const statusRes = await fetch("/api/v1/status");
      const status = await statusRes.json();
      setNav(status.account);
      setPositions(status.positions);
      const signalsRes = await fetch("/api/v1/signals/recent");
      const signalsJson = await signalsRes.json();
      setSignals(signalsJson);
    }
    fetchData();
    const interval = setInterval(fetchData, 60_000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-white p-8">
      <h1 className="text-3xl font-bold mb-6">Trading Bot Dashboard</h1>
      <section className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-900 rounded-xl p-4">
          <h2 className="text-lg text-gray-400">Tổng NAV</h2>
          <p className="text-2xl font-semibold">${nav.total.toFixed(2)}</p>
        </div>
        <div className="bg-gray-900 rounded-xl p-4">
          <h2 className="text-lg text-gray-400">Spot NAV</h2>
          <p className="text-2xl font-semibold">${nav.spot.toFixed(2)}</p>
        </div>
        <div className="bg-gray-900 rounded-xl p-4">
          <h2 className="text-lg text-gray-400">Futures NAV</h2>
          <p className="text-2xl font-semibold">${nav.fut.toFixed(2)}</p>
        </div>
      </section>
      <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-gray-900 rounded-xl p-4">
          <h2 className="text-xl font-semibold mb-3">Vị thế hiện tại</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400">
                <th>Symbol</th>
                <th>Side</th>
                <th>Qty</th>
                <th>SL</th>
                <th>TP</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {positions.map((pos) => (
                <tr key={pos.id} className="border-t border-gray-800">
                  <td className="py-2">{pos.symbol}</td>
                  <td>{pos.side}</td>
                  <td>{pos.qty.toFixed(4)}</td>
                  <td>{pos.sl.toFixed(2)}</td>
                  <td>{pos.tp.toFixed(2)}</td>
                  <td>{pos.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="bg-gray-900 rounded-xl p-4">
          <h2 className="text-xl font-semibold mb-3">Tín hiệu mới</h2>
          {(["SPOT", "FUT"] as const).map((type) => (
            <div key={type} className="mb-4">
              <h3 className="text-gray-400 text-sm mb-2">{type}</h3>
              <div className="space-y-2">
                {signals[type]?.map((sig, idx) => (
                  <div key={idx} className="border border-gray-800 rounded-lg p-2">
                    <div className="flex justify-between">
                      <span className="font-semibold">{sig.symbol}</span>
                      <span className="text-xs text-gray-400">{sig.action}</span>
                    </div>
                    <div className="text-xs text-gray-400">
                      Score: {sig.score.toFixed(2)} | ATR%: {sig.atr_pct.toFixed(2)} |
                      Exp: {(sig.expected_return * 100).toFixed(2)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default Dashboard;
