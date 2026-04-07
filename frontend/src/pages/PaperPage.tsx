import { useParams, useNavigate } from 'react-router-dom';
import PaperDetail from '../components/detail/PaperDetail';

export default function PaperPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  if (!id) return null;

  return (
    <PaperDetail paperId={Number(id)} onBack={() => navigate(-1)} />
  );
}
