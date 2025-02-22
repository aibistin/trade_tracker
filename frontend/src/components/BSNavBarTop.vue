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
              <li v-for="[symbol, name] in stockSymbols" :key="symbol">
                <router-link class="dropdown-item" @click="logNavigation(symbol, 'all')" :to="`/trades/all/${symbol}`">
                  {{ symbol }} - {{ name }}
                </router-link>
              </li>
            </ul>
          </li>


          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
              Open Trades
            </a>
            <ul class="dropdown-menu">
              <li v-for="[symbol, name] in stockSymbols" :key="symbol">
                <router-link class="dropdown-item" @click="logNavigation(symbol, 'to')" :to="`/trades/open/${symbol}`">
                  {{ symbol }} - {{ name }}
                </router-link>
              </li>
            </ul>
          </li>
          <li class="nav-item">
            <router-link class="nav-link disabled" to="/trades/closed" aria-disabled="true">Closed Trades</router-link>
          </li>
        </ul>
        <form class="d-flex disabled" role="search">
          <input class="form-control me-2 disabled" type="search" placeholder="Search" aria-label="Search"
            aria-disabled="true" />
          <button class="btn btn-outline-success disabled" type="submit">Search</button>
        </form>
      </div>
    </div>
  </nav>

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
</template>

<script setup>
import { onMounted, ref } from 'vue';
import { useFetchTrades } from '../composables/useFetchTrades';
const allSymbolsApiUrl = ref('http://localhost:5000/trade/symbols_json');

// Create the useFetchTrades composable for fetching stock symbols
console.log(`[BSNavBarTop->Init] Creating useFetchTrades`);
const { data: stockSymbols, loading, error, fetchData } = useFetchTrades();

// Fetch data when the component mounts
onMounted(() => {
  console.log(`[BSNavBarTop->onMounted] fetchData with ${allSymbolsApiUrl.value}`);
  fetchData(allSymbolsApiUrl);
});


const logNavigation = (symbol, type) => {
  console.log(`Navigating to ${type} trades for symbol: ${symbol}`);
};

</script>

<style scoped>
.navbar {
  margin-bottom: 20px;
}
</style>


<!-- <template> -->
<!-- Programatically  -->
<!-- <li class="nav-item dropdown">
            <a
              class="nav-link dropdown-toggle"
              href="#"
              role="button"
              data-bs-toggle="dropdown"
              aria-expanded="false"
            >
              Open Trades Pg
            </a>
            <ul class="dropdown-menu">
              <li v-for="[symbol, name] in stockSymbols" :key="symbol">
                <a
                  class="dropdown-item"
                  href="#"
                  @click="navigateToOpenTrades(symbol)"
                >
                  {{ symbol }} - {{ name }}
                </a>
              </li>
            </ul>
          </li> -->
<!-- End Programatically  -->
<!-- </template> -->


<!-- 
<template>
  <nav class="navbar navbar-expand-lg bg-body-tertiary">
  <div class="container-fluid">
    <a class="navbar-brand" href="#">Trade Track</a>
    <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent" aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
      <span class="navbar-toggler-icon"></span>
    </button>
    <div class="collapse navbar-collapse" id="navbarSupportedContent">
      <ul class="navbar-nav me-auto mb-2 mb-lg-0">
        <li class="nav-item">
            <router-link class="nav-link active" aria-current="page" to="/home">Home</router-link>
        </li>
        <li>
            <router-link class="nav-link" :to="{
              path: '/trades/all/ALAB',
            }">
              All Trades
            </router-link>
        </li>
        <li>
            <router-link class="nav-link" :to="{
              path: '/trades/open/NNE',
            }">
              Open Trades
            </router-link>
        </li>
        <li class="nav-item">
            <router-link class="nav-link disabled" to="/all_closed_trades" aria-disabled="true">Closed Trades</router-link>
        </li>
        <li class="nav-item dropdown">
          <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false">
            Dropdown
          </a>
          <ul class="dropdown-menu">
            <li><router-link class="dropdown-item" to="/home">Home</router-link></li>
            <li><router-link class="dropdown-item" to="/trades/all/DOCS">All Trades</router-link></li>
            <li><router-link class="dropdown-item" to="/trades/open/DOCS">Open Trades</router-link></li>
            <li><a class="dropdown-item" href="#">Another action</a></li>
            <li><hr class="dropdown-divider"></li>
            <li><a class="dropdown-item" href="#">Something else here</a></li>
          </ul>
        </li>
      </ul>
      <form class="d-flex disabled" role="search">
        <input class="form-control me-2 disabled" type="search" placeholder="Search" aria-label="Search" aria-disabled="true">
        <button class="btn btn-outline-success disabled" type="submit">Search</button>
      </form>
    </div>
  </div>
</nav>
</template> -->

<!-- <template>
  <nav class="navbar navbar-expand-lg navbar-light bg-light">
    <div class="container-fluid">
      <router-link class="navbar-brand" to="/home">Stock Trading App</router-link>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarSupportedContent"
        aria-controls="navbarSupportedContent" aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="navbarSupportedContent">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          <li class="nav-item">
            <router-link class="nav-link" to="/home">Home</router-link>
          </li>
          <li>
            <router-link class="nav-link" :to="{
              path: '/trades/all/ALAB',
            }">
              All Trades
            </router-link>
          </li>
          <li>
            <router-link class="nav-link" :to="{
              path: '/trades/open/NNE',
            }">
              Open Trades
            </router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/all_closed_trades">Closed Trades</router-link>
          </li>
        </ul>
      </div>
    </div>
  </nav>
</template>

<script setup>
// No script logic needed for BSNavBarTop.vue in this setup
console.count("BSNavBarTop.vue: Component! ");
</script>

<style scoped>
.navbar {
  margin-bottom: 20px;
}
</style>
-->