/**
 * OpenStadt - Civic Data Platform Configuration
 * Blue/Green civic-focused color palette
 */

const config = {
    // Vue delimiters - avoid conflict with Jinja2
    delimiters: ['${', '}'],

    // Vuetify configuration
    vuetifyConfig: {
        defaults: {
            VTextField: {
                variant: 'outlined'
            },
            VSelect: {
                variant: 'outlined'
            },
            VTextarea: {
                variant: 'outlined'
            },
            VCombobox: {
                variant: 'outlined'
            },
            VChip: {
                size: 'small'
            },
            VCard: {
                elevation: 0,
                rounded: 'lg'
            },
            VMenu: {
                offset: 10
            },
            VBtn: {
                variant: 'elevated',
                size: 'small'
            },
            VDataTableServer: {
                itemsPerPage: 25,
                itemsPerPageOptions: [25, 50, 100]
            }
        },
        theme: {
            defaultTheme: window.__settings__?.dark ? 'dark' : 'light',
            themes: {
                light: {
                    dark: false,
                    colors: {
                        // Civic blue theme
                        primary: '#0066CC',      // City Blue
                        secondary: '#2E7D32',    // Green (nature)
                        accent: '#00ACC1',       // Cyan
                        error: '#D32F2F',
                        info: '#1976D2',
                        success: '#388E3C',
                        warning: '#F57C00',
                        background: '#FAFAFA',
                        surface: '#FFFFFF',
                        'surface-light': '#F5F5F5',
                        'on-surface': '#212121',
                    }
                },
                dark: {
                    dark: true,
                    colors: {
                        primary: '#42A5F5',
                        secondary: '#66BB6A',
                        accent: '#26C6DA',
                        error: '#EF5350',
                        info: '#29B6F6',
                        success: '#66BB6A',
                        warning: '#FFA726',
                        background: '#121212',
                        surface: '#1E1E1E',
                        'surface-light': '#2D2D2D',
                        'on-surface': '#E0E0E0',
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

// Layer icons mapping (FontAwesome to Mdi)
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
