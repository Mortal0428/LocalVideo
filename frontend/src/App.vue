<template>
  <div id="apple-app-root">
    <!-- Ambient Aurora Gradient Background (Fixed 2-3 huge blurred floating orbs) -->
    <div class="aurora-ambient-bg" aria-hidden="true">
      <div class="aurora-orb orb-blue"></div>
      <div class="aurora-orb orb-purple"></div>
      <div class="aurora-orb orb-rose"></div>
    </div>

    <!-- Main Router View -->
    <div class="app-content-shell">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

// Theme initialization (Light, Dark, System)
const initTheme = () => {
  const saved = localStorage.getItem('cinema_theme') || 'system'
  if (saved === 'dark') {
    document.documentElement.setAttribute('data-theme', 'dark')
  } else if (saved === 'light') {
    document.documentElement.setAttribute('data-theme', 'light')
  } else {
    const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
    document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light')
  }
}

onMounted(() => {
  initTheme()
  if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
      const current = localStorage.getItem('cinema_theme') || 'system'
      if (current === 'system') {
        document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light')
      }
    })
  }
})
</script>

<style>
/* ========================================================================== */
/* Apple Human Interface Guidelines (HIG) Design Tokens & Light/Dark Themes    */
/* ========================================================================== */
:root, [data-theme="light"] {
  --theme-mode: light;
  --bg-base: #F6F7F8;
  --bg-surface: rgba(255, 255, 255, 0.85);
  --bg-card: #FFFFFF;
  --text-primary: #18191C;
  --text-secondary: #61666D;
  --text-muted: #9499A0;
  --border-line: #E3E5E7;
  --border-glass: rgba(255, 255, 255, 0.75);
  --glass-specular: inset 0 1px 1px rgba(255, 255, 255, 0.9), inset 0 -1px 1px rgba(0, 0, 0, 0.02);
  --glass-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
  --glass-shadow-hover: 0 18px 40px rgba(0, 0, 0, 0.08);
  --input-bg: #F1F2F3;
  --header-bg: rgba(255, 255, 255, 0.85);
  --header-border: rgba(0, 0, 0, 0.06);

  /* Canvas & Bilibili Theme Tokens */
  --bili-bg: #F6F7F8;
  --bili-pink: #FB7299;
  --bili-pink-hover: #FC8BAB;
  --bili-pink-glow: rgba(251, 114, 153, 0.25);
  --bili-blue: #00AEEC;
  --bili-blue-hover: #33BFF3;
  --bili-blue-glow: rgba(0, 174, 236, 0.22);
  
  --bili-text-dark: #18191C;
  --bili-text-secondary: #61666D;
  --bili-text-muted: #9499A0;
  --bili-line: #E3E5E7;
  --bili-tag-bg: #F1F2F3;

  /* Apple Liquid Glass Tokens */
  --liquid-glass-bg: rgba(255, 255, 255, 0.78);
  --liquid-glass-blur: blur(28px) saturate(180%) contrast(102%);
  --liquid-glass-border: 1px solid rgba(255, 255, 255, 0.75);
  --liquid-glass-shadow: 0 10px 30px rgba(0, 0, 0, 0.04), inset 0 1px 1px rgba(255, 255, 255, 0.9), inset 0 -1px 1px rgba(0, 0, 0, 0.02);
  --liquid-glass-hover: 0 18px 40px rgba(0, 0, 0, 0.08), inset 0 1px 1px rgba(255, 255, 255, 0.95);
  
  /* Apple HIG Tokens */
  --apple-bg: var(--bg-base);
  --apple-card-bg: var(--liquid-glass-bg);
  --apple-card-solid: var(--bg-card);
  --apple-card-border: var(--border-glass);
  --apple-hairline: var(--border-line);
  
  --apple-text-primary: var(--text-primary);
  --apple-text-secondary: var(--text-secondary);
  --apple-text-tertiary: var(--text-muted);
  
  --apple-blue: var(--bili-blue);
  --apple-blue-hover: var(--bili-blue-hover);
  --apple-blue-glow: var(--bili-blue-glow);
  
  --apple-gray-btn: var(--input-bg);
  --apple-gray-btn-hover: #E5E6E8;
  
  --apple-input-bg: var(--input-bg);
  --apple-input-focus: #FFFFFF;
  
  --apple-radius-card: 20px;
  --apple-radius-pill: 9999px;
  --apple-radius-icon: 12px;
  
  --apple-shadow-card: var(--liquid-glass-shadow);
  --apple-shadow-hover: var(--liquid-glass-hover);
  
  --apple-ease: cubic-bezier(0.25, 1, 0.5, 1);
  --apple-transition-fast: 0.2s var(--apple-ease);
  --apple-transition-normal: 0.35s var(--apple-ease);
}

