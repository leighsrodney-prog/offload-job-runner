"""Synthetic memory load: allocates ~N GB in chunks, hashes it, writes out/summary.json. No real data."""
import argparse, hashlib, json, os, resource, time


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--gb", type=float, default=3.0)
    p.add_argument("--chunk-mb", type=int, default=100)
    p.add_argument("--out", default="out")
    a = p.parse_args(argv)
    t0 = time.time(); chunks = []; h = hashlib.sha256()
    n = max(1, int(a.gb * 1024 / a.chunk_mb))
    for _ in range(n):
        b = bytearray(os.urandom(1024)) * (a.chunk_mb * 1024)
        h.update(b[::4096]); chunks.append(b)
    total = sum(len(c) for c in chunks)
    s = {"allocated_bytes": total, "allocated_gb": round(total / 2**30, 2), "chunks": n,
         "digest": h.hexdigest(),
         "max_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
         "seconds": round(time.time() - t0, 2)}
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "summary.json"), "w") as f:
        json.dump(s, f, indent=2)
    print(json.dumps(s))
    return s


if __name__ == "__main__":
    main()
