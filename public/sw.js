const CACHE_NAME = 'duyou-v2';

// 白名单：需要预缓存的核心页面
const WHITELIST_PAGES = [
  '/',
  '/agents',
  '/opensource',
  '/blog',
  '/briefings',
  '/duyou',
  '/delivery',
  '/research',
  '/achievements',
  '/timeline',
  '/studio',
  '/feed'
];

// 预缓存资源
const PRECACHE_ASSETS = [
  ...WHITELIST_PAGES,
  '/duyoufavicon.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  const pathname = url.pathname;

  // 对于导航请求（页面访问）
  if (event.request.mode === 'navigate') {
    // 检查是否在白名单中（支持带或不带尾部斜杠）
    const isWhitelisted = WHITELIST_PAGES.includes(pathname) || 
                          WHITELIST_PAGES.includes(pathname.replace(/\/$/, '')) ||
                          WHITELIST_PAGES.includes(pathname + '/') ||
                          pathname.startsWith('/blog/');

    if (isWhitelisted) {
      // 白名单页面：缓存优先策略
      event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) {
            // 后台更新
            fetch(event.request).then((response) => {
              if (response && response.status === 200) {
                caches.open(CACHE_NAME).then((cache) => {
                  cache.put(event.request, response.clone());
                });
              }
            }).catch(() => {});
            return cachedResponse;
          }
          
          // 缓存未命中，从网络获取并缓存
          return fetch(event.request).then((response) => {
            if (response && response.status === 200) {
              const responseToCache = response.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, responseToCache);
              });
            }
            return response;
          }).catch(() => {
            // 网络和缓存都失败，返回首页
            return caches.match('/');
          });
        })
      );
    } else {
      // 非白名单页面：网络优先，不缓存
      event.respondWith(
        fetch(event.request).catch(() => {
          // 网络失败时，尝试从缓存查找（可能之前访问过）
          return caches.match(event.request).then((cachedResponse) => {
            if (cachedResponse) {
              return cachedResponse;
            }
            return caches.match('/');
          });
        })
      );
    }
    return;
  }

  // 对于静态资源（CSS、JS、图片等），使用缓存优先策略
  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        // 后台更新缓存
        fetch(event.request).then((response) => {
          if (response && response.status === 200) {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, response.clone());
            });
          }
        }).catch(() => {});
        return cachedResponse;
      }

      return fetch(event.request).then((response) => {
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }

        const responseToCache = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });

        return response;
      }).catch(() => {
        return new Response('Offline', { status: 503 });
      });
    })
  );
});