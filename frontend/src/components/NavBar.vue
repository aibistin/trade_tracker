<template>
  <nav class="navbar">
    <div class="navbar-inner">
      <!-- Brand -->
      <router-link class="navbar-brand" to="/dashboard">
        &#9650; Trade Tracker
      </router-link>

      <!-- Nav Links -->
      <div class="navbar-links">
        <router-link class="nav-link" to="/dashboard">Dashboard</router-link>
        <router-link class="nav-link" to="/history">History</router-link>

        <!-- Symbols Dropdown (click-based) -->
        <div class="nav-dropdown" ref="dropdownRef">
          <button class="nav-link nav-dropdown-trigger" @click="toggleSymbols">
            Symbols <span class="dropdown-arrow">{{ showSymbols ? '▲' : '▼' }}</span>
          </button>
          <div v-if="showSymbols" class="dropdown-menu symbols-menu">
            <router-link
              v-for="[symbol, name] in symbolsList"
              :key="symbol"
              class="dropdown-item"
              :to="{ path: `/trades/${activeScope}/${symbol}`, query: route.query }"
              @click="showSymbols = false"
            >
              <span class="dropdown-symbol">{{ symbol }}</span>
              <span class="dropdown-name">{{ name }}</span>
            </router-link>
            <div v-if="!symbolsList.length" class="dropdown-item text-muted">Loading...</div>
          </div>
        </div>

        <!-- Scope Toggle (trade views only) -->
        <div v-if="isTradeView" class="nav-toggle-group">
          <div class="btn-group btn-group-sm">
            <button v-for="s in scopes" :key="s.value"
              class="btn" :class="activeScope === s.value ? 'btn-primary' : 'btn-outline-primary'"
              @click="setScope(s.value)">
              {{ s.label }}
            </button>
          </div>
        </div>

        <!-- Asset Type Toggle (trade views only) -->
        <div v-if="isTradeView" class="nav-toggle-group">
          <div class="btn-group btn-group-sm">
            <button v-for="t in assetTypes" :key="t.value"
              class="btn" :class="activeAssetType === t.value ? 'btn-success' : 'btn-outline-success'"
              @click="setAssetType(t.value)">
              {{ t.label }}
            </button>
          </div>
        </div>
      </div>

      <!-- Search -->
      <SymbolSearchDropdown
        :symbols="stockSymbols ?? []"
        placeholder="Search symbols..."
        @select="selectSymbolWithScope"
      />

      <SyncButton v-if="!isTradeView" />
    </div>
  </nav>

  <div v-if="loading" class="nav-status">Loading symbols...</div>
  <div v-if="error" class="nav-error">Error loading symbols: {{ error }}</div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useFetchTrades } from '@/composables/useFetchTrades.js';
import { useSymbolSearch } from '@/composables/useSymbolSearch.js';
import { API_BASE_URL } from '@/config.js';
import SymbolSearchDropdown from './SymbolSearchDropdown.vue';
import SyncButton from './SyncButton.vue';

const route = useRoute();
const router = useRouter();
const showSymbols = ref(false);
const dropdownRef = ref(null);

const scopes = [
  { value: 'all', label: 'All' },
  { value: 'open', label: 'Open' },
  { value: 'closed', label: 'Closed' },
];

const assetTypes = [
  { value: 'all', label: 'All' },
  { value: 'stock', label: 'Stock' },
  { value: 'option', label: 'Option' },
];

const isTradeView = computed(() => !['Dashboard', 'History'].includes(route.name));
const activeScope = computed(() => route.params.scope || 'all');
const activeAssetType = computed(() => route.query.asset_type || 'all');

// Use all traded symbols for the dropdown (not just current holdings)
const { data: stockSymbols, loading, error, fetchData } = useFetchTrades();

// symbolsList: all symbols as [symbol, name] pairs, sorted alphabetically
const symbolsList = computed(() => {
  if (!stockSymbols.value?.length) return [];
  return [...stockSymbols.value].sort((a, b) => a[0].localeCompare(b[0]));
});

const { selectSymbol } = useSymbolSearch();
const selectSymbolWithScope = (symbol) => {
  showSymbols.value = false;
  selectSymbol(symbol, activeScope.value);
};

function toggleSymbols() {
  showSymbols.value = !showSymbols.value;
}

// Close dropdown when clicking outside
function handleOutsideClick(e) {
  if (dropdownRef.value && !dropdownRef.value.contains(e.target)) {
    showSymbols.value = false;
  }
}

onMounted(() => {
  fetchData(`${API_BASE_URL}/trade/symbols_json`);
  document.addEventListener('click', handleOutsideClick);
});

onBeforeUnmount(() => {
  document.removeEventListener('click', handleOutsideClick);
});

const setScope = (scope) => {
  const symbol = route.params.stockSymbol;
  if (symbol) router.push({ path: `/trades/${scope}/${symbol}`, query: route.query });
};

const setAssetType = (type) => {
  const symbol = route.params.stockSymbol;
  if (symbol) {
    const query = { ...route.query };
    if (type && type !== 'all') query.asset_type = type;
    else delete query.asset_type;
    router.push({ path: route.path, query });
  }
};
</script>

<style scoped>
.navbar {
  background: var(--color-terminal-surface);
  border-bottom: 2px solid var(--color-terminal-border);
  padding: 0 20px;
  position: sticky;
  top: 0;
  z-index: 200;
}

.navbar-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 20px;
  height: 50px;
}

.navbar-brand {
  font-size: 1rem;
  font-weight: 700;
  color: var(--color-accent-blue);
  text-decoration: none;
  white-space: nowrap;
  flex-shrink: 0;
}
.navbar-brand:hover { color: var(--color-accent-blue); opacity: 0.85; }

.navbar-links {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
}

.nav-link {
  color: var(--color-terminal-text-muted);
  text-decoration: none;
  font-size: 0.82rem;
  font-weight: 600;
  padding: 4px 2px;
  border: none;
  background: none;
  cursor: pointer;
  white-space: nowrap;
}
.nav-link:hover,
.nav-link.router-link-active { color: var(--color-accent-blue); }

/* Symbols Dropdown */
.nav-dropdown { position: relative; }

.nav-dropdown-trigger {
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: inherit;
}

.dropdown-arrow { font-size: 0.6rem; }

.symbols-menu {
  position: absolute;
  top: calc(100% + 2px);
  left: 0;
  min-width: 240px;
  max-height: 360px;
  overflow-y: auto;
  z-index: 300;
}

.dropdown-symbol {
  font-weight: 700;
  color: var(--color-accent-blue);
  min-width: 60px;
  display: inline-block;
  font-size: 0.82rem;
}

.dropdown-name {
  color: var(--color-terminal-text-muted);
  font-size: 0.76rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 160px;
}

/* Toggle groups */
.nav-toggle-group { display: flex; align-items: center; }

/* Status / error below navbar */
.nav-status {
  font-size: 0.75rem;
  color: var(--color-terminal-text-muted);
  text-align: center;
  padding: 2px;
  background: var(--color-terminal-surface);
}
.nav-error {
  font-size: 0.75rem;
  color: var(--color-loss);
  text-align: center;
  padding: 2px 16px;
  background: var(--color-loss-bg);
}
</style>
