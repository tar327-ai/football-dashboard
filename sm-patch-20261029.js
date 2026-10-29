const fs = require('fs');
const path = 'index.js';
if (!fs.existsSync(path)) throw new Error('index.js not found. Run this from ~/sellermate-api');
let s = fs.readFileSync(path, 'utf8');
const stamp = new Date().toISOString().replace(/[-:TZ.]/g, '').slice(0,14);
fs.copyFileSync(path, `index.pre-autoskip-next60-${stamp}.js`);

function mustFind(text, label) {
  const i = s.indexOf(text);
  if (i < 0) throw new Error(`${label}_NOT_FOUND`);
  return i;
}

// ------------------------------------------------------------
// 1) AUTO_SKIP helper: only structured Domeggook source evidence.
// ------------------------------------------------------------
const autoSkipMarker = 'SELLERMATE_LISTING_AUTO_SKIP_V1';
if (!s.includes(autoSkipMarker)) {
  const productsApiMarker = '// ==============================\n\n// Products API';
  const insertAt = mustFind(productsApiMarker, 'PRODUCTS_API_MARKER');
  const helper = `// ${autoSkipMarker}\nfunction sellerMateNormalizeSourceText(value) {\n  return String(value ?? '').replace(/\\s+/g, ' ').trim();\n}\n\nfunction sellerMateIsSourcePlaceholder(value) {\n  const text = sellerMateNormalizeSourceText(value);\n  if (!text) return true;\n  return /(상세\\s*(정보|설명)?\\s*(별도)?\\s*(표기|참조)|별도\\s*표기|자사\\s*협력|협력\\s*업체|관계사|판매자\\s*(정보|연락처)\\s*참고|미정|해당\\s*없음|^없음$|^수입산[_\\s-]*$)/i.test(text);\n}\n\nfunction sellerMateParseSourceSelectOpt(item) {\n  const raw = item?.selectOpt;\n  if (!raw) return null;\n  if (typeof raw === 'object') return raw;\n  try { return JSON.parse(String(raw)); } catch { return null; }\n}\n\nfunction sellerMateSourceInfoItems(item) {\n  const rows = Array.isArray(item?.detail?.infoDuty?.item) ? item.detail.infoDuty.item : [];\n  return rows.filter(row => row?.type === 'item');\n}\n\nfunction sellerMateSourceOptionAxes(item) {\n  const opt = sellerMateParseSourceSelectOpt(item);\n  const sets = Array.isArray(opt?.set) && opt.set.length ? opt.set : (Array.isArray(opt?.orgSet) ? opt.orgSet : []);\n  return sets.map(set => ({\n    name: sellerMateNormalizeSourceText(set?.name),\n    values: Array.isArray(set?.opts) ? set.opts.map(sellerMateNormalizeSourceText).filter(Boolean) : []\n  }));\n}\n\nfunction sellerMateHasSourceEvidence(item, field) {\n  const infoItems = sellerMateSourceInfoItems(item);\n  const axes = sellerMateSourceOptionAxes(item);\n  const normalizedField = sellerMateNormalizeSourceText(field);\n\n  if (normalizedField === 'productIdentifier') {\n    return !sellerMateIsSourcePlaceholder(item?.detail?.model);\n  }\n\n  if (normalizedField === 'noticeCategory') {\n    // Notice category can be mapped from source infoDuty/category later; do not AUTO_SKIP solely for this.\n    return true;\n  }\n\n  if (normalizedField.startsWith('attribute:')) {\n    const attr = normalizedField.slice('attribute:'.length).trim();\n    const aliases = attr === '사이즈'\n      ? ['사이즈', 'size', '크기', '치수', '규격']\n      : attr === '색상'\n        ? ['색상', 'color', '컬러']\n        : attr === '수량'\n          ? ['수량', '구성', '개수', 'quantity']\n          : [attr];\n\n    const axisEvidence = axes.some(axis => {\n      const axisName = axis.name.toLowerCase();\n      return aliases.some(alias => axisName.includes(alias.toLowerCase())) &&\n        axis.values.some(value => !sellerMateIsSourcePlaceholder(value));\n    });\n    if (axisEvidence) return true;\n\n    if (attr === '수량') {\n      const quantityInOption = axes.some(axis => axis.values.some(value => /(?:^|\\s)\\d+\\s*(?:개|매|입|p|pcs|set|세트)(?:\\s|$)/i.test(value)));\n      if (quantityInOption) return true;\n    }\n\n    return infoItems.some(row => {\n      const name = sellerMateNormalizeSourceText(row?.name).toLowerCase();\n      const desc = sellerMateNormalizeSourceText(row?.desc);\n      return aliases.some(alias => name.includes(alias.toLowerCase())) && !sellerMateIsSourcePlaceholder(desc);\n    });\n  }\n\n  if (normalizedField.startsWith('notice:')) {\n    const notice = normalizedField.slice('notice:'.length).trim();\n    if (/제조자|제조사|수입자/.test(notice) && !sellerMateIsSourcePlaceholder(item?.detail?.manufacturer)) return true;\n    if (/제조국|원산지/.test(notice) && !sellerMateIsSourcePlaceholder(item?.detail?.country)) return true;\n\n    const aliases = /제조자|제조사|수입자/.test(notice)\n      ? ['제조자', '제조사', '수입자']\n      : /취급.*주의|주의사항/.test(notice)\n        ? ['취급시 주의사항', '주의사항']\n        : [notice.replace(/\\([^)]*\\)/g, '').trim()];\n\n    return infoItems.some(row => {\n      const name = sellerMateNormalizeSourceText(row?.name);\n      const desc = sellerMateNormalizeSourceText(row?.desc);\n      return aliases.some(alias => name.includes(alias)) && !sellerMateIsSourcePlaceholder(desc);\n    });\n  }\n\n  // Unknown field: fail open to HOLD, never AUTO_SKIP from an unsupported guess.\n  return true;\n}\n\nasync function sellerMateClassifyAutoSkip(productNo, missing) {\n  const fields = (Array.isArray(missing) ? missing : [])\n    .map(entry => sellerMateNormalizeSourceText(entry?.field || entry))\n    .filter(Boolean);\n  if (!fields.length) return { autoSkip: false, impossibleFields: [] };\n\n  let item = null;\n  try { item = await getDomeggookProductByNo(String(productNo)); } catch { item = null; }\n  if (!item) return { autoSkip: false, impossibleFields: [] };\n\n  const impossibleFields = fields.filter(field => !sellerMateHasSourceEvidence(item, field));\n  return { autoSkip: impossibleFields.length > 0, impossibleFields };\n}\n\n`;
  s = s.slice(0, insertAt) + helper + s.slice(insertAt);
}

