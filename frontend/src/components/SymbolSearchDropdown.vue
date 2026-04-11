<template>
  <div class="symbol-search-dropdown">
    <input
      v-model="searchQuery"
      type="text"
      class="form-control"
      :placeholder="placeholder"
      @focus="isDropdownOpen = true"
      @blur="closeDropdown"
    />
    <ul v-if="isDropdownOpen && filteredSymbols.length > 0" class="dropdown-menu show">
      <li v-for="[symbol, name] in filteredSymbols" :key="symbol">
        <a class="dropdown-item" href="#" @mousedown.prevent="select(symbol)">
          {{ symbol }} - {{ name }}
        </a>
      </li>
    </ul>
    <ul v-else-if="isDropdownOpen && searchQuery" class="dropdown-menu show">
      <li><span class="dropdown-item disabled">No matching symbols found</span></li>
    </ul>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  symbols: { type: Array, default: () => [] },
  placeholder: { type: String, default: 'Search symbols...' },
});

const emit = defineEmits(['select']);

const searchQuery = ref('');
const isDropdownOpen = ref(false);

const filteredSymbols = computed(() => {
  if (!props.symbols?.length) return [];
  if (!searchQuery.value) return props.symbols;
  const q = searchQuery.value.toLowerCase();
  return props.symbols.filter(([symbol, name]) =>
    symbol.toLowerCase().includes(q) || name.toLowerCase().includes(q)
  );
});

function select(symbol) {
  searchQuery.value = '';
  isDropdownOpen.value = false;
  emit('select', symbol);
}

function closeDropdown() {
  // Small delay so mousedown on item fires before blur hides the list
  setTimeout(() => { isDropdownOpen.value = false; }, 150);
}
</script>

<style scoped>
.symbol-search-dropdown {
  position: relative;
}

.symbol-search-dropdown input {
  width: 220px;
  min-width: 160px;
}

.dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  z-index: 1000;
  min-width: 260px;
  max-height: 300px;
  overflow-y: auto;
}

.dropdown-menu.show {
  display: block;
}

.dropdown-item.disabled {
  color: var(--color-terminal-text-dim);
  pointer-events: none;
}
</style>
