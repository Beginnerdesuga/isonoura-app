// 最小限のService Worker（PWAとしてホーム画面に追加できるようにするためだけの登録）
// オフラインキャッシュ等は行わず、通常通りネットワークから取得します。
self.addEventListener('install', () => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', () => {
    // 何もしない（通常のネットワーク取得を素通りさせる）
});
