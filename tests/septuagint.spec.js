const { test, expect } = require('@playwright/test');
const instance = require('../docs/instance.json');
const chunks = require('../docs/data/chunks.json');
const tokens = require('../docs/data/tokens.json');

async function ready(page, url = '/') {
  await page.goto(url);
  await page.waitForFunction(() => window.__contabulateReady === true);
  await expect(page.locator('#results tbody tr').first()).toBeVisible();
}

function localPath(sampleUrl) {
  const url = new URL(sampleUrl);
  return url.pathname + url.search;
}

async function hitTotal(page) {
  const counts = await page.locator('td[data-key="t0_count"]').allTextContents();
  return counts.map(Number).reduce((a, b) => a + b, 0);
}

test('sample queries load, answer their question, and survive a copied link', async ({ page, context }) => {
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  expect(instance.sample_queries).toHaveLength(4);
  const [eleos, agape, hades, poimainei] = instance.sample_queries;

  await ready(page, localPath(eleos.url));
  await expect(page.locator('#gran')).toHaveValue('play');
  await expect(page.locator('#matchMode')).toHaveValue('regex');
  await expect(page.locator('th[data-key="t0_count"]')).toHaveClass(/sorted-desc/);
  await expect(page.locator('#results tbody tr').first()).toContainText('Ψαλμοί (Psalms)');
  await expect(page.locator('#results tbody tr').nth(1)).toContainText('Psalms of Solomon');
  const counts = (await page.locator('td[data-key="t0_count"]').allTextContents()).map(Number);
  expect(counts).toEqual([...counts].sort((a, b) => b - a));
  const copied = await context.newPage();
  await ready(copied, page.url());
  expect((await copied.locator('td[data-key="t0_count"]').allTextContents()).map(Number)).toEqual(counts);
  await copied.close();

  await ready(page, localPath(agape.url));
  await expect(page.locator('#results tbody tr')).toHaveCount(6); // incl. Ecclesiastes 9:1, 9:6 (Brenton)
  await expect(page.locator('#results tbody tr').first()).toContainText('Song of Songs');
  const agapeIndex = ['ἀγάπη', 'ἀγάπης', 'ἀγάπην', 'ἀγάπῃ']
    .reduce((sum, w) => sum + (tokens[w] || []).reduce((s, [, n]) => s + n, 0), 0);
  expect(await hitTotal(page)).toBe(agapeIndex);

  await ready(page, localPath(hades.url));
  await expect(page.locator('#results tbody tr').first()).toContainText('Ἠσαΐας (Isaiah)');
  expect(await hitTotal(page)).toBeGreaterThan(40);

  await ready(page, localPath(poimainei.url));
  await expect(page.locator('#gran')).toHaveValue('line');
  await expect(page.locator('#results tbody tr')).toHaveCount(1);
  await expect(page.locator('#results tbody tr')).toContainText('17.Ps.022.001');
  await expect(page.locator('#results tbody .hit')).toHaveText('Κύριος ποιμαίνει με');
  expect(errors).toEqual([]);
});

test('Greek search keeps accents and breathings, but not case or Unicode form', async ({ page }) => {
  const expected = (tokens['ἔλεος'] || []).length;
  await ready(page, '/?q=' + encodeURIComponent('ἔλεος') + '&gran=line');
  await expect(page.locator('#segmentsTotalInfo')).toContainText(`(${expected} total rows)`);
  await ready(page, '/?q=' + encodeURIComponent('ἜΛΕΟΣ') + '&gran=line');
  await expect(page.locator('#segmentsTotalInfo')).toContainText(`(${expected} total rows)`);
  await ready(page, '/?q=' + encodeURIComponent('ἔλεος'.normalize('NFD')) + '&gran=line');
  await expect(page.locator('#segmentsTotalInfo')).toContainText(`(${expected} total rows)`);
  // Unaccented input is a different written form, as in gnt-contabulate
  await page.goto('/?q=' + encodeURIComponent('ελεος') + '&gran=line');
  await page.waitForFunction(() => window.__contabulateReady === true);
  await expect(page.locator('#results tbody')).toContainText(/No /i);
  // ...and an accent-insensitive regex finds every accented form
  await ready(page, '/');
  await page.selectOption('#gran', 'word');
  await page.selectOption('#matchMode', 'regex');
  await page.fill('#q', '^[ἔἐ]λ[εέ][οό]');
  await page.click('#addColumnBtn');
  const words = await page.locator('td[data-key="ngram"]').allTextContents();
  expect(words).toEqual(expect.arrayContaining(['ἔλεος', 'ἔλεός', 'ἐλέους']));
});

test('elision, final sigma, and highlight boundaries behave like the Greek NT instance', async ({ page }) => {
  await ready(page, '/');
  const helper = await page.evaluate(() => ({
    elision: tokenizeLineText('ἀφʼ ἧς μετ’ἐμοῦ διʼ αὐτοῦ'),
    sigma: tokenizeLineText('ΛΟΓΟΣ λόγος'),
    highlighted: highlightHTML('τὸ ἔλεος, καὶ ἔλεός μου.', buildHighlightRegexFromNgrams(['ἔλεος'])),
  }));
  expect(helper.elision).toEqual(['ἀφ', 'ἧς', 'μετ', 'ἐμοῦ', 'δι', 'αὐτοῦ']);
  expect(helper.sigma).toEqual(['λογος', 'λόγος']);
  expect(helper.highlighted).toContain('<span class="hit">ἔλεος</span>,');
  expect(helper.highlighted).not.toContain('<span class="hit">ἔλεός</span>');
});

