"""Generate the simulated shipment history used to train the ETA risk model.

Usage:
    python scripts/generate_eta_training_data.py              # data/eta_training.csv, 5000 rows
    python scripts/generate_eta_training_data.py --rows 20000 --seed 7
"""

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from backend.services.eta.simulation import TARGET, generate  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", default=str(REPO_ROOT / "data" / "eta_training.csv"))
    args = parser.parse_args()

    df = generate(args.rows, args.seed)
    df.to_csv(args.out, index=False)
    delayed = (df[TARGET] > 0).mean()
    print(f"Wrote {len(df)} rows to {args.out}")
    print(f"delayed shipments: {delayed:.1%}, mean delay: {df[TARGET].mean():.2f} days, max: {df[TARGET].max()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
