<template>
  <nav class="navbar navbar-expand-lg bg-body-tertiary">
    <div class="container-fluid">
      <router-link class="navbar-brand" to="/home">Trade Track</router-link>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>

      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <router-link class="nav-link active" aria-current="page" to="/home">Home</router-link>
          </li>

          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
              All Trades
            </a>
            <ul class="dropdown-menu">
              <li v-for="[symbol, name] in currentStockSymbols" :key="symbol">
                <router-link class="dropdown-item" :to="`/trades/all/${symbol}`">
                  {{ symbol }} - {{ name }}
                </router-link>
              </li>
            </ul>
          </li>

          <li class="nav-item dropdown" size="3">
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
              Open Trades
            </a>
            <ul class="dropdown-menu">
              <li v-for="[symbol, name] in currentStockSymbols" :key="symbol">
                <router-link class="dropdown-item" @click="logNavigation(symbol, 'to')" :to="`/trades/open/${symbol}`">
                  {{ symbol }} - {{ name }}
                </router-link>
              </li>
            </ul>
          </li>
          <li class="nav-item dropdown" size="3">
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
              Closed Trades
            </a>
            <ul class="dropdown-menu">
              <li v-for="[symbol, name] in currentStockSymbols" :key="symbol">
                <router-link class="dropdown-item"                  :to="`/trades/closed/${symbol}`">
                  {{ symbol }} - {{ name }}
                </router-link>
              </li>
            </ul>
          </li>
        </ul>

        <form class="d-flex" role="search">
          <input v-model="searchQuery" type="text" class="form-control" placeholder="View All Trades for ..."
            @input="filterSymbols" @focus="isDropdownOpen = true" />
          <!-- Dropdown Menu -->
          <ul v-if="isDropdownOpen" class="dropdown-menu show"
            style="width: 100%; max-height: 300px; overflow-y: auto;">
            <li v-for="[symbol, name] in filteredSymbols" :key="symbol">
              <a class="dropdown-item btn-outline-success" href="#" @click="selectAllTradesSymbol(symbol, 'all')">
                {{ symbol }} - {{ name }}
              </a>
            </li>
            <li v-if="filteredSymbols.length === 0">
              <a class="dropdown-item disabled">No matching symbols found</a>
            </li>
          </ul>
        </form>

      </div>
    </div>
  </nav>

  <!-- Loading State -->
  <div v-if="loading" class="text-center py-4">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Loading all symbols...</span>
    </div>
    <p class="mt-2">Loading all stock symbols...</p>
  </div>

  <div v-if="currentLoading" class="text-center py-4">
    <div class="spinner-border text-primary" role="status">
      <span class="visually-hidden">Loading current symbols...</span>
    </div>
    <p class="mt-2">Loading current stock symbols...</p>
  </div>

  <!-- Error State -->
  <div v-if="error" class="alert alert-danger">
    Error loading all stock symbols: {{ error }}
  </div>
  <!-- Error State -->
  <div v-if="currentError" class="alert alert-danger">
    Error loading open stock symbols: {{ error }}
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useFetchTrades } from '../composables/useFetchTrades';
import { useSymbolSearch } from '../composables/useSymbolSearch';
import { API_BASE_URL } from '@/config.js';

const allSymbolsApiUrl = ref(`${API_BASE_URL}/trade/symbols_json`);
const currentSymbolsApiUrl = ref(`${API_BASE_URL}/trade/current_holdings_symbols_json`);

const { data: stockSymbols, loading, error, fetchData } = useFetchTrades();
const { data: currentStockSymbols, loading: currentLoading, error: currentError, fetchData: fetchCurrentSymbols } = useFetchTrades();
const { searchQuery, isDropdownOpen, filteredSymbols, selectSymbol: selectAllTradesSymbol } = useSymbolSearch(stockSymbols);

onMounted(() => {
  fetchData(allSymbolsApiUrl);
  fetchCurrentSymbols(currentSymbolsApiUrl);
});
</script>

<style scoped>
.navbar {
  margin-bottom: 20px;
}
</style>
