/**
 * OpenStadt - Neo-Brutalist Design System
 * German Civic Colors: Black, Red, Gold
 */

const config = {
    // Vue delimiters - avoid conflict with Jinja2
    delimiters: ['${', '}'],

    // Vuetify configuration with Brutalist theme
    vuetifyConfig: {
        defaults: {
            VTextField: {
                variant: 'outlined',
                rounded: 0
            },
            VSelect: {
                variant: 'outlined',
                rounded: 0
            },
            VTextarea: {
                variant: 'outlined',
                rounded: 0
            },
            VCombobox: {
                variant: 'outlined',
                rounded: 0
            },
            VChip: {
                size: 'small',
                rounded: 0
            },
            VCard: {
                elevation: 0,
                rounded: 0
            },
            VMenu: {
                offset: 10
            },
            VBtn: {
                variant: 'elevated',
                size: 'small',
                rounded: 0
            },
            VAlert: {
                rounded: 0
            },
            VDataTableServer: {
                itemsPerPage: 25,
                itemsPerPageOptions: [25, 50, 100]
            }
        },
        theme: {
            defaultTheme: 'brutalist',
            themes: {
                brutalist: {
                    dark: false,
                    colors: {
                        // German Civic Palette
                        primary: '#DD0000',      // German Red
                        secondary: '#FFCC00',    // German Gold
                        accent: '#000000',       // Black
                        error: '#DD0000',
                        info: '#3B82F6',
                        success: '#22C55E',
                        warning: '#F59E0B',
                        background: '#FFF8E7',   // Cream
                        surface: '#FFFFFF',
                        'surface-light': '#F5F5F5',
                        'on-surface': '#000000',
                        'on-primary': '#FFFFFF',
                        'on-secondary': '#000000',
                    }
                },
                light: {
                    dark: false,
                    colors: {
                        primary: '#DD0000',
                        secondary: '#FFCC00',
                        accent: '#000000',
                        error: '#DD0000',
                        info: '#3B82F6',
                        success: '#22C55E',
                        warning: '#F59E0B',
                        background: '#FFF8E7',
                        surface: '#FFFFFF',
                        'surface-light': '#F5F5F5',
                        'on-surface': '#000000',
                    }
                },
                dark: {
                    dark: true,
                    colors: {
                        primary: '#EF4444',
                        secondary: '#FFD700',
                        accent: '#FFFFFF',
                        error: '#EF4444',
                        info: '#60A5FA',
                        success: '#4ADE80',
                        warning: '#FBBF24',
                        background: '#0A0A0A',
                        surface: '#171717',
                        'surface-light': '#262626',
                        'on-surface': '#FFFFFF',
                    }
                }
            }
        }
    }
};

// Leaflet default config
const leafletConfig = {
    tileLayer: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    tileAttribution: '&copy; <a href="https://openstreetmap.org">OpenStreetMap</a>',
    maxZoom: 19,
    minZoom: 8,
};

// Layer icons mapping
const layerIcons = {
    'baby-carriage': 'mdi-baby-carriage',
    'child': 'mdi-human-child',
    'tree': 'mdi-tree',
    'recycle': 'mdi-recycle',
    'school': 'mdi-school',
    'hospital': 'mdi-hospital',
    'water': 'mdi-water',
    'map-marker': 'mdi-map-marker',
};
