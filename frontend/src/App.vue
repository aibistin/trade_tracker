<script setup>
import NavBar from "./components/NavBar.vue";
</script>

<template>
  <div class="app-shell">
    <NavBar />
    <main class="app-main">
      <router-view></router-view>
    </main>
  </div>
</template>

<style scoped>
.app-shell {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-main {
  flex: 1;
  max-width: 1400px;
  width: 100%;
  margin: 0 auto;
  padding: 16px 20px;
}
</style>
