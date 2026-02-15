import { ref } from "vue";
import axios from "axios";

export function useFetchTrades() {
  const data = ref(null);
  const loading = ref(false);
  const error = ref(null);

  const fetchData = async (apiUrl) => {
    try {
      loading.value = true;
      error.value = null;
      const response = await axios.get(`${apiUrl.value}`, {
        headers: { Accept: "application/json" },
        timeout: 5000,
      });
      data.value = response.data;
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
