/// <reference types="../../node_modules/.vue-global-types/vue_3.5_0_0_0.d.ts" />
import { computed } from 'vue';
import { useRouter } from 'vue-router';
const router = useRouter();
const user = computed(() => {
    try {
        const raw = localStorage.getItem('user');
        return raw ? JSON.parse(raw) : null;
    }
    catch {
        return null;
    }
});
const isAdmin = computed(() => user.value?.role === 'ADMIN');
const goToPortal = () => {
    router.push('/');
};
const goToCreator = () => {
    router.push('/creator');
};
const goToAdmin = () => {
    router.push('/admin');
};
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
/** @type {__VLS_StyleScopedClasses['nav-glass-link']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-glass-link']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-cta-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['primary-apple-cta']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-apple-cta']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['role-card-item']} */ ;
/** @type {__VLS_StyleScopedClasses['role-card-item']} */ ;
/** @type {__VLS_StyleScopedClasses['role-card-item']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-headline']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-features-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['role-architecture-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['role-card-arrow']} */ ;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "landing-page-container" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "landing-ambient-bg" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "aurora-orb orb-1" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "aurora-orb orb-2" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "aurora-orb orb-3" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.header, __VLS_intrinsicElements.header)({
    ...{ class: "landing-nav-bar" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ onClick: (__VLS_ctx.goToPortal) },
    ...{ class: "nav-brand-wrap" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "brand-badge-pill" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "brand-title-text" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "nav-links-cluster" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.goToPortal) },
    ...{ class: "nav-glass-link" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.goToCreator) },
    ...{ class: "nav-glass-link" },
});
if (__VLS_ctx.isAdmin) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
        ...{ onClick: (__VLS_ctx.goToAdmin) },
        ...{ class: "nav-glass-link admin-highlight" },
    });
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.goToPortal) },
    ...{ class: "nav-cta-btn" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.main, __VLS_intrinsicElements.main)({
    ...{ class: "landing-hero-content" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "hero-tag-badge" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "pulse-dot" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({
    ...{ class: "landing-headline" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.br)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "gradient-text" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
    ...{ class: "landing-subtext" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.br)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "landing-actions-group" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.goToPortal) },
    ...{ class: "primary-apple-cta" },
    id: "btn-enter-portal",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "arrow-glyph" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (__VLS_ctx.goToCreator) },
    ...{ class: "secondary-apple-cta" },
    id: "btn-enter-creator",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "landing-features-grid" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-glass-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "card-accent-tag" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-glass-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "card-accent-tag" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "feature-glass-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "card-accent-tag" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h3, __VLS_intrinsicElements.h3)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "role-architecture-banner" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "role-card-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "role-chip user-chip" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "role-card-arrow" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "role-card-item highlight-card" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "role-chip creator-chip" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "role-card-arrow" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "role-card-item" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({
    ...{ class: "role-chip admin-chip" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.h4, __VLS_intrinsicElements.h4)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({});
__VLS_asFunctionalElement(__VLS_intrinsicElements.footer, __VLS_intrinsicElements.footer)({
    ...{ class: "landing-footer" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.span, __VLS_intrinsicElements.span)({});
/** @type {__VLS_StyleScopedClasses['landing-page-container']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-ambient-bg']} */ ;
/** @type {__VLS_StyleScopedClasses['aurora-orb']} */ ;
/** @type {__VLS_StyleScopedClasses['orb-1']} */ ;
/** @type {__VLS_StyleScopedClasses['aurora-orb']} */ ;
/** @type {__VLS_StyleScopedClasses['orb-2']} */ ;
/** @type {__VLS_StyleScopedClasses['aurora-orb']} */ ;
/** @type {__VLS_StyleScopedClasses['orb-3']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-nav-bar']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-brand-wrap']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-badge-pill']} */ ;
/** @type {__VLS_StyleScopedClasses['brand-title-text']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-links-cluster']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-glass-link']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-glass-link']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-glass-link']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-highlight']} */ ;
/** @type {__VLS_StyleScopedClasses['nav-cta-btn']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-hero-content']} */ ;
/** @type {__VLS_StyleScopedClasses['hero-tag-badge']} */ ;
/** @type {__VLS_StyleScopedClasses['pulse-dot']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-headline']} */ ;
/** @type {__VLS_StyleScopedClasses['gradient-text']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-subtext']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-actions-group']} */ ;
/** @type {__VLS_StyleScopedClasses['primary-apple-cta']} */ ;
/** @type {__VLS_StyleScopedClasses['arrow-glyph']} */ ;
/** @type {__VLS_StyleScopedClasses['secondary-apple-cta']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-features-grid']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-accent-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-accent-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['feature-glass-card']} */ ;
/** @type {__VLS_StyleScopedClasses['card-accent-tag']} */ ;
/** @type {__VLS_StyleScopedClasses['role-architecture-banner']} */ ;
/** @type {__VLS_StyleScopedClasses['role-card-item']} */ ;
/** @type {__VLS_StyleScopedClasses['role-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['user-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['role-card-arrow']} */ ;
/** @type {__VLS_StyleScopedClasses['role-card-item']} */ ;
/** @type {__VLS_StyleScopedClasses['highlight-card']} */ ;
/** @type {__VLS_StyleScopedClasses['role-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['creator-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['role-card-arrow']} */ ;
/** @type {__VLS_StyleScopedClasses['role-card-item']} */ ;
/** @type {__VLS_StyleScopedClasses['role-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['admin-chip']} */ ;
/** @type {__VLS_StyleScopedClasses['landing-footer']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            isAdmin: isAdmin,
            goToPortal: goToPortal,
            goToCreator: goToCreator,
            goToAdmin: goToAdmin,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=LandingView.vue.js.map