[data-theme="dark"] {
  --theme-mode: dark;
  --bg-base: #0F1014;
  --bg-surface: rgba(24, 25, 28, 0.85);
  --bg-card: #18191C;
  --text-primary: #F1F2F3;
  --text-secondary: #9499A0;
  --text-muted: #61666D;
  --border-line: rgba(255, 255, 255, 0.1);
  --border-glass: rgba(255, 255, 255, 0.12);
  --glass-specular: inset 0 1px 1px rgba(255, 255, 255, 0.15), inset 0 -1px 1px rgba(0, 0, 0, 0.4);
  --glass-shadow: 0 10px 30px rgba(0, 0, 0, 0.35);
  --glass-shadow-hover: 0 18px 40px rgba(0, 0, 0, 0.55);
  --input-bg: rgba(255, 255, 255, 0.08);
  --header-bg: rgba(15, 16, 20, 0.85);
  --header-border: rgba(255, 255, 255, 0.08);

  /* Bilibili Dark Overrides */
  --bili-bg: #0F1014;
  --bili-text-dark: #F1F2F3;
  --bili-text-secondary: #9499A0;
  --bili-text-muted: #61666D;
  --bili-line: rgba(255, 255, 255, 0.1);
  --bili-tag-bg: rgba(255, 255, 255, 0.08);

  /* Liquid Glass Dark */
  --liquid-glass-bg: rgba(24, 25, 28, 0.78);
  --liquid-glass-blur: blur(28px) saturate(180%) contrast(105%);
  --liquid-glass-border: 1px solid rgba(255, 255, 255, 0.12);
  --liquid-glass-shadow: 0 10px 30px rgba(0, 0, 0, 0.4), inset 0 1px 1px rgba(255, 255, 255, 0.12);
  --liquid-glass-hover: 0 18px 40px rgba(0, 0, 0, 0.6), inset 0 1px 1px rgba(255, 255, 255, 0.18);

  /* Apple HIG Dark Compat */
  --apple-bg: var(--bg-base);
  --apple-card-bg: var(--liquid-glass-bg);
  --apple-card-solid: var(--bg-card);
  --apple-card-border: var(--border-glass);
  --apple-hairline: var(--border-line);
  --apple-text-primary: var(--text-primary);
  --apple-text-secondary: var(--text-secondary);
  --apple-text-tertiary: var(--text-muted);
  --apple-gray-btn: rgba(255, 255, 255, 0.08);
  --apple-gray-btn-hover: rgba(255, 255, 255, 0.15);
  --apple-input-bg: rgba(255, 255, 255, 0.08);
  --apple-input-focus: rgba(255, 255, 255, 0.14);
}

/* Universal Apple HIG Visible & Humanized Scrollbars */
* {
  scrollbar-width: thin !important;
  scrollbar-color: rgba(0, 0, 0, 0.28) transparent !important;
}

[data-theme="dark"] * {
  scrollbar-color: rgba(255, 255, 255, 0.28) transparent !important;
}

*::-webkit-scrollbar {
  width: 6px !important;
  height: 6px !important;
}
*::-webkit-scrollbar-track {
  background: transparent !important;
}
*::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.28) !important;
  border-radius: 6px !important;
  transition: background 0.2s ease;
}
*::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.55) !important;
}
[data-theme="dark"] *::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.28) !important;
}
[data-theme="dark"] *::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.55) !important;
}

* {
  box-sizing: border-box;
}

/* Global Link Hygiene Reset */
a, a:link, a:visited, a:hover, a:active {
  text-decoration: none;
  color: inherit;
}

[data-theme="dark"] .aurora-orb {
  opacity: 0.38;
}

html, body {
  margin: 0;
  padding: 0;
  background-color: var(--apple-bg);
  color: var(--apple-text-primary);
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
  min-height: 100vh;
}

#apple-app-root {
  position: relative;
  min-height: 100vh;
  width: 100%;
}

/* Ambient Aurora Gradient Layer */
.aurora-ambient-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  z-index: 0;
  overflow: hidden;
}

.aurora-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(85px);
  opacity: 0.85;
  will-change: transform;
}

.orb-blue {
  width: 55vw;
  height: 55vw;
  max-width: 650px;
  max-height: 650px;
  top: -10vw;
  left: -10vw;
  background: radial-gradient(circle, rgba(162, 210, 255, 0.45) 0%, rgba(162, 210, 255, 0) 70%);
  animation: floatOrb1 18s ease-in-out infinite alternate;
}

.orb-purple {
  width: 60vw;
  height: 60vw;
  max-width: 700px;
  max-height: 700px;
  top: 15vh;
  right: -15vw;
  background: radial-gradient(circle, rgba(200, 180, 255, 0.38) 0%, rgba(200, 180, 255, 0) 70%);
  animation: floatOrb2 22s ease-in-out infinite alternate;
}

.orb-rose {
  width: 50vw;
  height: 50vw;
  max-width: 600px;
  max-height: 600px;
  bottom: -15vh;
  left: 20vw;
  background: radial-gradient(circle, rgba(255, 205, 225, 0.3) 0%, rgba(255, 205, 225, 0) 70%);
  animation: floatOrb3 20s ease-in-out infinite alternate;
}

@keyframes floatOrb1 {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(6vw, 8vh) scale(1.08); }
  100% { transform: translate(-4vw, 4vh) scale(0.96); }
}

@keyframes floatOrb2 {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(-8vw, -6vh) scale(1.06); }
  100% { transform: translate(4vw, 5vh) scale(0.95); }
}

@keyframes floatOrb3 {
  0% { transform: translate(0, 0) scale(1); }
  50% { transform: translate(5vw, -7vh) scale(1.1); }
  100% { transform: translate(-6vw, 3vh) scale(0.94); }
}

.app-content-shell {
  position: relative;
  z-index: 1;
}

/* Keyframes for entrance animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-up {
  animation: fadeInUp 0.5s var(--apple-ease) forwards;
}
</style>
