import { useParams } from 'react-router-dom';

export default function StockDetail() {
  const { code } = useParams<{ code: string }>();

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <img src="/empty-state.png" alt="" className="w-60 h-44 object-contain mb-6 opacity-50" />
      <h2 className="text-2xl font-semibold text-[#f1f5f9] mb-2">个股详情</h2>
      <p className="text-[#475569]">股票代码: <span className="font-mono text-[#c9a84c]">{code}</span></p>
    </div>
  );
}
