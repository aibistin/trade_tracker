import { ref } from "vue";
import axios from "axios";

export function useFetchTrades() {
  const data = ref(null);
  const loading = ref(false);
  const error = ref(null);
  console.log(`[useFetchTrades->Init] Caller: `);
  console.log(new Error().stack?.split("\n")[2]?.trim().split(" ")[1]);

  const fetchData = async (apiUrl) => {
    console.log(`[useFetchTrades->fetchData] Calling: ${apiUrl.value}`);
    console.log(`[useFetchTrades->fetchData] Caller: `);
    console.log(new Error().stack?.split("\n")[2]?.trim().split(" ")[1]);
    try {
      loading.value = true;
      error.value = null;
      const response = await axios.get(`${apiUrl.value}`, {
        headers: { Accept: "application/json" },
        timeout: 5000,
      });
      // if (!response.data?.stock_symbol && stockSymbol?.value) {
      // throw new Error(`Invalid data format from API - No data for stock: ${stockSymbol.value}`);
      // }
      data.value = response.data;
      console.log(
        `[useFetchTrades->fetchData] URL: ${apiUrl.value} Data fetched:`,
        data.value
      );
    } catch (err) {
      error.value = err.message || `Failed to fetch trades, URL: ${apiUrl.value}`;
      data.value = null;
    } finally {
      loading.value = false;
    }
  };

  return {
    data,
    loading,
    error,
    fetchData,
  };
}
