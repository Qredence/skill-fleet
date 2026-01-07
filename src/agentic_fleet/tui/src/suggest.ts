export interface FuzzyItem {
  key: string;
  description?: string;
  keywords?: string[];
  requiresValue?: boolean;
}

export interface FuzzyResult extends FuzzyItem {
  score: number; // higher is better
}

// Simple fuzzy match: favor prefix, then in-order subsequence; include keywords in scoring.
export function fuzzyMatch(query: string, items: FuzzyItem[], limit = 8): FuzzyResult[] {
  const q = query.trim().toLowerCase();
  if (!q) {
    return items.slice(0, limit).map((i) => ({ ...i, score: 0 }));
  }

  const results: FuzzyResult[] = [];
  for (const item of items) {
    const hay = item.key.toLowerCase();
    let score = 0;

    if (hay.startsWith(q)) score += 100; // strong prefix boost

    // in-order subsequence scoring
    let i = 0;
    let matched = 0;
    for (const ch of q) {
      const pos = hay.indexOf(ch, i);
      if (pos === -1) {
        matched = 0;
        break;
      }
      matched++;
      // closeness bonus (characters closer together rank higher)
      score += 5 - Math.min(4, pos - i);
      i = pos + 1;
    }
    if (matched === q.length) score += matched * 2;

    // keyword boosts
    if (item.keywords) {
      for (const kw of item.keywords) {
        const k = kw.toLowerCase();
        if (k === q) score += 30;
        else if (k.startsWith(q)) score += 15;
        else if (k.includes(q)) score += 5;
      }
    }

    if (score > 0 || hay.includes(q)) {
      results.push({ ...item, score });
    }
  }

  results.sort((a, b) => b.score - a.score || a.key.localeCompare(b.key));
  return results.slice(0, limit);
}
