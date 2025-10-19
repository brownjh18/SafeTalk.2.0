/**
 * Service Worker for SafeTalk
 * Enables offline functionality, caching, and background sync
 */

const CACHE_NAME = 'safetalk-v1';
const STATIC_CACHE_NAME = 'safetalk-static-v1';
const DYNAMIC_CACHE_NAME = 'safetalk-dynamic-v1';

// Files to cache immediately
const STATIC_FILES = [
    '/',
    '/static/css/main.css',
    '/static/js/main.js',
    '/static/js/offline-manager.js',
    '/static/js/websocket.js',
    '/static/img/logo.png',
    '/static/img/offline-icon.png',
    '/accounts/login/',
    '/accounts/register/',
    '/offline/',
    '/manifest.json'
];

// API endpoints that should work offline
const API_CACHE_PATTERNS = [
    /\/accounts\/api\/mood-entries/,
    /\/accounts\/api\/get-offline-data/,
    /\/chat\/api\/messages/
];

// Install event - cache static files
self.addEventListener('install', event => {
    console.log('Service Worker installing');
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then(cache => {
                console.log('Caching static files');
                return cache.addAll(STATIC_FILES);
            })
            .catch(error => {
                console.error('Failed to cache static files:', error);
            })
    );
    self.skipWaiting();
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker activating');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE_NAME && cacheName !== DYNAMIC_CACHE_NAME) {
                        console.log('Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Handle API requests
    if (url.pathname.startsWith('/api/') || API_CACHE_PATTERNS.some(pattern => pattern.test(url.pathname))) {
        event.respondWith(handleApiRequest(request));
        return;
    }

    // Handle static assets
    if (request.destination === 'style' || request.destination === 'script' || request.destination === 'image') {
        event.respondWith(handleStaticRequest(request));
        return;
    }

    // Handle navigation requests
    if (request.mode === 'navigate') {
        event.respondWith(handleNavigationRequest(request));
        return;
    }

    // Default fetch
    event.respondWith(
        fetch(request)
            .catch(() => {
                // Return offline page for navigation requests
                if (request.mode === 'navigate') {
                    return caches.match('/offline/');
                }
            })
    );
});

// Handle API requests with offline support
async function handleApiRequest(request) {
    try {
        // Try network first
        const response = await fetch(request);
        return response;
    } catch (error) {
        // Network failed, try cache
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // Return offline response for API calls
        return new Response(
            JSON.stringify({
                error: 'offline',
                message: 'You are currently offline. This action will be synced when connection is restored.'
            }),
            {
                status: 503,
                headers: { 'Content-Type': 'application/json' }
            }
        );
    }
}

// Handle static assets with cache-first strategy
async function handleStaticRequest(request) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }

    try {
        const response = await fetch(request);
        // Cache successful responses
        if (response.ok) {
            const cache = await caches.open(STATIC_CACHE_NAME);
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        // Return a placeholder for images
        if (request.destination === 'image') {
            return new Response('', { status: 404 });
        }
        return new Response('', { status: 503 });
    }
}

// Handle navigation requests
async function handleNavigationRequest(request) {
    try {
        const response = await fetch(request);
        return response;
    } catch (error) {
        // Try cache first
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }

        // Return offline page
        const offlineResponse = await caches.match('/offline/');
        if (offlineResponse) {
            return offlineResponse;
        }

        // Fallback offline page
        return new Response(
            `
            <!DOCTYPE html>
            <html>
            <head>
                <title>SafeTalk - Offline</title>
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                    .offline-icon { font-size: 4em; margin-bottom: 20px; }
                    h1 { color: #333; }
                    p { color: #666; max-width: 400px; margin: 0 auto; }
                </style>
            </head>
            <body>
                <div class="offline-icon">📱</div>
                <h1>You are offline</h1>
                <p>SafeTalk is not available right now. Please check your internet connection and try again.</p>
                <p>Your data will be automatically synced when you're back online.</p>
            </body>
            </html>
            `,
            {
                headers: { 'Content-Type': 'text/html' }
            }
        );
    }
}

// Background sync for offline actions
self.addEventListener('sync', event => {
    console.log('Background sync triggered:', event.tag);

    if (event.tag === 'background-sync') {
        event.waitUntil(performBackgroundSync());
    }
});

// Push notifications
self.addEventListener('push', event => {
    console.log('Push notification received');

    if (event.data) {
        const data = event.data.json();
        const options = {
            body: data.message,
            icon: '/static/img/notification-icon.png',
            badge: '/static/img/badge-icon.png',
            data: data.data || {},
            actions: [
                {
                    action: 'view',
                    title: 'View'
                },
                {
                    action: 'dismiss',
                    title: 'Dismiss'
                }
            ]
        };

        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
    console.log('Notification clicked:', event.action);

    event.notification.close();

    if (event.action === 'view') {
        // Open the app
        event.waitUntil(
            clients.openWindow(event.notification.data.url || '/')
        );
    }
});

// Background sync implementation
async function performBackgroundSync() {
    console.log('Performing background sync');

    try {
        // Get all open clients (tabs/windows)
        const clients = await self.clients.matchAll();

        // Notify all clients to sync their data
        clients.forEach(client => {
            client.postMessage({
                type: 'background-sync',
                message: 'Syncing offline data...'
            });
        });

        // Perform sync operations
        await syncOfflineData();

    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

// Sync offline data
async function syncOfflineData() {
    // This would typically make API calls to sync pending data
    // For now, we'll just log it
    console.log('Syncing offline data...');

    // You could implement IndexedDB access here to get pending data
    // and sync it with the server
}

// Message handling for communication with main thread
self.addEventListener('message', event => {
    const { type, data } = event.data;

    switch (type) {
        case 'skip-waiting':
            self.skipWaiting();
            break;

        case 'sync-data':
            performBackgroundSync();
            break;

        case 'cache-url':
            cacheUrl(data.url);
            break;

        default:
            console.log('Unknown message type:', type);
    }
});

// Cache a specific URL
async function cacheUrl(url) {
    try {
        const response = await fetch(url);
        if (response.ok) {
            const cache = await caches.open(DYNAMIC_CACHE_NAME);
            await cache.put(url, response);
            console.log('URL cached:', url);
        }
    } catch (error) {
        console.error('Failed to cache URL:', url, error);
    }
}

// Periodic background sync (if supported)
self.addEventListener('periodicsync', event => {
    if (event.tag === 'periodic-sync') {
        event.waitUntil(
            performPeriodicSync()
        );
    }
});

async function performPeriodicSync() {
    console.log('Performing periodic sync');

    // Perform maintenance tasks
    await cleanupOldCache();
    await prefetchImportantData();
}

async function cleanupOldCache() {
    const cache = await caches.open(DYNAMIC_CACHE_NAME);
    const keys = await cache.keys();

    // Remove old entries (older than 1 day)
    const oneDayAgo = Date.now() - (24 * 60 * 60 * 1000);

    for (const request of keys) {
        const response = await cache.match(request);
        if (response) {
            const date = response.headers.get('date');
            if (date && new Date(date).getTime() < oneDayAgo) {
                await cache.delete(request);
            }
        }
    }
}

async function prefetchImportantData() {
    // Prefetch important data for better offline experience
    const urlsToPrefetch = [
        '/accounts/profile/',
        '/accounts/mood-history/',
        '/chat/',
    ];

    for (const url of urlsToPrefetch) {
        await cacheUrl(url);
    }
}

// Error handling
self.addEventListener('error', event => {
    console.error('Service Worker error:', event.error);
});

self.addEventListener('unhandledrejection', event => {
    console.error('Service Worker unhandled rejection:', event.reason);
});