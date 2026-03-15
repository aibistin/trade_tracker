import { useRouter, useRoute } from 'vue-router';

export function useSymbolSearch() {
  const router = useRouter();
  const route = useRoute();

  const selectSymbol = (symbol, scope = 'all') => {
    router.push({ path: `/trades/${scope}/${symbol}`, query: route.query });
  };

  return { selectSymbol };
}
