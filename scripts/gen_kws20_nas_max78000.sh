#!/bin/sh
DEVICE="MAX78000"
TARGET="sdk/Examples/$DEVICE/CNN"
COMMON_ARGS="--device $DEVICE --timer 0 --display-checkpoint --verbose"

python ai8xize.py --test-dir $TARGET --prefix kws20_nas --checkpoint-file trained/ai85-kws20_nas-qat8-q.pth.tar --config-file networks/kws20-nas-hwc.yaml --softmax $COMMON_ARGS "$@"
