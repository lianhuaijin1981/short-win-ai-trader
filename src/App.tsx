import { Routes, Route } from 'react-router-dom';
import Layout from '@/components/Layout';
import Home from '@/pages/Home';
import Sentiment from '@/pages/Sentiment';
import Intraday from '@/pages/Intraday';
import Yingyou from '@/pages/Yingyou';
import Tactics from '@/pages/Tactics';
import Scoring from '@/pages/Scoring';
import Diagnosis from '@/pages/Diagnosis';
import StockDetail from '@/pages/StockDetail';

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/sentiment" element={<Sentiment />} />
        <Route path="/intraday" element={<Intraday />} />
        <Route path="/yingyou" element={<Yingyou />} />
        <Route path="/tactics" element={<Tactics />} />
        <Route path="/scoring" element={<Scoring />} />
        <Route path="/diagnosis" element={<Diagnosis />} />
        <Route path="/stock/:code" element={<StockDetail />} />
      </Routes>
    </Layout>
  );
}
