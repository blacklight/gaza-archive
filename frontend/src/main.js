import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles/index.scss'

import "@fortawesome/fontawesome-free/scss/fontawesome.scss";
import "@fortawesome/fontawesome-free/scss/solid.scss";    // fas
import "@fortawesome/fontawesome-free/scss/regular.scss";  // far
import "@fortawesome/fontawesome-free/scss/brands.scss";   // fab

const app = createApp(App)

app.use(router)

app.mount('#app')
