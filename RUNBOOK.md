# PiWind — local run notes

How OasisLMF and the PiWind demo model were installed and run on this
machine, so the run can be reproduced later. (Kept separate from the
upstream `README.md` so that file's project documentation isn't overwritten.)

## 1. System packages

```
sudo apt-get install -y g++ build-essential libtool zlib1g-dev autoconf \
    automake libspatialindex-dev python3-venv
```

Needed for: compiling ktools (`g++`, `build-essential`, `libtool`,
`autoconf`, `automake`, `zlib1g-dev`), the `rtree`/`geopandas` lookup deps
(`libspatialindex-dev`), and the Python venv.

## 2. Python environment

```
python3.13 -m venv ~/oasis-env
~/oasis-env/bin/pip install -U pip setuptools wheel
~/oasis-env/bin/pip install oasislmf
~/oasis-env/bin/pip install "oasislmf[extra]"   # shapely/geopandas, needed by PiWind's lookup
```

Installed: `oasislmf==2.5.7`.

## 3. ktools (C++ financial engine)

```
git clone https://github.com/OasisLMF/ktools.git ~/projects/ktools
cd ~/projects/ktools
./autogen.sh
./configure --disable-parquet
make -j$(nproc)
sudo make install        # installs to /usr/local/bin
```

**Note:** PiWind's `oasislmf.json` sets `"gulmc": true`, which routes the
whole loss pipeline through the modern all-Python tools bundled with the
`oasislmf` pip package (`evepy`, `gulmc`, `fmpy`, `summarypy`, `aalpy`,
`eltpy`, `lecpy`, `pltpy`, `katpy`, ...) instead of the compiled ktools
binaries. So step 3 (ktools) is **not actually exercised by this model's
config** — it's kept here because it's the standard prerequisite for
Oasis models in general, and other models may need it.

## 4. PATH

The Python tools above live in `~/oasis-env/bin`, which must be on `PATH`
for `oasislmf model run` to find them (it shells out to them by bare name).
Added to `~/.zshrc`:

```
export PATH="$HOME/oasis-env/bin:$PATH"
```

## 5. Clone PiWind

```
git clone https://github.com/OasisLMF/OasisPiWind.git ~/projects/OasisPiWind
```

## 6. Run the model

```
cd ~/projects/OasisPiWind
oasislmf model run -C oasislmf.json
```

Uses the config in `oasislmf.json` (10 sample locations, GUL+IL+RI,
`gulmc: true`, `ktools_alloc_rule_gul: 1`). Exposure summarisation runs by
default (no extra flag needed — there's only a `--disable-summarise-exposure`
opt-out).

## 7. Where the outputs land

Each run creates a new UTC-timestamped directory:

```
runs/losses-<YYYYMMDDHHMMSS>/
├── input/
│   ├── exposure_summary_report.json   # TIV, location/building counts, per-peril match stats
│   └── ...                            # generated Oasis input files (items.bin, keys.parquet, etc.)
├── output/
│   ├── gul_S1_*.csv                   # ground-up loss (ept/melt/mplt/palt/psept/qelt/qplt/selt/splt)
│   ├── il_S1_*.csv                    # insured (net) loss, same file set
│   ├── ri_S1_*.csv                    # net-of-reinsurance loss, same file set
│   └── analysis_settings.json
└── log/
    └── resource_report/resource_report.md   # run resource usage
```

`_ept.csv` files hold both OEP and AEP curves combined, distinguished by
the `EPType` column (1 = OEP, 2 = OEP TVaR, 3 = AEP, 4 = AEP TVaR) and by
`EPCalc` (1 = mean damage ratio, 2 = full uncertainty, 3 = per-sample mean,
4 = mean sample).

Last verified run: `runs/losses-20260913082716/`.
