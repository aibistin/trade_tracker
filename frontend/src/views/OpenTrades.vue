<template>
    <div>
      <h1>Open Trades for {{ stockSymbol }}</h1>
      <!-- Add your OpenTrades component logic here -->
    </div>
  </template>
  
  <script setup>
  import { defineProps } from 'vue';
  
  const props = defineProps({
    stockSymbol: {
      type: String,
      required: true
    }
  });
  </script>