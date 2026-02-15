import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';

export function useSymbolSearch(symbols) {
  const searchQuery = ref('');
  const isDropdownOpen = ref(false);
  const router = useRouter();

  const filteredSymbols = computed(() => {
    if (!searchQuery.value) {
      return symbols.value;
    }
    const query = searchQuery.value.toLowerCase();
    return symbols.value.filter(([symbol, name]) => {
      return (
        symbol.toLowerCase().includes(query) ||
        name.toLowerCase().includes(query)
      );
    });
  });

  const selectSymbol = (symbol, scope = 'all') => {
    searchQuery.value = '';
    isDropdownOpen.value = false;
    router.push(`/trades/${scope}/${symbol}`);
  };

  return {
    searchQuery,
    isDropdownOpen,
    filteredSymbols,
    selectSymbol,
  };
}
