<!-- New Way  -->
<template>
  <div>
    <h1>Stock Trading App - Home</h1>
    <p>Select a stock symbol from the dropdown to view its trades.</p>

    <!-- Custom Dropdown for Stock Symbols -->
    <div class="mb-3">
      <label for="stockSymbol" class="form-label">Select a Stock:</label>
      <div class="dropdown">
        <!-- Search Input -->
        <input v-model="searchQuery" type="text" class="form-control" placeholder="Type to search..."
          @input="filterSymbols" @focus="isDropdownOpen = true" />
        <!-- Dropdown Menu -->
        <ul v-if="isDropdownOpen" class="dropdown-menu show" style="width: 100%; max-height: 300px; overflow-y: auto;">
          <li v-for="[symbol, name] in filteredSymbols" :key="symbol">
            <a class="dropdown-item" href="#" @click="selectSymbol(symbol)">
              {{ symbol }} - {{ name }}
            </a>
          </li>
          <li v-if="filteredSymbols.length === 0">
            <a class="dropdown-item disabled">No matching symbols found</a>
          </li>
        </ul>
      </div>
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
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useFetchTrades } from '../composables/useFetchTrades';
const allSymbolsApiUrl = ref('http://localhost:5000/api/trade/symbols_json');
const searchQuery = ref('');
const isDropdownOpen = ref(false);
const router = useRouter();

console.log(`[Home->Init] useFetchTrades to get stockSymbols`);
const { data: stockSymbols, loading, error, fetchData } = useFetchTrades();

console.log("[Home->Init] error: ",error);
console.log(`[Home->Init] stockSymbols: ${JSON.stringify(stockSymbols.value?.slice(0, 3) , null, 2)}`);

// Filter symbols based on search query
const filteredSymbols = computed(() => {

  if (!searchQuery.value) {
    return stockSymbols.value;
  }
 
  const query = searchQuery.value.toLowerCase();
  return stockSymbols.value.filter(([symbol, name]) => {
    console.log("symbol: ", symbol, "name: ", name);
    return (
      symbol.toLowerCase().includes(query) ||
      name.toLowerCase().includes(query)
    );
  });

});

// Handle symbol selection
const selectSymbol = (symbol) => {
  searchQuery.value = ''; // Clear the search query
  isDropdownOpen.value = false; // Close the dropdown
  router.push(`/trades/all/${symbol}`);
};


onMounted(() => {
  console.log(`[home->onMounted] Calling API: ${allSymbolsApiUrl.value}`);
  fetchData(allSymbolsApiUrl);
});

</script>


<style scoped>
.dropdown {
  position: relative;
}

.dropdown-menu {
  display: none;
  position: absolute;
  top: 100%;
  left: 0;
  z-index: 1000;
  background-color: white;
  border: 1px solid rgba(0, 0, 0, 0.15);
  border-radius: 0.25rem;
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.175);
}

.dropdown-menu.show {
  display: block;
}

.dropdown-item {
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

.dropdown-item.disabled {
  color: #6c757d;
  pointer-events: none;
}
</style>
