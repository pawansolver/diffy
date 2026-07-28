// Minimal promise pool: run `worker` over `items` with at most `concurrency`
// in flight. Results are returned in input order.

export async function runPool<T, R>(
  items: T[],
  concurrency: number,
  worker: (item: T, index: number) => Promise<R>,
): Promise<R[]> {
  const results: R[] = new Array(items.length);
  const n = Math.max(1, Math.min(concurrency, items.length || 1));
  let next = 0;

  async function loop(): Promise<void> {
    while (true) {
      const i = next++;
      if (i >= items.length) return;
      results[i] = await worker(items[i], i);
    }
  }

  await Promise.all(Array.from({ length: n }, () => loop()));
  return results;
}