test('LXX-only books are present in Swete order', async ({ page }) => {
  await ready(page, '/?gran=play&sk=location&sd=asc&s_ft_location=' + encodeURIComponent('^5[1-6]\\.'));
  const titles = await page.locator('td[data-key="title"]').allTextContents();
  expect(titles).toEqual([
    'Μακκαβαίων Αʹ (1 Maccabees)', 'Μακκαβαίων Βʹ (2 Maccabees)', 'Μακκαβαίων Γʹ (3 Maccabees)',
    'Μακκαβαίων Δʹ (4 Maccabees)', 'Ψαλμοὶ Σαλωμῶντος (Psalms of Solomon)', 'Ὠδαί (Odes)',
  ]);
});

test('native labels: psalm titles, Ode 4a/4b, and Esther additions', async ({ page }) => {
  await ready(page, '/?gran=line&s_ft_location=' + encodeURIComponent('^17\\.Ps\\.022\\.') + '&sk=location&sd=asc');
  const first = page.locator('#results tbody tr').first();
  await expect(first.locator('td[data-key="scene"]')).toHaveText('title');
  await expect(first).toContainText('Ψαλμὸς τῷ Δαυείδ.');
  await expect(page.locator('#results tbody tr').nth(1)).toContainText('Κύριος ποιμαίνει με');

  await ready(page, '/?gran=line&s_ft_location=' + encodeURIComponent('^56\\.Odes\\.004\\.') + '&sk=location&sd=asc');
  const odeRows = chunks.filter(c => c.location.startsWith('56.Odes.004.')).length;
  await expect(page.locator('#segmentsTotalInfo')).toContainText(`(${odeRows} total rows)`);
  const chapters = await page.locator('td[data-key="act"]').allTextContents();
  expect(chapters[0]).toBe('4a');
  expect(chapters[chapters.length - 1]).toBe('4b');

  await ready(page, '/?gran=line&s_ft_location=' + encodeURIComponent('^24\\.Esth\\.003\\.013') + '&sk=location&sd=asc');
  const verses = await page.locator('td[data-key="scene"]').allTextContents();
  expect(verses).toEqual(['13', '1a', '2a', '3a', '4a', '5a', '6a', '7a']);
});

test('Ecclesiastes and lost verses come from Brenton and are marked as such', async ({ page }) => {
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  const eccl = chunks.filter(c => c.play_abbr === 'Eccl');
  expect(eccl).toHaveLength(222);
  expect(new Set(eccl.map(c => c.act)).size).toBe(12);
  expect(eccl.every(c => c.text_source === 'Brenton 1851')).toBe(true);

  await ready(page, '/?gran=play&sk=location&sd=asc&s_ft_location=' + encodeURIComponent('^1[89]\\.'));
  await expect(page.locator('td[data-key="title"]')).toHaveText(['Παροιμίαι (Proverbs)', 'Ἐκκλησιαστής (Ecclesiastes)Br']);
  await expect(page.locator('#results tbody tr').nth(1).locator('.text-source')).toHaveAttribute('title', /Brenton 1851/);
  await expect(page.locator('#results tbody tr').first().locator('.text-source')).toHaveCount(0);

  await ready(page, '/?gran=line&s_ft_location=' + encodeURIComponent('^19\\.Eccl\\.001\\.') + '&sk=location&sd=asc');
  await expect(page.locator('#segmentsTotalInfo')).toContainText('(18 total rows)');
  const second = page.locator('#results tbody tr').nth(1);
  await expect(second.locator('td[data-key="scene"]')).toHaveText('2');
  await expect(second.locator('td[data-key="line"]')).toContainText('Ματαιότης ματαιοτήτων');
  await expect(page.locator('td[data-key="line"] .text-source')).toHaveCount(18);
  await expect(second.locator('.text-source')).toHaveAttribute('title', /^text: Brenton 1851/);

  // Lost verse-1 texts: only the filled verse is marked, not its Swete neighbours
  await ready(page, '/?gran=line&s_ft_location=' + encodeURIComponent('^02\\.Exod\\.020\\.00[12]') + '&sk=location&sd=asc');
  await expect(page.locator('td[data-key="line"]').first()).toContainText('Καὶ ἐλάλησε Κύριος πάντας τοὺς λόγους');
  await expect(page.locator('td[data-key="line"] .text-source')).toHaveCount(1);
  await expect(page.locator('#results tbody tr').nth(1).locator('.text-source')).toHaveCount(0);

  await page.goto('/sources.html');
  await expect(page.locator('#brenton')).toContainText('Brenton');
  await expect(page.locator('main')).toContainText('public domain');
  expect(errors).toEqual([]);
});

test('desktop and mobile layouts keep the table usable', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 1000 });
  await ready(page);
  await expect(page.locator('h1')).toContainText('📜 Septuagint Tabular Explorer');
  await expect(page.locator('#gran option[value="genre"]')).toHaveText('Section');
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('#addColumnsMobile')).toBeVisible();
  const bounds = await page.evaluate(() => ({ page: document.documentElement.scrollWidth, viewport: innerWidth,
    table: document.querySelector('#results').scrollWidth, tableWidth: document.querySelector('#results').clientWidth }));
  expect(bounds.page).toBeLessThanOrEqual(bounds.viewport + 1);
  expect(bounds.table).toBeGreaterThan(bounds.tableWidth);
  const mobileButton = await page.locator('#addColumnsMobile').boundingBox();
  const input = await page.locator('#q').boundingBox();
  expect(mobileButton.y).toBeGreaterThan(input.y + input.height);
  expect(mobileButton.height).toBeLessThan(75);
  await page.goto('/sources.html');
  await expect(page.locator('h1')).toHaveText('Edition and sources');
});
