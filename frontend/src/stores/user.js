import { reactive, computed } from 'vue';
import { authApi } from '../api/auth';
export const userState = reactive({
    currentUser: null,
    token: null,
    initialized: false
});
export const useUserStore = () => {
    const isLoggedIn = computed(() => !!userState.currentUser && !!userState.token);
    const currentRole = computed(() => userState.currentUser?.role || 'GUEST');
    const isAdmin = computed(() => currentRole.value === 'ADMIN');
    const isCreator = computed(() => currentRole.value === 'CREATOR' || !!userState.currentUser?.is_creator);
    const isReviewer = computed(() => currentRole.value === 'REVIEWER' || !!userState.currentUser?.is_reviewer);
    function setUser(user, token) {
        userState.currentUser = user;
        userState.token = token;
        localStorage.setItem('cinema_access_token', token);
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
        window.dispatchEvent(new CustomEvent('cinema-auth-changed', { detail: { user, token } }));
    }
    function clearUser() {
        userState.currentUser = null;
        userState.token = null;
        localStorage.removeItem('cinema_access_token');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.dispatchEvent(new CustomEvent('cinema-auth-changed', { detail: { user: null, token: null } }));
    }
    async function refreshProfile() {
        const token = localStorage.getItem('cinema_access_token') || localStorage.getItem('token');
        if (!token) {
            clearUser();
            userState.initialized = true;
            return null;
        }
        userState.token = token;
        // Optimistically load cached user from localStorage
        const cachedUser = localStorage.getItem('user');
        if (cachedUser && !userState.currentUser) {
            try {
                userState.currentUser = JSON.parse(cachedUser);
            }
            catch (e) {
                // ignore JSON parse error
            }
        }
        try {
            const res = await authApi.getMe();
            const u = res?.data || res?.user || res;
            if (u && (u.id || u.username)) {
                userState.currentUser = u;
                localStorage.setItem('user', JSON.stringify(u));
                userState.initialized = true;
                return u;
            }
        }
        catch (err) {
            console.warn('Could not refresh profile from backend:', err?.message || err);
            // If 401 unauthorized, clear token
            if (err?.response?.status === 401) {
                clearUser();
            }
        }
        userState.initialized = true;
        return userState.currentUser;
    }
    return {
        state: userState,
        currentUser: computed(() => userState.currentUser),
        token: computed(() => userState.token),
        isLoggedIn,
        currentRole,
        isAdmin,
        isCreator,
        isReviewer,
        setUser,
        clearUser,
        refreshProfile
    };
};
// Auto sync across storage events
if (typeof window !== 'undefined') {
    window.addEventListener('storage', (e) => {
        if (e.key === 'cinema_access_token' || e.key === 'user') {
            const store = useUserStore();
            store.refreshProfile();
        }
    });
}
//# sourceMappingURL=user.js.map