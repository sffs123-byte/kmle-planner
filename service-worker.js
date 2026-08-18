const CACHE_NAME = 'kmle-planner-20260818T143424Z';
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './sync.js',
  './version.json',
  './quizzes/충남대_안과_포테_기출_Anki.html',
  './quizzes/assets/cnu_ophthalmology_posttest/q11_lpi.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q13_glaucoma_disc.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q13_normal_disc.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q14_ahmed_tube.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q14_filtering_bleb.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q15_dermatochalasis.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q15_ptosis_table.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q16_dcr_fluorescein.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q17_accommodative_esotropia.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q18_gonioscopy_lens.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q18_retinoscopy.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q19_endophthalmitis.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q20_ppv.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q20_retinal_detachment.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q20_scleral_buckle.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q20_subconjunctival_hemorrhage.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q21_buphthalmos.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q21_haab_striae.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q25_brvo.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q25_papilledema.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/q25_prp.webp',
  './quizzes/assets/cnu_ophthalmology_posttest/qx01_hyphema.webp',
  './data/clerkships/bundles/obgyn_2026_06_track_a3g6.bundle.json',
  './assets/icons/icon-180.png',
  './assets/icons/icon-192.png',
  './assets/icons/icon-512.png',
  './assets/icons/icon-512-maskable.png',
  './assets/icons/favicon.svg',
  './data/canary_import_seed.json',
  './data/allen_question_counts_2026-04-10.json'
];
const NETWORK_FIRST_PATHS = new Set(['/', '/kmle-planner/', '/kmle-planner/index.html', '/kmle-planner/sync.js', '/kmle-planner/manifest.webmanifest', '/kmle-planner/version.json']);

async function putInCache(request, response) {
  if (!response || response.status !== 200) return response;
  const cache = await caches.open(CACHE_NAME);
  await cache.put(request, response.clone());
  return response;
}

async function networkFirst(request, fallbackKey = null) {
  try {
    const response = await fetch(request, { cache: 'no-store' });
    return await putInCache(request, response);
  } catch {
    const cached = await caches.match(request);
    if (cached) return cached;
    if (fallbackKey) {
      const fallback = await caches.match(fallbackKey);
      if (fallback) return fallback;
    }
    return Response.error();
  }
}

async function cacheFirst(request, fallbackKey = null) {
  const cached = await caches.match(request);
  if (cached) return cached;
  try {
    const response = await fetch(request);
    return await putInCache(request, response);
  } catch {
    if (fallbackKey) {
      const fallback = await caches.match(fallbackKey);
      if (fallback) return fallback;
    }
    return Response.error();
  }
}

self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  const isLiveBundle = url.pathname.includes('/data/clerkships/bundles/');
  const isProfessorAsset = url.pathname.includes('/data/clerkships/professors/');
  const isNavigation = event.request.mode === 'navigate';
  const isShellPath = NETWORK_FIRST_PATHS.has(url.pathname);

  if (isProfessorAsset) {
    event.respondWith(networkFirst(event.request));
    return;
  }

  if (isLiveBundle || isNavigation || isShellPath) {
    event.respondWith(networkFirst(event.request, './index.html'));
    return;
  }

  event.respondWith(cacheFirst(event.request, isNavigation ? './index.html' : null));
});
