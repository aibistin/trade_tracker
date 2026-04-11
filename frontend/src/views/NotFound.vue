<template>
  <div class="not-found">
    <h1 class="nf-code">404</h1>
    <p class="nf-message">Page not found</p>
    <router-link to="/home" class="nf-link">Return to Home</router-link>
  </div>
</template>

<style scoped>
.not-found {
  text-align: center;
  padding-top: 80px;
}

.nf-code {
  font-size: 3rem;
  font-weight: 700;
  color: var(--color-terminal-text-dim);
  margin-bottom: 8px;
}

.nf-message {
  color: var(--color-terminal-text-muted);
  font-size: 0.9rem;
  margin-bottom: 20px;
}

.nf-link {
  color: var(--color-accent-cyan);
  font-size: 0.82rem;
}
</style>
