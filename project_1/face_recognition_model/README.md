# Face Recognition Model

Wraps a FaceNet-style pipeline (MTCNN for face detection + InceptionResnetV1
for embeddings) and matches a detected face against a precomputed database of
known-person embeddings.

## Files

- **`face_recognition.py`** — `face_match(img, data_path, mtcnn, resnet)`
  detects/crops the face, computes its embedding, and returns the closest
  match (by Euclidean distance) from `data.pt`.
- **`data.pt`** — a `torch.save`d tuple of `(embedding_list, name_list)`: the
  known face embeddings and their corresponding names. Required for matching
  to work; this is a model asset, not test data.
- **`resnetV1/resnetV1.pt`, `resnetV1/resnetV1_video_weights.pt`** — these are
  **Git LFS pointer files**, not the actual weights (the originals are
  ~100+ MB and were tracked with LFS). They are not required at runtime:
  `backend.py` loads `InceptionResnetV1(pretrained='vggface2')`, which
  downloads pretrained weights automatically the first time it runs.

## Dependency note

`backend.py` imports `MTCNN`/`InceptionResnetV1` from
`face_recognition_model.facenet_pytorch`. That submodule isn't vendored in
this repo — install the `facenet-pytorch` package instead:

```bash
pip install facenet-pytorch
```

and adjust the import in `app-tier/backend.py` to `from facenet_pytorch import
MTCNN, InceptionResnetV1` if you don't vendor the package under this
directory.
