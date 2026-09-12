import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import "@fontsource/archivo/600.css";
import "@fontsource/archivo/700.css";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import App from "./App.vue";
import NewIncident from "./views/NewIncident.vue";
import History from "./views/History.vue";
import Incident from "./views/Incident.vue";
import "./style.css";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", component: NewIncident },
    { path: "/historico", component: History },
    { path: "/ocorrencias/:id", component: Incident, props: true },
    { path: "/:pathMatch(.*)*", redirect: "/" },
  ],
  scrollBehavior: () => ({ top: 0 }),
});
createApp(App).use(router).mount("#app");
