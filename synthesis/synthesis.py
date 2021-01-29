import os
import os.path
import sys
import torch
import torch.utils.data as data
import cv2
import numpy as np

class RetinaTrainDataset(data.Dataset):
    def __init__(self, deepvac_config, augument=None):
        self.conf = deepvac_config
        self.augument = augument
        
        with open(self.conf.fileline_path, 'r') as f:
            lines = f.readlines()
       
        self.imgs_path = []
        self.words = []
        
        lines = list(map(lambda x: x.rstrip('\r\n'), lines))
        flag = np.char.count(np.array(lines), '#')!=0
        gaps = list(np.where(flag==True)[0])
        gaps.append(len(lines))
        
        for i in range(len(gaps)-1):
            path = lines[gaps[i]][2:]
            path = os.path.join(self.conf.fileline_data_path_prefix, path)
            self.imgs_path.append(path)
            self.words.append(lines[gaps[i]+1:gaps[i+1]])

        for i in range(len(self.words)):
            self.words[i] = [list(map(float, word.split(' '))) for word in self.words[i]]

    def __len__(self):
        return len(self.imgs_path)

    def __getitem__(self, index):
        img = cv2.imread(self.imgs_path[index])
        height, width, _ = img.shape

        labels = self.words[index]
        annotations = np.zeros((0, 15))
        if len(labels) == 0:
            return annotations
        for idx, label in enumerate(labels):
            annotation = np.zeros((1, 15))
            # bbox
            annotation[0, 0] = label[0]  # x1
            annotation[0, 1] = label[1]  # y1
            annotation[0, 2] = label[0] + label[2]  # x2
            annotation[0, 3] = label[1] + label[3]  # y2

            # landmarks
            annotation[0, 4] = label[4]    # l0_x
            annotation[0, 5] = label[5]    # l0_y
            annotation[0, 6] = label[7]    # l1_x
            annotation[0, 7] = label[8]    # l1_y
            annotation[0, 8] = label[10]   # l2_x
            annotation[0, 9] = label[11]   # l2_y
            annotation[0, 10] = label[13]  # l3_x
            annotation[0, 11] = label[14]  # l3_y
            annotation[0, 12] = label[16]  # l4_x
            annotation[0, 13] = label[17]  # l4_y
            if (annotation[0, 4]<0):
                annotation[0, 14] = -1
            else:
                annotation[0, 14] = 1

            annotations = np.append(annotations, annotation, axis=0)
        target = np.array(annotations)
        if self.augument is not None:
            img, target = self.augument(img, target)
       
        return torch.from_numpy(img), target

def detection_collate(batch):
    """Custom collate fn for dealing with batches of images that have a different
    number of associated object annotations (bounding boxes).

    Arguments:
        batch: (tuple) A tuple of tensor images and lists of annotations

    Return:
        A tuple containing:
            1) (tensor) batch of images stacked on their 0 dim
            2) (list of tensors) annotations for a given image are stacked on 0 dim
    """
    targets = []
    imgs = []
    for _, sample in enumerate(batch):
        for _, tup in enumerate(sample):
            if torch.is_tensor(tup):
                imgs.append(tup)
            elif isinstance(tup, type(np.empty(0))):
                annos = torch.from_numpy(tup).float()
                targets.append(annos)
    return (torch.stack(imgs, 0), targets)
