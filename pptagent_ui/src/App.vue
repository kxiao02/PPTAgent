<template>
  <div id="app">
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style scoped>
#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  margin: 0;
}

.app-main {
  flex: 1;
  width: 100%;
}
</style>
