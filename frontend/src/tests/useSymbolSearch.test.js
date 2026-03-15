import { describe, it, expect, vi } from 'vitest';
import { useSymbolSearch } from '@/composables/useSymbolSearch.js';

// Mock vue-router
const mockPush = vi.fn();
vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
  useRoute: () => ({ query: { asset_type: 'stock' } }),
}));

describe('useSymbolSearch', () => {
  it('navigates to the all scope for a symbol by default', () => {
    const { selectSymbol } = useSymbolSearch();
    selectSymbol('AAPL');
    expect(mockPush).toHaveBeenCalledWith({
      path: '/trades/all/AAPL',
      query: { asset_type: 'stock' },
    });
  });

  it('navigates to the specified scope', () => {
    const { selectSymbol } = useSymbolSearch();
    selectSymbol('MSFT', 'open');
    expect(mockPush).toHaveBeenCalledWith({
      path: '/trades/open/MSFT',
      query: { asset_type: 'stock' },
    });
  });

  it('preserves existing route query params on navigation', () => {
    const { selectSymbol } = useSymbolSearch();
    selectSymbol('TSLA', 'closed');
    expect(mockPush).toHaveBeenCalledWith(
      expect.objectContaining({ query: { asset_type: 'stock' } })
    );
  });
});
