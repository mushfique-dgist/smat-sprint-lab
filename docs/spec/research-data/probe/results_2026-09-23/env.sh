# Source this in every remote command. Keeps every cache/temp inside $PROBE.
export PROBE=/home/aurnab/.cache/smatsprint-probe-2026-09-23
export UV=/home/aurnab/.local/bin/uv
export UV_CACHE_DIR=$PROBE/uv-cache
export UV_PYTHON_INSTALL_DIR=$PROBE/uv-python
export UV_PYTHON_DOWNLOADS=never
export UV_NO_CONFIG=1
export TMPDIR=$PROBE/tmp
export XDG_CACHE_HOME=$PROBE/xdg
export XDG_CONFIG_HOME=$PROBE/xdg-config
export WARP_CACHE_PATH=$PROBE/warp-cache
export CUDA_CACHE_PATH=$PROBE/nv-cache
export PYTHONPYCACHEPREFIX=$PROBE/pycache
export PYTHONDONTWRITEBYTECODE=1
export MPLCONFIGDIR=$PROBE/xdg/mpl
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 MKL_NUM_THREADS=8 NUMEXPR_NUM_THREADS=8 VECLIB_MAXIMUM_THREADS=8
export OLDVENV=/home/aurnab/projects/sail-sprint-20260905/.venv
export NEWVENV=$PROBE/venv
mkdir -p $PROBE/tmp $PROBE/xdg $PROBE/xdg-config $PROBE/warp-cache $PROBE/nv-cache $PROBE/pycache $PROBE/uv-cache $PROBE/model $PROBE/work $PROBE/results
