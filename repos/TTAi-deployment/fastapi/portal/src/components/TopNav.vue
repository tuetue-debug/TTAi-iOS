<template>
  <header class="topbar">
    <div class="brand-wrap">
      <div class="brand-mark">T</div>
      <div>
        <div class="brand-name">TTAi Platform</div>
        <div class="brand-subtitle">console.tuetue.vn</div>
      </div>
    </div>
    <nav class="topnav">
      <RouterLink to="/">Home</RouterLink>
      <a href="#features">Features</a>
      <a href="#docs">Docs</a>
      <a href="#pricing">Pricing</a>
    </nav>
    <div class="top-actions">
      <RouterLink class="ghost-btn link-btn" to="/login">Log in</RouterLink>
      <RouterLink class="primary-btn link-btn" to="/signup">Start building</RouterLink>
    </div>
  </header>
</template>
