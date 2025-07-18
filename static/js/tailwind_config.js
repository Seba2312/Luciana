


/*
 basically ability to have a light mode
for now not being used, maybe easier if in seperate file and over db,
const light = {
    background: '#f8fafc', surface: '#ffffff',
    textPrimary: '#0f172a', textSecondary: '#475569',

    primary: '#0ea5e9', primaryHover: '#0284c7',
    secondary: '#8b5cf6', secondaryHover: '#7c3aed',
    success: '#10b981', successHover: '#059669',
    info: '#06b6d4', infoHover: '#0891b2',
    warning: '#fbbf24', warningHover: '#f59e0b',
    danger: '#ef4444', dangerHover: '#dc2626',
    neutral: '#64748b', neutralHover: '#475569',
    accent: '#e879f9', accentHover: '#d946ef',

    navActive: '#8b5cf6', navDefault: '#0f172a', navHover: '#000000',
    demo: '#fbbf24', demoHover: '#f59e0b',
    avatarFallback: '#9ca3af',
    logout: '#ef4444', logoutHover: '#dc2626',

    online: '#3b82f6', presence: '#10b981', hybrid: '#8b5cf6'
};
*/
tailwind.config = {
    theme: {
        extend: {
            colors: {
                background: '#0f2339',
                surface: '#1e293b',
                textPrimary: '#f1f5f9',
                textSecondary: '#94a3b8',

                /* 8 zentrale Töne */
                primary: '#38bdf8', primaryHover: '#0ea5e9',
                secondary: '#8b5cf6', secondaryHover: '#7c3aed',
                success: '#10b981', successHover: '#059669',
                info: '#06b6d4', infoHover: '#0891b2',
                warning: '#fbbf24', warningHover: '#f59e0b',
                danger: '#ef4444', dangerHover: '#dc2626',
                neutral: '#64748b', neutralHover: '#475569',
                accent: '#e879f9', accentHover: '#d946ef',

                /* Navigation  / Buttons */
                navActive: '#8b5cf6', navDefault: '#f1f5f9', navHover: '#ffffff',
                demo: '#fbbf24', demoHover: '#f59e0b',
                avatarFallback: '#9ca3af',
                logout: '#ef4444', logoutHover: '#dc2626',

                /* Badges */
                online: '#3b82f6', presence: '#10b981', hybrid: '#8b5cf6'
            }
        }
    }
}

;
