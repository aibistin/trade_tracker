<template>
  <div>
    <h1>Stock Trading App - Home</h1>
    <p>Select a stock symbol from the dropdown to view its trades.</p>

    <!-- Dropdown for Stock Symbols -->
    <div class="mb-3">
      <label for="stockSymbol" class="form-label">Select a Stock:</label>
      <select v-model="selectedSymbol" class="form-select" id="stockSymbol" @change="navigateToTrades">
        <option value="" disabled>Select a stock symbol</option>
        <option v-for="[symbol, name] in stockSymbols" :key="symbol" :value="symbol">
          {{ symbol }} - {{ name }}
        </option>
      </select>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
      <p class="mt-2">Loading stock symbols...</p>
    </div>

    <!-- Error State -->
    <div v-if="error" class="alert alert-danger">
      Error loading stock symbols: {{ error }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRouter } from 'vue-router';
import { useFetchTrades } from '../composables/useFetchTrades';

const router = useRouter();
const allSymbolsApiUrl = ref('http://localhost:5000/trade/symbols_json');
const selectedSymbol = ref(null);

console.log(`[Home->Init] useFetchTrades`);
const { data: stockSymbols, loading, error, fetchData } = useFetchTrades();

onMounted(() => {
  console.log(`[home->onMounted] Calling API: ${allSymbolsApiUrl.value}`);
  fetchData(allSymbolsApiUrl);
});

const navigateToTrades = () => {
  if (selectedSymbol.value) {
    router.push(`/trades/all/${selectedSymbol.value}`);
  }
};
</script>

<style scoped>
.form-select {
  max-width: 400px;
  margin: 0 auto;
}
</style>