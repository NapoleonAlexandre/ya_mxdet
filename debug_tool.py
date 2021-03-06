#!/usr/bin/python3 
# Copyright 2017, Mengxiao Lin <linmx0130@gmail.com>
import mxnet as mx 
import numpy as np
import cv2

def show_anchors(data, label, anchors, anchors_chosen, count=None):
    """
    show image, ground truth and anchors in the same window
    """
    data = data[0].as_in_context(mx.cpu(0))
    data[0] = data[0] * 0.229 + 0.485
    data[1] = data[1] * 0.224 + 0.456
    data[2] = data[2] * 0.225 + 0.406
    label = label[0].asnumpy()
    img = data.asnumpy()
    img = np.array(np.round(img * 255), dtype=np.uint8)
    img = np.transpose(img, (1, 2, 0))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    for item in label:
        cv2.rectangle(img, (int(item[0]), int(item[1])), (int(item[2]), int(item[3])), color=(255, 0, 0), thickness=2)
        #cv2.putText(img, ds.voc_class_name[int(item[4])], (int(item[0]), int(item[3])),0, 0.5,(0, 255, 0))
    anchors = anchors[0].asnumpy()
    anchors_chosen = anchors_chosen[0].asnumpy()
    anchors = anchors.reshape((-1, 4))
    anchors_chosen = anchors_chosen.reshape((-1,))
    for anchor_id, c in enumerate(anchors_chosen):
        if c==1:
            anc = anchors[anchor_id]
            cv2.rectangle(img, (int(anc[0]), int(anc[1])), (int(anc[2]), int(anc[3])), color=(0,0, 255), thickness=1)
            print((int(anc[0]), int(anc[1])), (int(anc[2]), int(anc[3])))
        if count is not None:
            count = count - 1
            if count == 0:
                break
    cv2.imshow("Img", img)
    cv2.waitKey(0)
