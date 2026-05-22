import { Routes, Route } from 'react-router-dom';
import Layout from '@/components/Layout';
import Home from '@/pages/Home';
import Sentiment from '@/pages/Sentiment';
import IntradayMonitor from '@/pages/IntradayMonitor';
import Yingyou from '@/pages/Yingyou';
import Tactics from '@/pages/Tactics';
import Scoring from '@/pages/Scoring';
import Diagnosis from '@/pages/Diagnosis';
import StockDetail from '@/pages/StockDetail';
import News from '@/pages/News';
import TradeJournal from '@/pages/TradeJournal';
import TradeHistory from '@/pages/TradeHistory';
import TradeEnvironment from '@/pages/TradeEnvironment';
import RealtimeDemo from '@/pages/RealtimeDemo';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/sentiment" element={<Sentiment />} />
        <Route path="/intraday" element={<IntradayMonitor />} />
        <Route path="/yingyou" element={<Yingyou />} />
        <Route path="/tactics" element={<Tactics />} />
        <Route path="/scoring" element={<Scoring />} />
        <Route path="/diagnosis" element={<Diagnosis />} />
        <Route path="/news" element={<News />} />
        <Route path="/stock/:code" element={<StockDetail />} />
        <Route path="/trade-journal" element={<TradeJournal />} />
        <Route path="/trade-history" element={<TradeHistory />} />
        <Route path="/trade-environment/:id" element={<TradeEnvironment />} />
        <Route path="/realtime-demo" element={<RealtimeDemo />} />
      </Routes>
    </Layout>
  );
}