// Patch the products readiness gate.
if (!s.includes('SELLERMATE_LISTING_AUTO_SKIP_GATE_V1')) {
  const varsOld = '        const readyProducts = [];\n        const holdProducts = [];';
  const varsNew = '        const readyProducts = [];\n        const holdProducts = [];\n        const autoSkipProducts = [];\n\n        // SELLERMATE_LISTING_AUTO_SKIP_GATE_V1';
  if (!s.includes(varsOld)) throw new Error('READINESS_GATE_VARS_NOT_FOUND');
  s = s.replace(varsOld, varsNew);

  const elseOld = `            if (isReady) {\n              readyProducts.push({ ...product, listingReadiness: "READY" });\n            } else {\n              holdProducts.push({\n                productNo,\n                title: productName,\n                status: readiness?.status || ("HTTP_" + rr.status),\n                missing: missing.map(x => x?.field || x),\n                review: review.map(x => x?.field || x)\n              });\n            }`;
  const elseNew = `            if (isReady) {\n              readyProducts.push({ ...product, listingReadiness: "READY" });\n            } else {\n              const autoSkip = await sellerMateClassifyAutoSkip(productNo, missing);\n              const nonReady = {\n                productNo,\n                title: productName,\n                status: readiness?.status || ("HTTP_" + rr.status),\n                missing: missing.map(x => x?.field || x),\n                review: review.map(x => x?.field || x)\n              };\n\n              if (autoSkip.autoSkip) {\n                autoSkipProducts.push({\n                  ...nonReady,\n                  status: "AUTO_SKIP",\n                  impossibleFields: autoSkip.impossibleFields\n                });\n              } else {\n                holdProducts.push(nonReady);\n              }\n            }`;
  if (!s.includes(elseOld)) throw new Error('READINESS_GATE_BRANCH_NOT_FOUND');
  s = s.replace(elseOld, elseNew);

  const countOld = '          marketCandidateCount: products.length,\n          listingHoldCount: holdProducts.length,';
  const countNew = '          marketCandidateCount: products.length,\n          listingAutoSkipCount: autoSkipProducts.length,\n          listingHoldCount: holdProducts.length,';
  if (!s.includes(countOld)) throw new Error('READINESS_GATE_COUNT_RETURN_NOT_FOUND');
  s = s.replace(countOld, countNew);

  const listOld = '          products: readyProducts,\n          listingHolds: holdProducts';
  const listNew = '          products: readyProducts,\n          listingAutoSkips: autoSkipProducts,\n          listingHolds: holdProducts';
  if (!s.includes(listOld)) throw new Error('READINESS_GATE_LIST_RETURN_NOT_FOUND');
  s = s.replace(listOld, listNew);
}

