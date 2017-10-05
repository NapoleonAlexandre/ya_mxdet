#!/usr/bin/python3
# Copyright 2017, Mengxiao Lin <linmx0130@gmail.com>

from config import cfg
from VOCDataset import VOCDataset
from ssd import SSDFeatures, DetectorHead
import mxnet as mx
from utils import random_flip, imagenetNormalize, img_resize, random_square_crop, bbox_overlaps
from anchor_generator import ssd_generate_anchors, map_anchors

def train_transformation(data, label):
    data, label = random_flip(data, label)
    data, label = random_square_crop(data, label)
    data = imagenetNormalize(data)
    return data, label

train_dataset = VOCDataset(annotation_dir=cfg.annotation_dir,
                           img_dir=cfg.img_dir,
                           dataset_index=cfg.dataset_index,
                           transform=train_transformation,
                           resize_func=img_resize)
train_datait = mx.gluon.data.DataLoader(train_dataset, batch_size=1, shuffle=True)
ctx = mx.gpu(0)
ssd_features = SSDFeatures()
ssd_features.init_by_vgg(ctx)
ssd_heads = [DetectorHead(21, 5), DetectorHead(21, 5), DetectorHead(21, 5), DetectorHead(21, 5)]

for h in ssd_heads:
    h.init_params(ctx)

for it, (data, label) in enumerate(train_datait):
    data = data.as_in_context(ctx)
    _n, _c, h, w = data.shape
    label = label.as_in_context(ctx).reshape((-1, 5))
    background_bndbox = mx.nd.array([[-h*10,-h*10, h*10, w*10, 0]], ctx=ctx)
    label = mx.nd.concatenate([background_bndbox, label], axis=0).reshape((1, -1, 5))
    label_count = label.shape[1]
    with mx.autograd.record():
        features = ssd_features(data)
        for fi, (f, dh) in enumerate(zip(features, ssd_heads)):
            cls_head, reg_head = dh(f)
            _fn, _fc, feature_height, feature_width = reg_head.shape
            anchor_counts = _fc // 4
            # only batch size=1 is supported
            ref_anchors = ssd_generate_anchors(cfg.anchor_scales[fi] * h, ratios=cfg.anchor_ratios)
            anchors = map_anchors(ref_anchors, reg_head.shape, h, ctx)
            anchors = anchors.reshape((1, -1, 4, feature_height, feature_width))
            anchors = mx.nd.transpose(anchors, (0, 3, 4, 1, 2))
            anchors = anchors.reshape((-1, 4))
            # So until now, anchors are N * 4, the order is [(H, W, A), 4]
            overlaps = bbox_overlaps(anchors, label.reshape((-1, 4)))
            overlaps = overlaps.reshape((1, feature_height, feature_width, anchor_counts, -1))
            # Reshape the overlaps to [1, H, W, A, #{label}]
            overlaps = mx.nd.transpose(overlaps, (0, 3, 1, 2, 4))
            # Transpose overlaps to [1, A, H, W, #{label}]
            bbox_assignment = mx.nd.argmax(overlaps, axis=4)
            # Get bbox_assignment to [1, A, H, W]
            label_extend = label[:,:,4].reshape(
                    (1, 1, 1, 1, label_count)).broadcast_to(
                    (1, anchor_counts, feature_height, feature_width, label_count))
            bbox_cls_gt = mx.nd.pick(label_extend, bbox_assignment)
            from IPython import embed; embed()
            break
    #TODO
    if it >= 5:
        break
