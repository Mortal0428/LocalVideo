/// <reference types="../node_modules/.vue-global-types/vue_3.5_0_0_0.d.ts" />
import { onMounted } from 'vue';
// Theme initialization (Light, Dark, System)
const initTheme = () => {
    const saved = localStorage.getItem('cinema_theme') || 'system';
    if (saved === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
    }
    else if (saved === 'light') {
        document.documentElement.setAttribute('data-theme', 'light');
    }
    else {
        const isDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
    }
};
onMounted(() => {
    initTheme();
    if (window.matchMedia) {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
            const current = localStorage.getItem('cinema_theme') || 'system';
            if (current === 'system') {
                document.documentElement.setAttribute('data-theme', e.matches ? 'dark' : 'light');
            }
        });
    }
});
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    id: "apple-app-root",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "aurora-ambient-bg" },
    'aria-hidden': "true",
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "aurora-orb orb-blue" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "aurora-orb orb-purple" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "aurora-orb orb-rose" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
    ...{ class: "app-content-shell" },
});
const __VLS_0 = {}.RouterView;
/** @type {[typeof __VLS_components.RouterView, typeof __VLS_components.routerView, ]} */ ;
// @ts-ignore
const __VLS_1 = __VLS_asFunctionalComponent(__VLS_0, new __VLS_0({}));
const __VLS_2 = __VLS_1({}, ...__VLS_functionalComponentArgsRest(__VLS_1));
/** @type {__VLS_StyleScopedClasses['aurora-ambient-bg']} */ ;
/** @type {__VLS_StyleScopedClasses['aurora-orb']} */ ;
/** @type {__VLS_StyleScopedClasses['orb-blue']} */ ;
/** @type {__VLS_StyleScopedClasses['aurora-orb']} */ ;
/** @type {__VLS_StyleScopedClasses['orb-purple']} */ ;
/** @type {__VLS_StyleScopedClasses['aurora-orb']} */ ;
/** @type {__VLS_StyleScopedClasses['orb-rose']} */ ;
/** @type {__VLS_StyleScopedClasses['app-content-shell']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
//# sourceMappingURL=App.vue.js.map