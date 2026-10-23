<template>
  <svg 
    class="gold-coin-svg"
    :width="size" 
    :height="size" 
    viewBox="0 0 48 48" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
    :style="{ width: `${size}px`, height: `${size}px` }"
  >
    <defs>
      <!-- Outer Rim Radial Gradient -->
      <radialGradient id="coinRimGrad" cx="30%" cy="30%" r="70%">
        <stop offset="0%" stop-color="#FFEBA0" />
        <stop offset="45%" stop-color="#F59E0B" />
        <stop offset="85%" stop-color="#D97706" />
        <stop offset="100%" stop-color="#92400E" />
      </radialGradient>

      <!-- Inner Disc Linear Gradient -->
      <linearGradient id="coinInnerGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#FEF3C7" />
        <stop offset="35%" stop-color="#FBBF24" />
        <stop offset="75%" stop-color="#D97706" />
        <stop offset="100%" stop-color="#78350F" />
      </linearGradient>

      <!-- Embossed Highlight Gradient -->
      <linearGradient id="coinEmbossGrad" x1="20%" y1="0%" x2="80%" y2="100%">
        <stop offset="0%" stop-color="#FFFBEB" stop-opacity="0.9" />
        <stop offset="50%" stop-color="#F59E0B" stop-opacity="0.6" />
        <stop offset="100%" stop-color="#78350F" stop-opacity="0.9" />
      </linearGradient>

      <!-- Metallic Specular Glow Filter -->
      <filter id="coinGlow" x="-20%" y="-20%" width="140%" height="140%">
        <feGaussianBlur in="SourceAlpha" stdDeviation="1.5" />
        <feOffset dx="0" dy="1" result="offsetblur" />
        <feComponentTransfer>
          <feFuncA type="linear" slope="0.3" />
        </feComponentTransfer>
        <feMerge>
          <feMergeNode />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>

    <!-- Coin Outer Rim with 3D Drop Shadow effect -->
    <circle cx="24" cy="24" r="22" fill="url(#coinRimGrad)" filter="url(#coinGlow)" />
    
    <!-- Outer Beveled Edge Border -->
    <circle cx="24" cy="24" r="21.5" stroke="#FDE68A" stroke-width="1" stroke-opacity="0.8" />
    <circle cx="24" cy="24" r="19" stroke="#78350F" stroke-width="0.8" stroke-opacity="0.5" />

    <!-- Coin Inner Inset Disc -->
    <circle cx="24" cy="24" r="18" fill="url(#coinInnerGrad)" />

    <!-- Inner Textured Ring / Serration Dots -->
    <circle cx="24" cy="24" r="15.5" stroke="url(#coinEmbossGrad)" stroke-width="1.2" stroke-dasharray="2 1.5" />

    <!-- Embossed Center Symbol: High-relief Star & Currency Mark -->
    <g transform="translate(24, 24)">
      <!-- Center Four-Point Star Relief -->
      <path 
        d="M 0 -9 L 2.5 -2.5 L 9 0 L 2.5 2.5 L 0 9 L -2.5 2.5 L -9 0 L -2.5 -2.5 Z" 
        fill="url(#coinEmbossGrad)"
        stroke="#78350F"
        stroke-width="0.5"
      />
      <!-- Inner Radiant Core -->
      <circle cx="0" cy="0" r="2.2" fill="#FEF3C7" stroke="#B45309" stroke-width="0.6" />
      <circle cx="-0.8" cy="-0.8" r="0.8" fill="#FFFFFF" />
    </g>

    <!-- Top Left Specular Highlight Arc -->
    <path 
      d="M 10 16 A 18 18 0 0 1 28 7" 
      stroke="#FFFFFF" 
      stroke-width="1.6" 
      stroke-linecap="round" 
      stroke-opacity="0.65" 
    />
  </svg>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  size?: number | string
}>(), {
  size: 20
})
</script>

<style scoped>
.gold-coin-svg {
  display: inline-block;
  vertical-align: middle;
  flex-shrink: 0;
  transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), filter 0.25s ease;
}

.gold-coin-svg:hover {
  transform: rotate(12deg) scale(1.08);
  filter: drop-shadow(0 2px 8px rgba(245, 158, 11, 0.45));
}
</style>