// ------------------------------------------------------------
// 2) NEXT 60: exclude all products already batched today (KST)
//    and use Domeggook search_after pagination.
// ------------------------------------------------------------
const nextMarker = 'SELLERMATE_COLLECTOR_NEXT60_V1';
if (!s.includes(nextMarker)) {
  const todaySnapshotPos = s.indexOf('      const todaySnapshot =', mustFind("'/api/products'", 'PRODUCTS_ROUTE'));
  if (todaySnapshotPos < 0) throw new Error('TODAY_SNAPSHOT_NOT_FOUND');
  const nextSetup = `      // ${nextMarker}\n      const collectorNextMode =\n        collectorMode &&\n        String(req.query?.next || '') === '1';\n\n      let collectorSeenToday = new Set();\n      if (collectorNextMode) {\n        try {\n          const seenRows = db.prepare(\`\n            SELECT DISTINCT mbi.product_no\n            FROM market_collector_batch_items mbi\n            JOIN market_collector_batches mb\n              ON mb.id = mbi.batch_id\n            WHERE date(mb.created_at, '+9 hours') = date('now', '+9 hours')\n          \`).all();\n          collectorSeenToday = new Set(seenRows.map(row => String(row.product_no)));\n        } catch {\n          collectorSeenToday = new Set();\n        }\n      }\n\n`;
  s = s.slice(0, todaySnapshotPos) + nextSetup + s.slice(todaySnapshotPos);

  const routePos = mustFind("'/api/products'", 'PRODUCTS_ROUTE_2');
  const fetchStart = s.indexOf('      const response = await fetch(', routePos);
  const sourceDecl = s.indexOf('      const sourceProducts =', fetchStart);
  if (fetchStart < 0 || sourceDecl < 0) throw new Error('DOMEGGOOK_FETCH_BLOCK_NOT_FOUND');
  const sourceEnd = s.indexOf(';', sourceDecl);
  if (sourceEnd < 0) throw new Error('SOURCE_PRODUCTS_END_NOT_FOUND');

  const fetchBlock = `      let data = null;\n      const sourceProducts = [];\n      const sourceSeen = new Set();\n      let searchAfter = null;\n      const maxSourcePages = collectorNextMode ? 8 : 1;\n\n      for (let sourcePage = 0; sourcePage < maxSourcePages; sourcePage += 1) {\n        const searchBody = {\n          size: 100,\n          track_total_hits: true,\n          query: {\n            term: {\n              'channel.supply': true\n            }\n          },\n          sort: [\n            { no: { order: 'desc' } }\n          ]\n        };\n\n        if (collectorNextMode && Array.isArray(searchAfter) && searchAfter.length) {\n          searchBody.search_after = searchAfter;\n        }\n\n        const response = await fetch(\n          'https://product.domeggook.com/api/v1/product/_search',\n          {\n            method: 'POST',\n            headers: {\n              Authorization: \`Bearer \${apiKey}\`,\n              'Content-Type': 'application/json'\n            },\n            body: JSON.stringify(searchBody)\n          }\n        );\n\n        const pageData = await response.json();\n        if (!response.ok || pageData.result !== true) {\n          return res.status(502).json({\n            success: false,\n            message: 'Domeggook API error'\n          });\n        }\n\n        if (!data) data = pageData;\n        const pageList = Array.isArray(pageData.data?.list) ? pageData.data.list : [];\n\n        for (const item of pageList) {\n          const productNo = String(item?.no || '').trim();\n          if (!productNo || sourceSeen.has(productNo)) continue;\n          sourceSeen.add(productNo);\n          if (collectorNextMode && collectorSeenToday.has(productNo)) continue;\n          sourceProducts.push(item);\n        }\n\n        if (!collectorNextMode) break;\n        if (sourceProducts.length >= 400) break;\n\n        const nextAfter = pageData.data?.searchAfter;\n        if (!Array.isArray(nextAfter) || !nextAfter.length || !pageList.length) break;\n        searchAfter = nextAfter;\n      }`;
  s = s.slice(0, fetchStart) + fetchBlock + s.slice(sourceEnd + 1);
}

fs.writeFileSync(path, s);
console.log(JSON.stringify({
  patched: true,
  autoSkip: s.includes(autoSkipMarker) && s.includes('SELLERMATE_LISTING_AUTO_SKIP_GATE_V1'),
  next60: s.includes(nextMarker),
  backup: `index.pre-autoskip-next60-${stamp}.js`
}, null, 2));
