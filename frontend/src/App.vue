<script setup>
// import { ref, onMounted, inject, watch } from "vue";
import { onMounted, inject } from "vue";
import AppContainer from "./views/AppContainer.vue";
// import AllTrades from './views/AllTrades.vue';
import BSNavBarTop from "./components/BSNavBarTop.vue";

// Inject Bootstrap
const bootstrap = inject("bootstrap");

// State for the component
// const selectedTicker = ref('ALAB'); // Default ticker
// const showOpenTrades = ref(true); // Toggle between open trades and all trades
// const openTradesUrl = 'http://localhost:5000/open_trades_json'; // API URL for open trades
// const allTradesUrl = 'http://localhost:5000/trade/transactions_json'; // API URL for all trades

/* Debug: Log when showOpenTrades changes */
// watch(showOpenTrades, (newValue) => {
//   console.log('showOpenTrades changed:', newValue);
// });

onMounted(() => {
  try {
    // Expanding the navbar
    const collapse = new bootstrap.Collapse("#navbarSupportedContent");
    collapse.show();
    console.count("App mounted");
    // "https://getbootstrap.com/docs/5.3/components/tooltips/#enable-tooltips"
    // const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
    // const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))
  } catch (e) {
    console.log("Bootstrap error: ", e);
  }
});

</script>


<template>
  <app-container>
    <header class="row">
      <BSNavBarTop />
    </header>
    <main class="row">
      <div class="col">
        <!-- Router View -->
        <router-view></router-view>
      </div>
    </main>
  </app-container>
</template>


<!-- <template>
  <app-container>
    <header class="row">
      <BSNavBarTop />
    </header>
    <main class="row">
      <div class="col">
        <div class="mb-3">
          <button @click="showOpenTrades = true" :class="[
            'btn',
            'me-2',
            showOpenTrades ? 'btn-primary' : 'btn-outline-primary',
          ]">
            Open Trades
          </button>
          <button @click="showOpenTrades = false" :class="[
            'btn',
            showOpenTrades ? 'btn-outline-primary' : 'btn-primary',
          ]">
            All Trades
          </button>
        </div>
        <AllTrades :stockSymbol="selectedTicker" :apiUrl="showOpenTrades ? openTradesUrl : allTradesUrl" />
      </div>
    </main>
  </app-container>
</template> -->

<style scoped>
.btn {
  transition: all 0.3s ease;
}
</style>