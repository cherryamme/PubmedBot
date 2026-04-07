import SearchBar from '../components/search/SearchBar';
import ResultsList from '../components/results/ResultsList';

export default function HomePage() {
  return (
    <div className="space-y-4">
      <SearchBar />
      <ResultsList />
    </div>
  );
}
