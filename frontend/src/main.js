import { createApp } from 'vue'
import * as bootstrap from 'bootstrap/dist/js/bootstrap.bundle';
// import 'bootstrap/dist/css/bootstrap.css'
// Put here if you want yours to override Bootstrap variables
import App from './App.vue'
import router from './router/index'
import './assets/main.css'

// createApp(App).mount('#app')
const app = createApp(App);
app.provide('bootstrap', bootstrap);
app.use(router);  
app.mount('#app');

